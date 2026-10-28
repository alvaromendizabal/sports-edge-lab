"""Execute and reopen the aggregate notebook; hosted CI requires a separate kernel."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import sys
import tempfile


def verify_outputs(notebook):
    cells=[c for c in notebook['cells'] if c['cell_type']=='code']
    if len(cells)<3 or [c.get('execution_count') for c in cells] != list(range(1,len(cells)+1)):
        raise ValueError('every coverage notebook code cell must execute')
    outputs=[o for c in cells for o in c.get('outputs',[])]
    if any(o.get('output_type')=='error' for o in outputs):
        raise ValueError('persisted notebook error')
    figures=sum('application/vnd.plotly.v1+json' in o.get('data',{}) for o in outputs)
    if figures!=2:
        raise ValueError('two persisted native Plotly figures required')
    if not any('text/html' in o.get('data',{}) for o in outputs):
        raise ValueError('exact aggregate table must persist')
    if not any('MARKET_COVERAGE_REVIEW_COMPLETE' in str(o.get('text','')) for o in cells[-1].get('outputs',[])):
        raise ValueError('later persistence cell must complete')
    meta=notebook.get('metadata',{}).get('sports_edge_execution',{})
    if meta.get('model_fits')!=0 or meta.get('private_data_loaded') is not False or meta.get('new_source_requests')!=0:
        raise ValueError('aggregate review cannot imply modeling or acquisition')
    return {'code_cells':len(cells),'native_plotly_outputs':figures,'saved_error_outputs':0,
            'model_fits':0,'private_data_loaded':False,'new_source_requests':0}


def main():
    import nbformat
    from nbclient import NotebookClient
    from jupyter_client import KernelManager
    from jupyter_client.kernelspec import KernelSpecManager
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--mode',choices=('kernel','in-process'),default='kernel')
    args=parser.parse_args();root=Path(__file__).resolve().parents[2]
    notebook=nbformat.read(root/'notebooks/basketball_market_coverage.ipynb',as_version=4)
    for cell in notebook.cells:
        if cell.cell_type=='code':cell.outputs=[];cell.execution_count=None
    if args.mode == 'in-process':
        from IPython.core.interactiveshell import InteractiveShell
        from IPython.utils.capture import capture_output
        shell=InteractiveShell.instance()
        count=0
        for cell in notebook.cells:
            if cell.cell_type != 'code':
                continue
            count += 1
            with capture_output() as captured:
                result=shell.run_cell(cell.source,store_history=True)
            if result.error_before_exec or result.error_in_exec:
                raise RuntimeError('notebook cell failed') from (result.error_before_exec or result.error_in_exec)
            cell.execution_count=count
            for name,value in (('stdout',captured.stdout),('stderr',captured.stderr)):
                if value:
                    cell.outputs.append(nbformat.v4.new_output('stream',name=name,text=value))
            cell.outputs.extend(nbformat.v4.new_output('display_data',data=o.data,metadata=o.metadata) for o in captured.outputs)
    else:
        with tempfile.TemporaryDirectory(prefix='sports-edge-coverage-kernel-') as temp:
            kernel=Path(temp)/'sports-edge-coverage';kernel.mkdir()
            (kernel/'kernel.json').write_text(json.dumps({'argv':[sys.executable,'-m','ipykernel_launcher','-f','{connection_file}'],'display_name':'Sports Edge coverage audit','language':'python'}))
            specs=KernelSpecManager(kernel_dirs=[temp],ensure_native_kernel=False)
            connection={'transport':'ipc','ip':str(Path(temp)/'ipc')} if sys.platform!='win32' else {}
            manager=KernelManager(kernel_name='sports-edge-coverage',kernel_spec_manager=specs,**connection)
            NotebookClient(notebook,km=manager,timeout=90,resources={'metadata':{'path':str(root)}}).execute()
    notebook.metadata['sports_edge_execution']={'mode':args.mode,'model_fits':0,'private_data_loaded':False,'new_source_requests':0,'descriptive_development_analysis':True}
    verify_outputs(notebook);args.output.parent.mkdir(parents=True,exist_ok=True);nbformat.write(notebook,args.output)
    receipt=verify_outputs(nbformat.read(args.output,as_version=4))
    print(json.dumps({'status':'PASS','mode':args.mode,'saved_and_reopened':True,**receipt},sort_keys=True))

if __name__=='__main__':main()
