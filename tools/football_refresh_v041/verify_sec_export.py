"""Recover a quarantined SEC export only with exact full-table DOM hash parity.

Runs offline. It writes a separate verification result and never alters v041.
Input/output paths are explicit; this file performs no network requests.
"""
import argparse, collections, copy, datetime, gzip, hashlib, importlib.util, json
from pathlib import Path
import sys, tempfile, unittest, zipfile

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'src'))
spec = importlib.util.spec_from_file_location('football_refresh', ROOT / 'src' / '__main__.py')
refresh = importlib.util.module_from_spec(spec)
spec.loader.exec_module(refresh)

def canonical(rows):
    return json.dumps(rows, ensure_ascii=False, separators=(',', ':')).encode('utf-8')

def verify(original, receipt):
    if original['headers'] != receipt['headers'] or receipt['headers'] != refresh.ngs_avail.HEAD:
        raise ValueError('header_mismatch')
    rows = copy.deepcopy(original['rows'])
    if len(rows) != receipt['row_count'] or any(len(r) != 9 for r in rows):
        raise ValueError('row_shape_or_count')
    correction = receipt['export_discrepancies']['name_correction']
    i = correction['zero_based_row']
    if rows[i][4] != correction['export_value']:
        raise ValueError('correction_precondition')
    rows[i][4] = correction['rendered_value']
    dashes = sum(c == '—' for r in rows for c in r[5:])
    if dashes != receipt['export_discrepancies']['non_source_emdash_cells']:
        raise ValueError('dash_count')
    for r in rows:
        for j in range(5, 9):
            if r[j] == '—': r[j] = '-'
    raw = canonical(rows)
    if len(raw) != receipt['canonical_utf8_bytes'] or hashlib.sha256(raw).hexdigest() != receipt['canonical_rows_sha256']:
        raise ValueError('full_table_dom_hash_mismatch')
    if dict(collections.Counter(r[0] for r in rows)) != receipt['team_counts']:
        raise ValueError('team_counts')
    seed = dict(headers=receipt['headers'], rows=rows, row_count=len(rows))
    normalized, rejected = refresh.sec_rows(seed)
    if rejected or len(normalized) != len(rows):
        raise ValueError('normalization_rejected_rows')
    for r in normalized:
        r['source_url'] = receipt['source_url']
        r['observed_at'] = receipt['observed_at']
        r['capture_method'] = 'DOM-verified rendered table, not original PDF'
    return rows, normalized, refresh.availability_summary(normalized, rejected)

class Tests(unittest.TestCase):
    def setUp(self):
        self.seed = dict(headers=refresh.ngs_avail.HEAD, rows=[['Texas','10/17/26','vs. A','74','Wrong Name','Questionable','Out','—','—']])
        corrected = [['Texas','10/17/26','vs. A','74','Right Name','Questionable','Out','-','-']]
        b = canonical(corrected)
        self.receipt = dict(headers=refresh.ngs_avail.HEAD, row_count=1, canonical_rows_sha256=hashlib.sha256(b).hexdigest(), canonical_utf8_bytes=len(b), team_counts={'Texas':1}, source_url='https://example.org', observed_at='2026-10-16T22:24:23Z', export_discrepancies=dict(name_correction=dict(zero_based_row=0, export_value='Wrong Name', rendered_value='Right Name'), non_source_emdash_cells=2))
    def test_exact_dom_parity_and_null_status(self):
        rows,norm,cov = verify(self.seed,self.receipt)
        self.assertEqual(norm[0]['player_name'],'Right Name')
        self.assertIsNone(norm[0]['statuses']['game_day'])
        self.assertFalse(norm[0]['historical_point_in_time_approved'])
        self.assertEqual(cov['rows'],1)
        self.assertEqual(self.seed['rows'][0][4],'Wrong Name')
    def test_extra_row_rejected(self):
        self.seed['rows'] *= 2
        with self.assertRaises(ValueError): verify(self.seed,self.receipt)
    def test_any_status_change_rejected(self):
        self.seed['rows'][0][5] = 'Available'
        with self.assertRaisesRegex(ValueError,'dom_hash'): verify(self.seed,self.receipt)
    def test_any_team_change_rejected(self):
        self.seed['rows'][0][0] = 'Other'
        with self.assertRaises(ValueError): verify(self.seed,self.receipt)
    def test_wrong_hash_rejected(self):
        self.receipt['canonical_rows_sha256'] = '0'*64
        with self.assertRaises(ValueError): verify(self.seed,self.receipt)
    def test_unobserved_correction_rejected(self):
        self.seed['rows'][0][4] = 'Different Name'
        with self.assertRaisesRegex(ValueError,'precondition'): verify(self.seed,self.receipt)
    def test_header_swap_rejected(self):
        self.seed['headers'] = list(reversed(self.seed['headers']))
        with self.assertRaisesRegex(ValueError,'header'): verify(self.seed,self.receipt)
    def test_counter_disagreement_rejected(self):
        self.receipt['team_counts'] = {'Texas':2}
        with self.assertRaisesRegex(ValueError,'team_counts'): verify(self.seed,self.receipt)

def main():
    p=argparse.ArgumentParser(); p.add_argument('--input'); p.add_argument('--receipt'); p.add_argument('--output'); p.add_argument('--self-test-only',action='store_true'); a=p.parse_args()
    tests=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Tests))
    if not tests.wasSuccessful(): raise SystemExit(1)
    if a.self_test_only: return
    raw=gzip.decompress(Path(a.input).read_bytes())
    if hashlib.sha256(raw).hexdigest() != '391f95a7758d2818c0bbb362d15ab371cb52fae6e0e3c370fed0d9d7f798f862': raise ValueError('original_raw_hash')
    receipt=json.loads(Path(a.receipt).read_text()); rows,norm,coverage=verify(json.loads(raw),receipt)
    out=Path(a.output);out.mkdir(parents=True,exist_ok=False)
    capture=dict(headers=receipt['headers'],rows=rows,row_count=len(rows),source_url=receipt['source_url'],observed_at=receipt['observed_at'],verification=receipt)
    files={'capture.json.gz':gzip.compress(refresh.pack(capture),mtime=0),'rows.jsonl.gz':gzip.compress(b''.join(refresh.pack(x)+b'\n' for x in norm),mtime=0),'dom_receipt.json':refresh.pack(receipt)}
    report=dict(version='v041-sec-dom-verification',observed_at=receipt['observed_at'],verified_at=refresh.stamp(),status='verified_rendered_table',tests_passed=tests.testsRun,coverage=coverage,source_requests=0,paid_provider_requests=0,subscription_credits=0,original_quarantine_sha256=hashlib.sha256(raw).hexdigest(),original_quarantine_retained=True,original_v041_outcome_unchanged=True,full_archive_or_season_coverage_claimed=False,files={n:dict(bytes=len(b),sha256=hashlib.sha256(b).hexdigest()) for n,b in files.items()})
    files['report.json']=refresh.pack(report)
    for n,b in files.items(): (out/n).write_bytes(b)
    with zipfile.ZipFile(out/'sports_edge_lab_sec_verification_return_20261016T222423Z.zip','w',zipfile.ZIP_DEFLATED) as z:
        for n,b in files.items():z.writestr(n,b)
    print(json.dumps(report,indent=2))

if __name__ == '__main__':main()
