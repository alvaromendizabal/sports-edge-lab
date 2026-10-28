"""Persisted rich-output checks; no optional notebook dependencies required."""
import unittest

from examples.basketball_contracts.execute_notebook import verify_basketball_outputs


class BasketballNotebookTests(unittest.TestCase):
    def setUp(self):
        self.notebook={'metadata':{'sports_edge_execution':{'model_fits':0,'private_data_loaded':False}},'cells':[
            {'cell_type':'code','execution_count':1,'outputs':[
                {'output_type':'display_data','data':{'text/html':'<table></table>'}},
                {'output_type':'display_data','data':{'image/svg+xml':'<svg/>'}},
                {'output_type':'display_data','data':{'application/vnd.plotly.v1+json':{'data':[],'layout':{}}}},
                {'output_type':'display_data','data':{'application/vnd.plotly.v1+json':{'data':[],'layout':{}}}},
                {'output_type':'display_data','data':{'application/vnd.plotly.v1+json':{'data':[],'layout':{}}}}]},
            {'cell_type':'code','execution_count':2,'outputs':[{'output_type':'stream','text':'PUBLIC_REVIEW_COMPLETE\n'}]}]}

    def test_saved_plotly_and_later_cell_verified(self):
        self.assertEqual(verify_basketball_outputs(self.notebook)['native_inline_plotly_outputs'],3)

    def test_missing_native_plotly_rejected(self):
        self.notebook['cells'][0]['outputs'].pop()
        with self.assertRaisesRegex(ValueError,'native inline Plotly'):
            verify_basketball_outputs(self.notebook)

    def test_invented_private_model_execution_rejected(self):
        self.notebook['metadata']['sports_edge_execution']['model_fits']=172
        with self.assertRaisesRegex(ValueError,'must not claim private modeling'):
            verify_basketball_outputs(self.notebook)

    def test_figure_without_later_completion_rejected(self):
        self.notebook['cells'][1]['outputs']=[]
        with self.assertRaisesRegex(ValueError,'final persistence'):
            verify_basketball_outputs(self.notebook)


if __name__=='__main__':
    unittest.main()
