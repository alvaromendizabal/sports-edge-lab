import unittest
from examples.basketball_contracts.execute_feature_notebook import verify_outputs

class FeatureNotebookTests(unittest.TestCase):
    def setUp(self):
        self.n={'metadata':{'sports_edge_execution':{'model_fits':0,'private_data_loaded':False,'new_source_requests':0}},'cells':[
          {'cell_type':'code','execution_count':1,'outputs':[{'output_type':'display_data','data':{'text/html':'<table></table>'}}]},
          {'cell_type':'code','execution_count':2,'outputs':[{'output_type':'display_data','data':{'application/vnd.plotly.v1+json':{}}},{'output_type':'display_data','data':{'application/vnd.plotly.v1+json':{}}}]},
          {'cell_type':'code','execution_count':3,'outputs':[{'output_type':'stream','text':'FEATURE_RELEASE_REVIEW_COMPLETE'}]}]}
    def test_reopened_artifacts_verified(self):self.assertEqual(verify_outputs(self.n)['native_plotly_outputs'],2)
    def test_missing_plotly_artifact_rejected(self):
        self.n['cells'][1]['outputs'].pop()
        with self.assertRaisesRegex(ValueError,'two persisted'):verify_outputs(self.n)
    def test_no_completion_after_figures_rejected(self):
        self.n['cells'][2]['outputs']=[]
        with self.assertRaisesRegex(ValueError,'later persistence'):verify_outputs(self.n)
    def test_private_or_network_claim_rejected(self):
        self.n['metadata']['sports_edge_execution']['new_source_requests']=1
        with self.assertRaisesRegex(ValueError,'acquisition'):verify_outputs(self.n)
