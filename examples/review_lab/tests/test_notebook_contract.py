import unittest

from examples.review_lab.execute_notebook import verify_outputs


class SavedNotebookContractTests(unittest.TestCase):
    def setUp(self):
        self.notebook = {"cells": [
            {"cell_type": "code", "execution_count": 1, "outputs": [
                {"output_type": "display_data", "data": {"text/html": "<table></table>"}},
                {"output_type": "display_data", "data": {"image/svg+xml": "<svg/>"}}]},
            {"cell_type": "code", "execution_count": 2, "outputs": [
                {"output_type": "stream", "text": "PUBLIC_REVIEW_COMPLETE\n"}]}]}

    def test_complete_rich_outputs_and_later_cell(self):
        result = verify_outputs(self.notebook)
        self.assertEqual(result["code_cells"], 2)
        self.assertTrue(result["final_cell_completed"])

    def test_unexecuted_cell_is_rejected(self):
        self.notebook["cells"][1]["execution_count"] = None
        with self.assertRaisesRegex(ValueError, "every code cell"):
            verify_outputs(self.notebook)

    def test_error_output_is_rejected(self):
        self.notebook["cells"][0]["outputs"].append({"output_type": "error"})
        with self.assertRaisesRegex(ValueError, "error output"):
            verify_outputs(self.notebook)

    def test_missing_persisted_figure_is_rejected(self):
        self.notebook["cells"][0]["outputs"].pop()
        with self.assertRaisesRegex(ValueError, "rich table or figure"):
            verify_outputs(self.notebook)

    def test_missing_following_completion_is_rejected(self):
        self.notebook["cells"][1]["outputs"] = []
        with self.assertRaisesRegex(ValueError, "final persistence"):
            verify_outputs(self.notebook)


if __name__ == "__main__":
    unittest.main()
