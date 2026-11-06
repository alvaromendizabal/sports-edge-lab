import copy,json,pathlib,re,unittest
from build_review_n053 import build,validate
from export_site_n053 import projection
ROOT=pathlib.Path(__file__).resolve().parent


class CurrentReviewN053Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.data=json.loads((ROOT/'current_review_n053.json').read_text())

    def test_deterministic_evidence(self):self.assertEqual((ROOT/'review_n053.html').read_text(),build(self.data))

    def test_future_preparation_has_no_credit(self):
        for key in ['owner_native_fits','owner_correction_fits','owner_forecasts']:
            d=copy.deepcopy(self.data);d['next'][key]=1
            with self.subTest(key=key),self.assertRaisesRegex(ValueError,'future execution'):validate(d)

    def test_no_promotion_original_refit_or_order(self):
        for key in ['owner_research_accepted','protected_original_refits','actual_orders']:
            d=copy.deepcopy(self.data);d[key]=1
            with self.subTest(key=key),self.assertRaises(ValueError):validate(d)

    def test_no_recrediting_cards_as_additional_rows(self):
        d=copy.deepcopy(self.data);d['new_total_issue_rows']+=28
        with self.assertRaises(ValueError):validate(d)

    def test_missing_and_duplicated_study_comparisons_rejected(self):
        for operation in ['remove','duplicate']:
            d=copy.deepcopy(self.data);rows=d['science']['paired_comparisons']
            if operation=='remove':rows.pop()
            else:rows[1]=rows[0]
            with self.subTest(operation=operation),self.assertRaisesRegex(ValueError,'paired closure'):validate(d)

    def test_selected_years_cannot_include_current_year(self):
        d=copy.deepcopy(self.data);d['science']['selection_years'].append(2026)
        with self.assertRaisesRegex(ValueError,'selection boundary'):validate(d)

    def test_issue_must_precede_kickoff(self):
        d=copy.deepcopy(self.data);c=d['cards'][0];g=next(g for g in d['games'] if g['game_id']==c['game_id']);c['actual_issue_at']=g['kickoff_utc']
        with self.assertRaisesRegex(ValueError,'postgame issue'):validate(d)

    def test_fit_and_feature_clocks_cannot_postdate_issue(self):
        for key in ['base_feature_asof','fit_completed_by_target']:
            d=copy.deepcopy(self.data);c=d['cards'][0]
            if key=='base_feature_asof':c[key]='2027-01-01T00:00:00+00:00'
            else:c[key]['win']='2027-01-01T00:00:00+00:00'
            with self.subTest(key=key),self.assertRaisesRegex(ValueError,'issue clock'):validate(d)

    def test_less_probability_cannot_use_greater_orientation(self):
        d=copy.deepcopy(self.data);c=next(c for c in d['cover_references'] if c['orientation'].endswith('LESS_THAN'));c['conditional_cover_probability_nonpush']=c['probability_above_threshold']/(1-c['probability_equal_threshold'])
        with self.assertRaisesRegex(ValueError,'conditional probability'):validate(d)

    def test_no_source_only_predictive_credit(self):
        for k in ['new_market_path_fits','new_market_path_forecasts','completed_study_recomputed']:
            d=copy.deepcopy(self.data);d['completed_source'][k]=1
            with self.subTest(key=k),self.assertRaisesRegex(ValueError,'source-only'):validate(d)

    def test_current_references_do_not_become_scored_cohort(self):
        d=copy.deepcopy(self.data);d['winner_references'][0]['metric_eligible']=True
        with self.assertRaisesRegex(ValueError,'scored cohort'):validate(d)

    def test_unknown_quote_clock_stays_missing(self):
        self.assertTrue(all(r['quote_at'] is None for r in self.data['winner_references'] if r['provider']=='Kalshi'))
        self.assertTrue(all(not r['acquired_at'] for r in self.data['winner_references'] if r['game_id']=='2026_09_JAX_BAL'))

    def test_censoring_and_units_close(self):
        source=self.data['completed_source'];c=source['minute_window_census']
        self.assertEqual(sum(c['window_'+str(m)+'_rows'] for m in [1,3,5,10]),source['expanded_window_rows'])
        for m in [1,3,5,10]:self.assertEqual(c['window_'+str(m)+'_complete']+c['window_'+str(m)+'_censored'],source['feature_rows'])

    def test_correction_counts_and_unique_comparisons_are_required(self):
        d=copy.deepcopy(self.data);d['correction']['report_rows']-=1
        with self.assertRaisesRegex(ValueError,'correction closure'):validate(d)
        d=copy.deepcopy(self.data);d['correction']['paired_rows'][1]=d['correction']['paired_rows'][0]
        with self.assertRaisesRegex(ValueError,'duplicate comparisons'):validate(d)

    def test_correction_freeze_must_precede_later_states(self):
        d=copy.deepcopy(self.data);s=d['correction']['selection'];s['frozen_at_utc']=s['earliest_later_start']
        with self.assertRaisesRegex(ValueError,'freeze clock'):validate(d)

    def test_current_year_cannot_select_correction(self):
        d=copy.deepcopy(self.data);d['correction']['selection']['seasons'].append(2026)
        with self.assertRaisesRegex(ValueError,'selection boundary'):validate(d)

    def test_prior_studies_cannot_be_refitted(self):
        for key in ['repeated_designation_only_fits','repeated_injury_only_fits']:
            d=copy.deepcopy(self.data);d['science'][key]=1
            with self.subTest(key=key),self.assertRaisesRegex(ValueError,'protected study reuse'):validate(d)

    def test_selected_baseline_margin_is_identical(self):
        rows=[r for r in self.data['correction']['selected_pairs'] if r['target']=='margin']
        self.assertEqual(len(rows),5)
        for r in rows:self.assertEqual([r[k] for k in ['left_minus_right','bootstrap_95_low','bootstrap_95_high']],[0.0,0.0,0.0])

    def test_hosted_projection_preserves_complete_embedded_science(self):
        current=build(self.data);original=(ROOT/'review.html').read_text();published,history=projection(current,original,json.loads((ROOT/'readiness_n049.json').read_text()),'a'*40)
        pattern=r'<script[^>]*type="application/json"[^>]*>(.*?)</script>'
        self.assertEqual(re.findall(pattern,original,re.S),re.findall(pattern,history,re.S));self.assertEqual(re.findall(pattern,current,re.S),re.findall(pattern,published,re.S));self.assertIn('previous.html',published)

    def test_public_export_excludes_private_source_and_recipe_fields(self):
        raw=json.dumps(self.data)
        self.assertIsNone(re.search(r's3://|arn:aws:|sagemaker|/workspace/|/home/|X-Amz-|AKIA[A-Z0-9]{16}|component_bindings|model_sha256|raw_source|source_body|direct201_|designation_only32|lambda=',raw))


if __name__=='__main__':unittest.main()
