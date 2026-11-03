import copy
import json
from pathlib import Path
import tempfile
import unittest
from examples.fbs_contracts import certified_resume as recovery
from examples.review_lab import numerical_recovery as numerical

class CertifiedResumeTests(unittest.TestCase):
    def test_partial_work_survives_and_complete_reentry_does_no_solves(self):
        r=recovery.walkthrough();a,b,c=[r[n] for n in ('first_attempt','recovery','completed_reentry')]
        self.assertEqual((a['fresh_synthetic_solves'],a['failed_attempts']),(2,1))
        self.assertEqual((b['fresh_synthetic_solves'],b['reused_committed_states']),(1,2))
        self.assertEqual((c['fresh_synthetic_solves'],c['reused_committed_states']),(0,3))
        self.assertEqual(a['status'],'PARTIAL');self.assertFalse(r['private_owner_recovery_success_claimed'])
    def test_solver_status_cannot_be_string_coerced(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValueError,'solver status'):
                recovery.commit_candidate(directory,recovery.jobs()[0],[.55,.45,0.],solver_success='false')
            self.assertEqual(list(Path(directory).rglob('*.json')),[])
    def test_bad_success_flag_produces_no_accepted_files(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaisesRegex(ValueError,'certificate rejected'):
                recovery.commit_candidate(d,recovery.jobs()[0],[0.,0.,0.],solver_success=True)
            self.assertEqual(list(Path(d).rglob('*.json')),[])
    def test_original_solver_stop_retained_for_certified_point(self):
        j=recovery.jobs()[0];fit=numerical.recover(j['target'],j['curvature'])
        with tempfile.TemporaryDirectory() as d:
            recovery.commit_candidate(d,j,fit['point'],solver_success=False)
            state=recovery.restore(d,j)['state']
        self.assertFalse(state['solver_reported_success'])
        self.assertEqual(state['certificate']['status'],'CERTIFIED_WITH_SOLVER_STOP_RETAINED')
    def test_corrupted_state_not_reused_or_overwritten(self):
        with tempfile.TemporaryDirectory() as d:
            recovery.run(d);p=sorted((Path(d)/'states').glob('*.json'))[0]
            state=json.loads(p.read_bytes());state['point']=[0.,0.,0.];bad=recovery.encode(state);p.write_bytes(bad)
            r=recovery.run(d)
            self.assertEqual((r['fresh_synthetic_solves'],r['reused_committed_states'],r['failed_attempts']),(0,2,1))
            self.assertEqual(p.read_bytes(),bad)
    def test_rehashed_bad_numerical_state_still_rejected(self):
        j=recovery.jobs()[0]
        with tempfile.TemporaryDirectory() as d:
            recovery.run(d);p,q=recovery._paths(d,recovery.identity(j));_,state=recovery._read(p)
            state['point']=[0.,0.,0.];state['certificate']=numerical.certificate(j['target'],j['curvature'],state['point'],solver_success=False)
            body=recovery.encode(state);p.write_bytes(body);_,receipt=recovery._read(q);receipt['state']=recovery.pin(body);q.write_bytes(recovery.encode(receipt))
            with self.assertRaisesRegex(ValueError,'certificate rejected'):recovery.restore(d,j)
    def test_changed_problem_creates_different_identity(self):
        j=recovery.jobs()[0];changed=copy.deepcopy(j);changed['target'][0]=.8
        with tempfile.TemporaryDirectory() as d:
            recovery.run(d);self.assertIsNone(recovery.restore(d,changed))
            self.assertEqual(len(list((Path(d)/'states').glob('*.json'))),3)
    def test_missing_state_rejects_receipt(self):
        j=recovery.jobs()[0]
        with tempfile.TemporaryDirectory() as d:
            recovery.run(d);p,_=recovery._paths(d,recovery.identity(j));p.unlink()
            with self.assertRaisesRegex(ValueError,'without its state'):recovery.restore(d,j)
    def test_stop_after_state_recovery_does_not_refit(self):
        j=recovery.jobs()[0];fit=numerical.recover(j['target'],j['curvature'])
        def stop():raise InterruptedError('invented interruption')
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(InterruptedError):recovery.commit_candidate(d,j,fit['point'],before_receipt=stop)
            state=recovery.restore(d,j)
            self.assertEqual(state['reuse'],'RECOVERED_UNCOMMITTED_LOCAL_STATE');self.assertFalse(state['new_fit'])
            self.assertEqual(recovery.restore(d,j)['reuse'],'VERIFIED_COMMITTED_STATE')
    def test_environment_identity_cannot_be_self_attested(self):
        j=recovery.jobs()[0];fit=numerical.recover(j['target'],j['curvature'])
        with tempfile.TemporaryDirectory() as d:
            recovery.commit_candidate(d,j,fit['point']);state=recovery.restore(d,j)['state'];state['contract']['python']='other'
            with self.assertRaisesRegex(ValueError,'identity changed'):recovery.validate_state(state,recovery.identity(j))

if __name__=='__main__':unittest.main()
