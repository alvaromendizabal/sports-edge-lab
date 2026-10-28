"""Execute and reopen the basketball aggregate notebook in a real kernel."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import tempfile

from examples.review_lab.execute_notebook import verify_outputs


def verify_basketball_outputs(notebook: dict) -> dict:
    result = verify_outputs(notebook)
    outputs = [o for c in notebook['cells'] if c['cell_type']=='code' for o in c.get('outputs',[])]
    plotly_count = sum('application/vnd.plotly.v1+json' in o.get('data',{}) for o in outputs)
    if plotly_count != 1:
        raise ValueError('expected one persisted native inline Plotly figure')
    metadata = notebook.get('metadata',{}).get('sports_edge_execution',{})
    if metadata.get('model_fits') != 0 or metadata.get('private_data_loaded') is not False:
        raise ValueError('aggregate notebook must not claim private modeling')
    return {**result, 'native_inline_plotly_outputs':plotly_count, 'model_fits':0, 'private_data_loaded':False}


def main() -> None:
    import nbformat
    from nbclient import NotebookClient
    from jupyter_client import KernelManager
    from jupyter_client.kernelspec import KernelSpecManager

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args=parser.parse_args()
    root=Path(__file__).resolve().parents[2]
    notebook=nbformat.read(root/'notebooks/basketball_review.ipynb',as_version=4)
    for cell in notebook.cells:
        if cell.cell_type=='code':
            cell.outputs=[]
            cell.execution_count=None
    with tempfile.TemporaryDirectory(prefix='sports-edge-basketball-kernel-') as temp:
        kernel=Path(temp)/'sports-edge-basketball'
        kernel.mkdir()
        (kernel/'kernel.json').write_text(json.dumps({'argv':[sys.executable,'-m','ipykernel_launcher','-f','{connection_file}'],
                                                    'display_name':'Sports Edge basketball review','language':'python'}))
        specs=KernelSpecManager(kernel_dirs=[temp],ensure_native_kernel=False)
        connection={'transport':'ipc','ip':str(Path(temp)/'ipc')} if sys.platform!='win32' else {}
        manager=KernelManager(kernel_name='sports-edge-basketball',kernel_spec_manager=specs,**connection)
        NotebookClient(notebook,km=manager,timeout=90,resources={'metadata':{'path':str(root)}}).execute()
    notebook.metadata['sports_edge_execution']={'mode':'separate_kernel','model_fits':0,'private_data_loaded':False,
                                                'real_aggregate_evidence_displayed':True,'synthetic_contracts_displayed_separately':True}
    verify_basketball_outputs(notebook)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    nbformat.write(notebook,args.output)
    persisted=verify_basketball_outputs(nbformat.read(args.output,as_version=4))
    print(json.dumps({'status':'PASS','saved_and_reopened':True,**persisted},sort_keys=True))


if __name__=='__main__':
    main()
