"""Exact gzip transport, original-byte downloads and refusal of altered assets."""
from pathlib import Path
import base64
import gzip
import hashlib
import json
import tempfile
import unittest
import restore_snapshot_assets as storage
from b083_html import expand_html
ROOT=Path(__file__).parent
class SnapshotAssetTests(unittest.TestCase):
    def fixture(self,root):
        body=b'{"invented_rows":[1,2,3]}\n';compressed=gzip.compress(body,mtime=0);(root/'example.json.gz').write_bytes(compressed)
        pin=lambda b:{'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
        (root/storage.MANIFEST).write_text(json.dumps({'schema':storage.SCHEMA,'lossy_projection':False,'files':[{'name':'example.json','gzip_name':'example.json.gz','original_pin':pin(body),'gzip_pin':pin(compressed)}]}))
        return body
    def test_original_restored_then_reused_without_mutation(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);body=self.fixture(root)
            self.assertEqual(storage.restore(root)['files'][0]['status'],'EXACT_ORIGINAL_RESTORED')
            before=(root/'example.json').stat();self.assertEqual((root/'example.json').read_bytes(),body)
            self.assertEqual(storage.restore(root)['files'][0]['status'],'EXACT_ORIGINAL_REUSED')
            self.assertEqual((root/'example.json').stat().st_mtime_ns,before.st_mtime_ns)
    def test_altered_existing_raw_or_compressed_bytes_are_rejected(self):
        for kind,error in [('example.json','EXISTING_ORIGINAL_CHANGED'),('example.json.gz','COMPRESSED_PIN_CHANGED')]:
            with tempfile.TemporaryDirectory() as directory:
                root=Path(directory);self.fixture(root);storage.restore(root);(root/kind).write_bytes(b'altered')
                with self.assertRaisesRegex(ValueError,error):storage.restore(root)
                self.assertEqual((root/kind).read_bytes(),b'altered')
    def test_complete_public_assets_and_embedded_downloads_match_original_pins(self):
        storage.restore(ROOT);manifest=json.loads((ROOT/storage.MANIFEST).read_bytes())
        expanded=expand_html((ROOT/'latest_research_outputs.html').read_text())
        import re
        match=re.search(r'<script id="sel-json-download-data" type="application/json">(.*?)</script>',expanded,re.S)
        self.assertIsNotNone(match);downloads=json.loads(match.group(1));self.assertEqual(len(downloads),2)
        for row,download in zip(manifest['files'],downloads):
            body=(ROOT/row['name']).read_bytes();self.assertEqual(gzip.decompress(base64.b64decode(download['gzip_base64'])),body)
            self.assertEqual(storage.file_pin(ROOT/row['name']),row['original_pin']);self.assertEqual(download['original_pin'],row['original_pin'])
        self.assertIn('Download complete selected-output JSON',expanded)
        self.assertIn('latest_research_outputs.json.gz',(ROOT/'latest_research_outputs.html').read_text())
    def test_every_original_json_anchor_has_a_real_committed_fallback(self):
        from html.parser import HTMLParser
        class Anchors(HTMLParser):
            def __init__(self):super().__init__();self.rows=[]
            def handle_starttag(self,tag,attrs):
                if tag=='a':self.rows.append(dict(attrs))
        parser=Anchors();parser.feed((ROOT/'latest_research_outputs.html').read_text())
        names={row['name'] for row in json.loads((ROOT/storage.MANIFEST).read_bytes())['files']}
        for row in parser.rows:
            self.assertNotIn(row.get('href'),names)
            if row.get('data-sel-json') in names:
                self.assertEqual(row['href'],row['data-sel-json']+'.gz')
                self.assertTrue((ROOT/row['href']).is_file())
        self.assertEqual(sum(row.get('data-sel-json') in names for row in parser.rows),5)
    def test_uncompressed_inputs_are_logical_not_silently_omitted(self):
        names={row['name'] for row in json.loads((ROOT/storage.MANIFEST).read_bytes())['files']}
        self.assertEqual(names,{'latest_research_outputs.json','latest_v9_acceptance.json'})
if __name__=='__main__':unittest.main()
