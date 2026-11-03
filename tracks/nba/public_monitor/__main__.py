"""Run an offline, invented NBA evidence-admission demonstration."""
import json

from .contracts import walkthrough
from .snapshot_versions import walkthrough as version_walkthrough

print(json.dumps({"result_admission": walkthrough(), "prediction_versions": version_walkthrough()}, indent=2, sort_keys=True))
