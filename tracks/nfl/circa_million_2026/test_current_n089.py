"""Public rendering, injection, immutability and exact payload contracts."""
import copy
import gzip
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('circa_renderer',HERE/'build_current_n089.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

class CircaRendererTests(unittest.TestCase):
    def source(self):
        source=HERE/'current/evidence.json'
        self.assertTrue(source.is_file(),'The actual scientific payload must exist')
        data=json.loads(source.read_text())
        if data.get('history_asset'):
            histories=json.loads(gzip.decompress((source.parent/'history.json.gz').read_bytes()))
            for view in data['model_views']:view['history']=histories[view['model_id']]
        return data
    def test_exact_public_payload_and_no_inline_injection(self):
        data=self.source();data['gaps'].append('</script><script>alert("x")</script>&')
        raw=m.render(data,(HERE/'site_template_n089.html.in').read_text(),(HERE/'current_n089.js').read_text()).decode()
        embedded=raw.split('<script id="circa-data" type="application/json">')[1].split('</script>')[0]
        self.assertEqual(json.loads(embedded),m.public_payload(data))
        self.assertNotIn('</script>',embedded)
        self.assertIn('JMac View',raw)
        self.assertIn('Cover probabilities',raw)
    def test_private_paths_rejected_and_unknown_top_fields_omitted(self):
        data=self.source();data['private_dump']={'secret':'must never appear'}
        self.assertNotIn('private_dump',m.public_payload(data))
        data['gaps'].append('/home/sagemaker-user/private.npy')
        with self.assertRaises(ValueError):m.public_payload(data)
    def test_idempotent_render_preserves_input_and_rejects_overwrite(self):
        data=self.source();before=copy.deepcopy(data)
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'payload.json';p.write_text(json.dumps(data));out=Path(tmp)/'render'
            a=m.prepare_circa_dashboard(p,out);b=m.prepare_circa_dashboard(p,out)
            self.assertEqual(a,b);self.assertEqual(a['state'],'PREPARED_NOT_DEPLOYED');self.assertEqual(a['new_fits'],0)
            self.assertEqual(json.loads(p.read_text()),before)
            data['gaps'].append('Changed snapshot');p.write_text(json.dumps(data))
            with self.assertRaises(FileExistsError):m.prepare_circa_dashboard(p,out)
    def test_actual_no_cover_distribution_no_expected_points(self):
        data=self.source();self.assertGreater(len(data['current_board']['games']),5)
        for view in data['model_views']:
            for row in view['slate']:
                if row['p_cover'] is None:self.assertIsNone(row['expected_points'])
            for name in ['model_card','user_adjusted_card']:
                card=view.get(name)
                if not card:continue
                picks=card.get('picks',[])
                self.assertEqual(len({p['game_id'] for p in picks}),len(picks))
                if len(picks)==5 and any(p['expected_points'] is None for p in picks):self.assertIsNone(card['expected_points'])

if __name__=='__main__':unittest.main()
