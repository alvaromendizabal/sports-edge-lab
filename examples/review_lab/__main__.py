"""Run the public synthetic example without credentials or third-party packages."""
import argparse
import json
from pathlib import Path
from .core import write_run


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=119)
    args = parser.parse_args()
    result = write_run(args.output, args.seed)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
