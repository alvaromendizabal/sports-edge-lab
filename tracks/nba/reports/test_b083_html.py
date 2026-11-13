"""Lossless standalone display tests on invented HTML, without sports work."""
import json
import unittest
import b083_html as subject

class LosslessHtmlTests(unittest.TestCase):
    def setUp(self):
        self.body='<!doctype html><html><body><p>résumé</p><script id="rows" type="application/json">'+json.dumps({'rows':[1,2],'text':'<ignored> }, [ "'})+'</script><script>const DATA=JSON.parse(document.getElementById("rows").textContent);</script></body></html>\n'
    def test_exact_full_bytes_and_order_roundtrip(self):
        packed=subject.pack_html(self.body)
        self.assertEqual(subject.expand_html(packed),self.body)
        self.assertEqual(subject.pack_html(self.body),packed)
        self.assertEqual(subject.pack_html(packed),packed)
        self.assertEqual(subject.transport_receipt(packed)['script_blocks'],2)
    def test_changed_static_html_is_rejected(self):
        packed=subject.pack_html(self.body).replace('<p>résumé</p>','<p>changed</p>')
        with self.assertRaisesRegex(ValueError,'FULL_ORIGINAL_PIN'):subject.expand_html(packed)
    def test_changed_script_pin_is_rejected(self):
        packed=subject.pack_html(self.body).replace('"bytes":','"bytes":9',1)
        with self.assertRaisesRegex(ValueError,'SCRIPT_PIN_CHANGED'):subject.expand_html(packed)
    def test_missing_or_reordered_script_is_rejected(self):
        packed=subject.pack_html(self.body).replace('data-sel-gzip="0"','data-sel-gzip="9"')
        with self.assertRaisesRegex(ValueError,'SCRIPT_ORDER'):subject.expand_html(packed)
    def test_explicit_unsupported_browser_and_offline_fallback(self):
        packed=subject.pack_html(self.body)
        for value in ['DecompressionStream','latest_research_outputs.json','latest_model_review.json','latest_v9_acceptance.json','crypto.subtle.digest','__SEL_OFFLINE_ERROR__']:
            self.assertIn(value,packed)
        self.assertNotIn('fetch(',subject.BOOT)
    def test_plain_html_passes_through_and_missing_envelope_fails(self):
        self.assertEqual(subject.expand_html(self.body),self.body)
        with self.assertRaisesRegex(ValueError,'ENVELOPE_MISSING'):subject.expand_html(subject.pack_html(self.body).replace(subject.START,''))

if __name__=='__main__':unittest.main()
