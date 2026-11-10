"""Public boundary, exact evidence, deterministic page, and publication tests."""
import base64
import copy
import gzip
import json
from pathlib import Path
import re
import tempfile
import unittest
from unittest.mock import patch

import build_review_n063 as build
import export_site_n063 as export


class N063PublicTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data=build.load()
        cls.html=(build.HERE/"season_review_n063.html").read_text()
    def changed(self):
        return copy.deepcopy(self.data["current"])
    def test_exact_authenticated_projection_and_original_counts(self):
        self.assertEqual(build.identity((build.HERE/build.PROJECTION_NAME).read_bytes()),build.PROJECTION_PIN)
        c=self.data["current"]
        self.assertEqual(c["owner_actual"]["new_fits"],25030)
        self.assertEqual(c["owner_actual"]["new_issued_rows"],3650)
        self.assertEqual(c["n063_execution"]["new_scientific_fits"],0)
    def test_all_272_games_and_570_historical_results_are_preserved(self):
        c=self.data["current"]
        self.assertEqual(len(c["games"]),272);self.assertEqual(len(c["historical_games"]),570)
        self.assertEqual(sum(g["completed"]for g in c["games"]),135)
        self.assertEqual(sum(g["home_score"]==g["away_score"]for g in c["games"]if g["completed"]),1)
    def test_selected_card_population_and_target_count(self):
        cards=self.data["current"]["issued_cards"]
        self.assertEqual(len(cards),113);self.assertEqual(sum(len(c["targets"])for c in cards),339)
        self.assertTrue(all(c["status"]=="ORIGINAL_ISSUED_RESEARCH_CARD"for c in cards))
        card=next(c for c in cards if c["game_id"]=="2026_09_BUF_MIN")
        self.assertEqual([card["targets"][t]["prediction"]for t in ("win","margin","total")],[.4213,-1.7,49.3])
    def test_all_provider_game_target_cells_and_reasons_remain(self):
        c=self.data["current"];self.assertEqual(len(c["provider_cells"]),2448)
        self.assertTrue(all(r["qualified_probability"]is None and r["reason_codes"]for r in c["provider_cells"]))
    def test_actual_metrics_and_earlier_archive_stay_separate(self):
        c=self.data["current"];self.assertEqual(len(c["season_metrics"]),540)
        self.assertEqual(len(c["paired_comparisons"]),252);self.assertEqual(len(self.data["retained"]["rows"]),1349)
        old=json.loads(gzip.decompress((build.HERE/"public_projection_n062.json.gz").read_bytes()))
        self.assertEqual(self.data["retained"]["rows"],old["scoreboards"])
    def test_distinct_target_populations_and_negative_findings(self):
        c=self.data["current"];r={(r["study"],r["target"]):r["n"]for r in c["chosen_policy_metrics"]if r["season"]==2026}
        self.assertEqual(r[("retained_n061","win")],121);self.assertEqual(r[("retained_n061","margin")],122)
        self.assertEqual(r[("score_history_n062","win")],134);self.assertEqual(r[("score_history_n062","margin")],135)
        self.assertEqual(c["negative_findings"]["score_graph_isolated_comparisons"],18)
        self.assertEqual(c["negative_findings"]["holm_significant"],0)
    def test_injury_temporal_exclusions_are_not_missing_health(self):
        i=self.data["current"]["injuries"]
        self.assertEqual((i["source_rows"],i["future_pregame_admitted_rows"],i["post_start_monitoring_only_rows"]),(362,32,330))
        self.assertFalse(i["absence_is_known_healthy"]);self.assertFalse(i["full_roster_coverage_claimed"])
    def test_original_partial_cannot_be_promoted(self):
        c=self.changed();c["owner_actual"]["status"]="COMPLETE"
        with self.assertRaisesRegex(ValueError,"partial"):build.validate(c)
    def test_prepared_release_cannot_claim_fits(self):
        c=self.changed();c["n063_execution"]["new_scientific_fits"]=1
        with self.assertRaisesRegex(ValueError,"invented execution"):build.validate(c)
    def test_missing_game_or_provider_is_rejected(self):
        c=self.changed();c["games"].pop()
        with self.assertRaisesRegex(ValueError,"event census"):build.validate(c)
        c=self.changed();c["provider_cells"].pop()
        with self.assertRaisesRegex(ValueError,"provider/target"):build.validate(c)
    def test_fabricated_qualified_market_probability_is_rejected(self):
        c=self.changed();c["provider_cells"][0]["qualified_probability"]=.5
        with self.assertRaisesRegex(ValueError,"Unproved provider"):build.validate(c)
    def test_original_issue_clock_after_cutoff_is_rejected(self):
        c=self.changed();row=c["issued_cards"][0]["targets"]["win"]
        row["actual_issue_at_utc"]="2027-01-01T00:00:00Z"
        with self.assertRaisesRegex(ValueError,"chronology"):build.validate(c)
    def test_missing_future_result_cannot_be_filled_with_zero(self):
        c=self.changed();g=next(g for g in c["games"]if not g["completed"]);g["home_score"]=0
        with self.assertRaisesRegex(ValueError,"Future game"):build.validate(c)
    def test_joint_distribution_and_rounded_rescoring_are_rejected(self):
        c=self.changed();c["issued_cards"][0]["coherent_joint_score_distribution"]=True
        with self.assertRaisesRegex(ValueError,"distribution capability"):build.validate(c)
        c=self.changed();c["issued_cards"][0]["targets"]["margin"]["proper_scores_recomputed_from_display"]=True
        with self.assertRaisesRegex(ValueError,"rescored"):build.validate(c)
    def test_private_source_path_and_active_recipe_field_are_rejected(self):
        for key,value in (("source_note","s3://private-bucket/raw"),("recipe_id","active_private_recipe")):
            c=self.changed();c[key]=value
            with self.assertRaises(ValueError):build.validate(c)
    def test_generated_page_is_deterministic_and_embeds_exact_data(self):
        self.assertEqual(self.html,build.build(self.data))
        encoded=re.search(r'const DATA_GZIP="([^"]+)";',self.html).group(1)
        decoded=json.loads(gzip.decompress(base64.b64decode(encoded)))
        self.assertEqual(decoded,self.data)
    def test_active_ui_is_research_only_with_no_external_script(self):
        visible=re.sub(r"<script\b[^>]*>.*?</script>","",self.html,flags=re.S|re.I)
        visible=re.sub(r"<style\b[^>]*>.*?</style>","",visible,flags=re.S|re.I)
        self.assertIsNone(re.search(r"\b(?:bet|bets|betting|wager|wagers|bankroll|parlay|staking)\b",visible,re.I))
        self.assertIsNone(re.search(r"<(?:script|img|iframe)\b[^>]*\bsrc\s*=",self.html,re.I))
        self.assertIn("Kickoff time TBD",self.html);self.assertIn("Time unconfirmed",self.html)
    def test_archive_links_resolve_and_old_browser_tests_are_retained(self):
        targets=export.local_links(self.html)
        self.assertIn(build.HERE/"season_review_n054.html",targets)
        script=(build.HERE/"browser_test.cjs").read_text()
        self.assertEqual(script.count("require('./browser_n063.cjs')"),1)
        self.assertIn("require('./browser_season_n054.cjs')",script)
    def test_export_rejects_unpinned_commit(self):
        for commit in ("main","abc","A"*40,"../private"):
            with self.assertRaises(ValueError):export.projection(self.html,commit)
    def test_export_rewrites_every_relative_document_to_exact_commit(self):
        commit="a"*40;html=export.projection(self.html,commit)
        before_scripts=re.sub(r"<script\b[^>]*>.*?</script>","",html,flags=re.S|re.I)
        for href in re.findall(r'href="([^"]+)"',before_scripts):
            self.assertTrue(href.startswith("#")or href=="provenance.json"or commit in href,href)
        self.assertIn("https://raw.githubusercontent.com/",html)
        self.assertIn("provenance.json",html)
    def test_export_does_not_rewrite_quoted_script_text(self):
        test=self.html.replace('</script>','const fixture=\'href="README.md"\';</script>')
        projected=export.projection(test,"a"*40)
        self.assertIn('const fixture=\'href="README.md"\';',projected)
    def test_export_checks_every_input_against_commit_and_records_provenance(self):
        with tempfile.TemporaryDirectory()as tmp:
            seen=[]
            def committed(commit,path):
                seen.append(path);return path.read_bytes()
            with patch.object(export,"_committed_bytes",committed):
                receipt=export.export(Path(tmp),"a"*40)
            self.assertEqual(receipt["actual_owner_cycle"],"N062")
            self.assertEqual(receipt["next_owner_execution_status"],"PREPARED_NOT_OWNER_EXECUTED")
            self.assertEqual(receipt["new_publication_fits"],0)
            self.assertIn(export.ROOT/"docs/PUBLICATION_BOUNDARY.md",seen)
            self.assertTrue(all(build.HERE/name in seen for name in export.INPUTS))
            self.assertEqual({p.name for p in Path(tmp).iterdir()},{"index.html","provenance.json"})
    def test_dirty_publication_input_blocks_before_output(self):
        with tempfile.TemporaryDirectory()as tmp:
            output=Path(tmp)/"site"
            with patch.object(export,"_committed_bytes",lambda commit,path:path.read_bytes()+b"changed"):
                with self.assertRaisesRegex(ValueError,"Uncommitted publication input"):export.export(output,"a"*40)
            self.assertFalse(output.exists())
    def test_unexpected_hosted_file_is_not_deleted_or_published(self):
        with tempfile.TemporaryDirectory()as tmp:
            output=Path(tmp);(output/"unapproved.txt").write_text("must remain")
            with self.assertRaisesRegex(ValueError,"only index"):export.validate_output_directory(output)
            self.assertEqual((output/"unapproved.txt").read_text(),"must remain")


if __name__=="__main__":unittest.main()

