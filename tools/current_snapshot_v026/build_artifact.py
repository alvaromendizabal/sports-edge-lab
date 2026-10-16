"""Build the reviewed current-snapshot PYZ; execute tests on AWS."""
import hashlib
import json
import zipfile
from pathlib import Path

root=Path(__file__).resolve().parent
artifact=root/"sports_edge_lab_current_v026_20261016.pyz"
with zipfile.ZipFile(artifact,"w",zipfile.ZIP_DEFLATED) as z:
    for path in sorted((root/"src").glob("*.py")):
        info=zipfile.ZipInfo(path.name,date_time=(2026,10,16,0,0,0))
        info.compress_type=zipfile.ZIP_DEFLATED
        z.writestr(info,path.read_bytes())
manifest={"artifact":str(artifact),"bytes":artifact.stat().st_size,
    "sha256":hashlib.sha256(artifact.read_bytes()).hexdigest(),"version":"sports-edge-lab-current-v026",
    "source_sha256":{str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((root/"src").glob("*.py"))},
    "self_tests":"30 tests bundled; AWS preflight before credentials or acquisition",
    "limits":{"odds_credits":500,"stats_calls":100,"app_seconds":600,"aws_seconds":900,
        "workers":4,"props_per_track":12,"maximum_requests_per_second":2,"lease_seconds":1200,
        "odds_reserve_floor":100000},
    "arguments":["--odds-credits","500","--stats-calls","100","--max-seconds","600",
        "--workers","4","--props-per-track","12","--odds-reserve-floor","100000"],
    "report_prefix":"shared/acquisition/current/", "lease_key":"shared/control/current-acquisition/v026-active.json"}
(root/"artifact_manifest.json").write_text(json.dumps(manifest,indent=2)+"\n")
print(json.dumps(manifest,indent=2))
