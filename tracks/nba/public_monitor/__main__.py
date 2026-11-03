"""Run an offline, invented NBA evidence-admission demonstration."""
import json

from .contracts import walkthrough

print(json.dumps(walkthrough(), indent=2, sort_keys=True))
