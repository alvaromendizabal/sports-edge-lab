"""Execute the public notebook in a real kernel and reopen its saved rich outputs."""
import argparse
from pathlib import Path
import nbformat
from nbclient import NotebookClient

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'notebooks/fbs_branch_review.ipynb'
MARKER = 'FBS_PUBLIC_NOTEBOOK_VERIFIED'


def execute(output):
    notebook = nbformat.read(SOURCE, as_version=4)
    code = [cell for cell in notebook.cells if cell.cell_type == 'code']
    for cell in code:
        cell.outputs = []
        cell.execution_count = None
    NotebookClient(notebook, timeout=180, kernel_name='python3', resources={'metadata': {'path': str(ROOT)}}).execute()
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    nbformat.write(notebook, output)
    saved = nbformat.read(output, as_version=4)
    saved_code = [cell for cell in saved.cells if cell.cell_type == 'code']
    if any(cell.execution_count is None for cell in saved_code):
        raise ValueError('not all code cells executed')
    if any(out.output_type == 'error' for cell in saved_code for out in cell.outputs):
        raise ValueError('saved notebook contains an execution error')
    rich = sum('text/html' in out.get('data', {}) for cell in saved_code for out in cell.outputs)
    final = ''.join(out.get('text', '') for out in saved_code[-1].outputs)
    if rich < 2 or MARKER not in final:
        raise ValueError('persisted rich outputs or final completion missing')
    return {'kernel': 'python3', 'executed_code_cells': len(saved_code), 'persisted_html_outputs': rich,
            'reopened': True, 'final_marker': MARKER, 'actual_owner_fits': 0}


def main():
    import json
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    print(json.dumps(execute(args.output), indent=2))


if __name__ == '__main__': main()
