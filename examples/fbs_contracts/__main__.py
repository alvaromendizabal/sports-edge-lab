import argparse
import json
from .core import run_demo

parser = argparse.ArgumentParser(description="Run wholly invented FBS chronology and resume example")
parser.add_argument("--output", required=True)
args = parser.parse_args()
print(json.dumps(run_demo(args.output), indent=2, sort_keys=True))
