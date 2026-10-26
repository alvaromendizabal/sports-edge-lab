"""Execute the public notebook through IPython or an optional separate kernel."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import sys
import tempfile


def verify_outputs(notebook: dict) -> dict:
    """Check the saved review, including rich output and the following cell."""
    cells = [cell for cell in notebook["cells"] if cell["cell_type"] == "code"]
    if not cells or [cell.get("execution_count") for cell in cells] != list(range(1, len(cells) + 1)):
        raise ValueError("not every code cell executed in order")
    outputs = [output for cell in cells for output in cell.get("outputs", [])]
    if any(output.get("output_type") == "error" for output in outputs):
        raise ValueError("notebook contains an error output")
    formats = {name for output in outputs for name in output.get("data", {})}
    if not {"text/html", "image/svg+xml"}.issubset(formats):
        raise ValueError("saved rich table or figure is missing")
    last_text = "".join(output.get("text", "") for output in cells[-1].get("outputs", []))
    if "PUBLIC_REVIEW_COMPLETE" not in last_text:
        raise ValueError("the final persistence-check cell did not finish")
    return {"code_cells": len(cells), "rich_formats": sorted(formats), "final_cell_completed": True}


def main() -> None:
    import nbformat

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--mode", choices=("in-process", "kernel"), default="in-process")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    notebook = nbformat.read(root / "notebooks/engineering_review.ipynb", as_version=4)
    if args.mode == "in-process":
        from IPython.core.interactiveshell import InteractiveShell
        from IPython.utils.capture import capture_output
        shell = InteractiveShell.instance()
        count = 0
        for cell in notebook.cells:
            if cell.cell_type != "code":
                continue
            count += 1
            with capture_output() as captured:
                result = shell.run_cell(cell.source, store_history=True)
            if result.error_before_exec or result.error_in_exec:
                raise RuntimeError("notebook cell failed") from (result.error_before_exec or result.error_in_exec)
            cell.execution_count = count
            cell.outputs = []
            for name, value in (("stdout", captured.stdout), ("stderr", captured.stderr)):
                if value:
                    cell.outputs.append(nbformat.v4.new_output("stream", name=name, text=value))
            cell.outputs.extend(nbformat.v4.new_output("display_data", data=output.data, metadata=output.metadata)
                                for output in captured.outputs)
    else:
        from nbclient import NotebookClient
        from jupyter_client import KernelManager
        from jupyter_client.kernelspec import KernelSpecManager
        with tempfile.TemporaryDirectory(prefix="sports-edge-kernel-") as temp:
            kernel_path = Path(temp) / "sports-edge-review"
            kernel_path.mkdir()
            (kernel_path / "kernel.json").write_text(json.dumps({
                "argv": [sys.executable, "-m", "ipykernel_launcher", "-f", "{connection_file}"],
                "display_name": "Sports Edge review", "language": "python"}))
            specs = KernelSpecManager(kernel_dirs=[temp], ensure_native_kernel=False)
            connection = {"transport": "ipc", "ip": str(Path(temp) / "ipc")} if sys.platform != "win32" else {}
            manager = KernelManager(kernel_name="sports-edge-review", kernel_spec_manager=specs, **connection)
            NotebookClient(notebook, km=manager, timeout=90, resources={"metadata": {"path": str(root)}}).execute()
    errors = [output for cell in notebook.cells for output in cell.get("outputs", []) if output.get("output_type") == "error"]
    if errors:
        raise RuntimeError("notebook returned error outputs")
    notebook.metadata["sports_edge_execution"] = {"mode": args.mode, "synthetic_only_fitting": True}
    verify_outputs(notebook)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    nbformat.write(notebook, args.output)
    persisted = verify_outputs(nbformat.read(args.output, as_version=4))
    print(json.dumps({"status": "PASS", "mode": args.mode, **persisted,
                      "synthetic_only_fitting": True, "saved_and_reopened": True, "output": str(args.output)}))


if __name__ == "__main__":
    main()
