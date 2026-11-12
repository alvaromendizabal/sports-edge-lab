"""Real Chromium checks of the saved R2 page, filtering, download, and mobile layout."""
from pathlib import Path
import csv
import io
import json
import os

ROOT = Path(__file__).resolve().parents[2]
PAGE = ROOT / "docs/ncaa/b063r2.html"

def main():
    from playwright.sync_api import sync_playwright
    result = {"status": "PASS", "browser": "Chromium", "viewports": [], "script_errors": [], "external_requests": [], "candidate_csv_rows": []}
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, executable_path=os.environ.get("CHROMIUM_EXECUTABLE", "/usr/bin/chromium"), args=["--no-sandbox"])
        try:
            page = browser.new_page()
            page.on("pageerror", lambda err: result["script_errors"].append(str(err)))
            page.on("request", lambda req: result["external_requests"].append(req.url) if not req.url.startswith(("file:", "data:", "blob:")) else None)
            for width in (1440, 390):
                page.set_viewport_size({"width": width, "height": 1000})
                page.goto(PAGE.as_uri())
                page.wait_for_selector("#season-leaders tbody tr")
                assert page.locator("#season-leaders tbody tr").count() == 28
                assert page.locator("#pooled-leaders tbody tr").count() == 14
                assert page.locator("#current-leaders tbody tr").count() == 14
                assert page.locator("#candidate-table tbody tr").count() == 25
                assert page.locator("#early-groups tbody tr").count() == 6
                assert page.locator("#late-groups tbody tr").count() == 11
                assert page.locator("#late-rows tbody tr").count() == 46
                assert page.locator("#outcome-sources tbody tr").count() == 38
                assert "1–25 of 164" in page.locator("#candidate-count").inner_text()
                assert page.evaluate("window.__ncaaB063R2.ownerR2Executed") is False
                page.locator("#candidate-next").click()
                assert "26–50 of 164" in page.locator("#candidate-count").inner_text()
                page.locator("#league").select_option("ncaaw")
                page.locator("#season").select_option("2026")
                page.locator("#objective").select_option("win:log_loss")
                assert page.locator("#season-leaders tbody tr").count() == 1
                assert page.locator("#current-leaders tbody tr").count() == 1
                assert page.locator("#candidate-table tbody tr").count() == 14
                assert "Women" in page.locator("#season-leaders").inner_text()
                with page.expect_download() as download_info:
                    page.locator("#download-candidates").click()
                downloaded = Path(download_info.value.path()).read_text()
                rows = list(csv.DictReader(io.StringIO(downloaded)))
                assert len(rows) == 14
                assert all(row["league"] == "ncaaw" and row["season"] == "2025–26" and row["target"] == "win" for row in rows)
                result["candidate_csv_rows"].append(len(rows))
                page.locator("#query").fill("NO_MATCH_IN_SAVED_EVIDENCE")
                assert "No rows match" in page.locator("#candidate-table").inner_text()
                assert page.locator("#candidate-next").is_disabled()
                page.locator("#reset").click()
                assert page.locator("#season-leaders tbody tr").count() == 28
                assert page.evaluate("document.documentElement.scrollWidth <= innerWidth + 1"), "Horizontal document overflow"
                for name in page.locator("a[download]").evaluate_all("nodes => nodes.map(n => n.getAttribute('href'))"):
                    assert (PAGE.parent / name).is_file(), name
                screenshot_root = os.environ.get("DASHBOARD_SCREENSHOTS")
                if screenshot_root:
                    path = Path(screenshot_root)
                    path.mkdir(parents=True, exist_ok=True)
                    page.screenshot(path=str(path / f"b063r2-{width}.png"), full_page=False)
                result["viewports"].append({"width": width, "no_horizontal_document_overflow": True, "filter_and_download_passed": True})
            assert not result["script_errors"], result["script_errors"]
            assert not result["external_requests"], result["external_requests"]
        finally:
            browser.close()
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
