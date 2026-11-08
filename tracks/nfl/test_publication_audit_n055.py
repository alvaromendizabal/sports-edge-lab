import copy,hashlib,json,pathlib,unittest
from build_season_review_n054 import load,build
from publication_audit_n055 import audit
from build_delivery_exports_n055 import records

class PublicationAuditTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.data=load();cls.audited=audit(cls.data)
 def test_complete_inventory_and_numeric_support_remain_distinct(self):
  a=self.audited;rows={r['record_set']:r for r in a['completeness']}
  self.assertEqual(rows['Model role / target cells']['present'],51408);self.assertEqual(rows['Model role / target cells']['numeric_values'],8921)
  self.assertEqual(rows['Provider / target / horizon cells']['present'],24480)
  self.assertEqual([rows[p+' grid']['present'] for p in ['DraftKings','Kalshi','Polymarket']],[8160]*3)
  self.assertEqual([rows[p+' grid']['numeric_values'] for p in ['DraftKings','Kalshi','Polymarket']],[689,1107,1710])
 def test_holes_and_duplicate_cells_are_rejected(self):
  for key in ['model_rows','provider_rows']:
   d=dict(self.data);d[key]=d[key][:-1]
   with self.assertRaises(ValueError):audit(d)
   d[key]=self.data[key]+[self.data[key][0]]
   with self.assertRaises(ValueError):audit(d)
 def test_diagnostic_is_additive_and_never_replaces_original_plan(self):
  original=json.dumps(self.data['next'],sort_keys=True);a=audit(self.data)
  self.assertEqual(json.dumps(self.data['next'],sort_keys=True),original)
  self.assertEqual(self.data['next']['status'],'PREPARED_NOT_OWNER_EXECUTED')
  self.assertEqual(a['owner_attempt']['status'],'ACTUAL_DIAGNOSTIC_PACKAGING_FAILURE');self.assertFalse(a['owner_attempt']['full_durable_evidence_closure']);self.assertEqual(a['owner_attempt']['new_scientific_result_credit'],0)
  self.assertFalse(a['original_data_modified']);self.assertEqual(a['new_fits_from_publication'],0)
 def test_export_retains_every_field_and_null(self):
  source={'table':[{'game_id':'x','value':None,'detail':{'clock':None,'x':.123456789123}}],'metadata':{'status':'dated'}}
  rows=list(records(source));self.assertEqual(len(rows),2);self.assertEqual(rows[0]['value'],'');self.assertEqual(json.loads(rows[0]['record_json']),source['table'][0]);self.assertEqual(json.loads(rows[1]['record_json']),source['metadata'])
 def test_active_page_has_audit_and_explicit_team_labels(self):
  html=build(self.data);self.assertNotIn('__PUBLICATION_AUDIT_JSON__',html);self.assertTrue('N056 actual partial' in html);self.assertIn('Los Angeles Rams',html);self.assertIn('Los Angeles Chargers',html);self.assertTrue('N057 repairs the final census parser' in html);self.assertTrue('Original base snapshot time:' in html)

if __name__=='__main__':unittest.main()
