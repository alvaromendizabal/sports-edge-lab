import json
from pathlib import Path
import tempfile
import unittest
from dataclasses import replace
from examples.review_lab.recoverable_stages import Stage, create, run, fixture, walkthrough


class RecoverableStagesTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.context = {"decision_time": "2030-01-01T12:00:00Z", "fixture": "invented-v1"}

    def execute(self, stages=None, context=None):
        return run(self.root, fixture() if stages is None else stages, self.context if context is None else context)

    def test_failure_resume_and_zero_work_reentry(self):
        x = walkthrough()
        self.assertEqual([x[k]["new_attempts"] for k in ("first", "resume", "reentry")], [7, 2, 0])
        self.assertEqual([x[k]["reused_stages"] for k in ("first", "resume", "reentry")], [0, 6, 8])
        self.assertTrue(x["forecast_identity_preserved"] and x["finance_identity_preserved"])
        self.assertFalse(x["resume"]["outputs"]["qualification"]["qualified"])

    def test_prior_bytes_unchanged_by_recovery(self):
        self.execute(fixture(True))
        prior = {p.name: p.read_bytes() for p in self.root.glob('*.json')}
        self.execute()
        for name, content in prior.items(): self.assertEqual((self.root / name).read_bytes(), content)
        self.assertEqual(json.loads((self.root/'research.result-1.json').read_text())["status"], "FAILED")

    def test_changed_context_rejected(self):
        self.execute()
        with self.assertRaises(ValueError): self.execute(context={**self.context, "fixture": "changed"})

    def test_changed_recipe_rejected(self):
        self.execute()
        stages=fixture();stages[0]=replace(stages[0],recipe="changed")
        with self.assertRaises(ValueError): self.execute(stages)

    def test_accepted_corruption_rejected(self):
        self.execute();path=self.root/'forecast.accepted.json'
        data=json.loads(path.read_text());data['output']['fixture_probability']=0.99;path.write_text(json.dumps(data))
        with self.assertRaises(ValueError): self.execute()

    def test_missing_success_event_rejected(self):
        self.execute();(self.root/'forecast.result-1.json').unlink()
        with self.assertRaises(ValueError): self.execute()

    def test_success_before_acceptance_can_be_recovered_without_work(self):
        original=self.execute();(self.root/'forecast.accepted.json').unlink()
        result=self.execute()
        self.assertEqual(result['new_attempts'],0)
        self.assertEqual(result['outputs']['forecast'],original['outputs']['forecast'])
        self.assertTrue((self.root/'forecast.accepted.json').exists())

    def test_attempt_limit_exhausts_failed_research_only(self):
        self.execute(fixture(True));self.execute(fixture(True));r=self.execute(fixture(True))
        self.assertEqual(r['new_attempts'],0)
        self.assertEqual(next(x['status'] for x in r['stages'] if x['stage']=='research'),'EXHAUSTED')
        self.assertIn('finance',r['outputs'])

    def test_stale_writer_lock_requires_inspection(self):
        (self.root/'.writer-lock').mkdir()
        with self.assertRaises(RuntimeError): self.execute()
        self.assertTrue((self.root/'.writer-lock').exists())

    def test_duplicate_stage_rejected(self):
        s=fixture()
        with self.assertRaises(ValueError): self.execute(s+[s[0]])

    def test_future_dependency_rejected(self):
        s=fixture();s[0]=replace(s[0],dependencies=('research',))
        with self.assertRaises(ValueError): self.execute(s)

    def test_system_exit_consumes_reservation_without_fake_completion(self):
        s=fixture()
        def stop(d,c):raise SystemExit(1)
        s[6]=replace(s[6],work=stop)
        with self.assertRaises(SystemExit): self.execute(s)
        self.assertTrue((self.root/'research.attempt-1.json').exists())
        self.assertFalse((self.root/'research.accepted.json').exists())
        r=self.execute();self.assertEqual(r['new_attempts'],2)
        self.assertEqual(json.loads((self.root/'research.accepted.json').read_text())['attempt'],2)

    def test_nonfinite_output_rejected_as_failure(self):
        s=fixture();s[6]=replace(s[6],work=lambda d,c: {'value':float('nan')})
        r=self.execute(s)
        self.assertEqual(next(x['status'] for x in r['stages'] if x['stage']=='research'),'FAILED')
        self.assertNotIn('research',r['outputs'])

    def test_dependency_mutation_cannot_modify_upstream_artifact(self):
        s=fixture()
        def mutate(d,c):d['integrity']['validated']=False;return {'candidate':'invented'}
        s[6]=replace(s[6],work=mutate)
        self.assertTrue(self.execute(s)['outputs']['integrity']['validated'])

    def test_atomic_creation_does_not_replace(self):
        p=self.root/'same.json';create(p,{'value':1})
        with self.assertRaises(FileExistsError):create(p,{'value':2})
        self.assertEqual(json.loads(p.read_text()),{'value':1})
        self.assertEqual(list(self.root.glob('.pending-*')),[])

    def test_attempt_after_completion_rejected(self):
        self.execute();old=json.loads((self.root/'research.attempt-1.json').read_text());old['attempt']=2;create(self.root/'research.attempt-2.json',old)
        with self.assertRaises(ValueError):self.execute()

    def test_unreserved_terminal_event_rejected(self):
        self.execute();(self.root/'research.attempt-1.json').unlink()
        with self.assertRaises(ValueError):self.execute()

    def test_later_callback_cannot_mutate_retained_output_by_alias(self):
        shared={"value":1}
        def later(d,c):shared["value"]=2;return {"done":True}
        stages=[Stage("first",(),"v1",lambda d,c:shared),Stage("later",("first",),"v1",later)]
        result=self.execute(stages)
        self.assertEqual(result["outputs"]["first"],{"value":1})
        saved=json.loads((self.root/"first.accepted.json").read_text())
        self.assertEqual(result["outputs"]["first"],saved["output"])

    def test_generator_plan_executes_all_stages(self):
        result=self.execute(iter(fixture()))
        self.assertEqual(result["new_attempts"],8)
        self.assertEqual(len(result["outputs"]),8)
