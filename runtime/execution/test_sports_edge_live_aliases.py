"""Generic per-run literal paths and authoritative progress on invented inputs."""
import copy
import os
from pathlib import Path
import tempfile
import unittest
from sports_edge_live import LiveExecutionLog, atomic_json, process_identity, project_measurements, utc

class StandardLogPathTests(unittest.TestCase):
    def test_incompatible_denominator_does_not_invent_zero_eta(self):
        source={'completed':3740,'remaining':0,'total':636,'eta_seconds':0,'work_unit':'files'}
        before=copy.deepcopy(source);row=project_measurements(source)
        self.assertEqual(source,before);self.assertEqual(row['progress']['completed'],3740)
        self.assertIsNone(row['progress']['total']);self.assertIsNone(row['progress']['eta_seconds'])

    def test_standard_named_wrapper_prefix_needs_no_nested_duplicate_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            with LiveExecutionLog(root/'LIVE_EXECUTION',project='nfl',release='TEST',interval=.1) as logger:
                self.assertEqual(logger.live_directory,root)
                self.assertEqual(Path(logger.live_aliases['log']),logger.paths['log'])
                self.assertFalse((root/'LIVE_EXECUTION.logs').exists())

    def test_every_project_gets_live_names_without_duplicate_storage(self):
        with tempfile.TemporaryDirectory() as directory:
            for project in ('nfl','fbs','nba','ncaa_basketball','ncaam','ncaaw','other_sport'):
                with LiveExecutionLog(Path(directory)/project,project=project,release='B083_TEST',interval=.1) as logger:
                    logger.event('ENGINEERING_EVENT',new_sports_fits=0)
                    for kind,path in logger.live_aliases.items():
                        self.assertEqual(Path(path).name,'LIVE_EXECUTION.'+kind)
                        self.assertTrue(os.path.samefile(path,logger.paths[kind]))
                        self.assertIn('ENGINEERING_EVENT',Path(path).read_text())
                self.assertTrue(logger.receipt()['standard_live_log_paths'])

    def test_existing_different_alias_and_symlink_fail_without_overwriting(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);live=root/'live';live.mkdir();conflict=live/'LIVE_EXECUTION.log';conflict.write_text('ORIGINAL')
            with self.assertRaisesRegex(ValueError,'ALREADY_HAS_DIFFERENT'):
                LiveExecutionLog(root/'execution',project='nba',release='TEST',live_directory=live)
            self.assertEqual(conflict.read_text(),'ORIGINAL')
            conflict.unlink();conflict.symlink_to(root/'execution.log')
            with self.assertRaisesRegex(ValueError,'SYMLINK'):
                LiveExecutionLog(root/'execution2',project='nba',release='TEST',live_directory=live)

    def test_bound_new_snapshot_does_not_inherit_old_operation_counters(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);progress=root/'PROGRESS.json';identity=process_identity(os.getpid())
            with LiveExecutionLog(root/'execution',project='nba',release='TEST',invocation_id='ours',interval=.1) as logger:
                logger.bind_progress(progress,identity)
                envelope={'invocation_id':'ours','producer_identity':identity,'at_utc':utc()}
                atomic_json(progress,{**envelope,'stage_name':'OLD','completed':200,'total':200,'remaining':0,'eta_seconds':0})
                self.assertEqual(logger.heartbeat()['measurements']['progress']['completed'],200)
                atomic_json(progress,{**envelope,'stage_name':'NEW','at_utc':utc()})
                measured=logger.heartbeat()['measurements']
                self.assertEqual(measured['stage']['stage_name'],'NEW')
                self.assertIsNone(measured['progress']['completed']);self.assertIsNone(measured['progress']['eta_seconds'])

    def test_other_project_fit_scope_fields_remain_available(self):
        measured=project_measurements({'invocation_fit_counts':{'scope':'PRESERVED_NFL_SCOPE',
            'source_phase':'prior','reported_counts':{'new':12}},'native':{'observed_peak_concurrent_native_fits':4}})
        self.assertEqual(measured['fits']['scope'],'PRESERVED_NFL_SCOPE')
        self.assertEqual(measured['fits']['reported_counts'],{'new':12})
        self.assertEqual(measured['fits']['peak_concurrent_native_fits_observed'],4)


if __name__=='__main__':unittest.main()
