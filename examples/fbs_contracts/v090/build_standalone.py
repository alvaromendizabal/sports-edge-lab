"""Embed the reviewed public FBS page and JSON in one offline HTML report."""
import argparse
import hashlib
import json
from pathlib import Path


def build(site, output):
    site, output = Path(site), Path(output)
    page = (site/'index.html').read_text()
    css = (site/'styles.css').read_text()
    js = (site/'app.js').read_text()
    if page.count('<link rel="stylesheet" href="styles.css">') != 1 or page.count('<script src="app.js" defer></script>') != 1:
        raise ValueError('Unexpected source-page asset declaration')
    page = page.replace('<link rel="stylesheet" href="styles.css">', '<style>'+css+'</style>')
    page = page.replace('<script src="app.js" defer></script>', '')
    page = page.replace('href="./"', 'href="#main"').replace('href="README.md"', 'href="#execution"')
    archive = 'https://github.com/alvaromendizabal/sports-edge-lab/tree/fc5573bfa656d8cd87c6b33a8b4a92707e7112b2/docs/fbs/v079'
    page = page.replace('href="../v079/"', 'href="'+archive+'"')
    page = page.replace('href="../v079/market-readiness.html"', 'href="'+archive+'/market-readiness.html"')
    embedded = []
    for filename, element_id in [('review.json','fbs090-inline-review'), ('games.json','fbs090-inline-games')]:
        text = (site/'data'/filename).read_text()
        json.loads(text)
        # Prevent any source text from closing its own script element.
        safe = text.replace('<', '\\u003c').replace('\u2028','\\u2028').replace('\u2029','\\u2029')
        embedded.append('<script type="application/json" id="'+element_id+'">'+safe+'</script>')
    embedded.append('<script>'+js.replace('</script','<\\/script')+'</script>')
    page = page.replace('</body>', '\n'.join(embedded)+'\n</body>')
    if 'src="app.js"' in page or 'href="styles.css"' in page:
        raise ValueError('External runtime asset remains')
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(page)
    return {'bytes':output.stat().st_size,'sha256':hashlib.sha256(output.read_bytes()).hexdigest(),
            'embedded_public_models':len(json.loads((site/'data/review.json').read_text())['models']),
            'owner_research_executed':0,'runtime_network_required':False}


if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--site',required=True);ap.add_argument('--output',required=True)
    a=ap.parse_args();print(json.dumps(build(a.site,a.output),sort_keys=True))
