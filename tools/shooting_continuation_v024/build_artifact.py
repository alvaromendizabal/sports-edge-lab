"""Package source only. All runtime/self-test execution is on AWS."""
import hashlib
import json
import zipfile
from pathlib import Path

root = Path(__file__).resolve().parent
artifact = root / "sports_edge_lab_shooting_continuation_v024_20261016.pyz"
with zipfile.ZipFile(artifact, "w", zipfile.ZIP_DEFLATED) as z:
    for path in sorted((root / "src").glob("*.py")):
        info = zipfile.ZipInfo(path.name, date_time=(2026, 10, 16, 0, 0, 0))
        info.compress_type = zipfile.ZIP_DEFLATED
        z.writestr(info, path.read_bytes())
manifest = {
    "artifact": str(artifact), "bytes": artifact.stat().st_size,
    "sha256": hashlib.sha256(artifact.read_bytes()).hexdigest(),
    "version": "sports-edge-lab-cbbd-shooting-continuation-v024",
    "source_sha256": {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
                      for p in sorted((root / "src").glob("*.py"))},
    "self_tests": "34 meaningful tests bundled; self-test gate executes on AWS before credentials and downloads",
    "limits": {"stats_http_reservations": 3000, "odds_credits": 0, "app_seconds": 2100,
               "recommended_aws_seconds": 2400, "workers": 4, "max_requests_per_second": 2,
               "max_response_bytes": 67108864},
    "command_arguments": ["--stats-calls", "3000", "--max-seconds", "2100", "--workers", "4"],
    "source_run": "20261016T005814Z-dc2ec3e9a5",
    "endpoints": ["/stats/team/shooting/season", "/stats/player/shooting/season"],
    "seasons": [2003] + list(range(2006, 2028)),
}
(root / "artifact_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
print(json.dumps(manifest, indent=2))
