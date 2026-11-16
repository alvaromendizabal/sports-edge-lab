"""Cross-check the versioned N123 public response and all science assets, without authentication."""
from concurrent.futures import ThreadPoolExecutor
from hashlib import sha256
from pathlib import Path
import json
import urllib.request

def main():
    base='https://sports-edge-lab-nfl.alv-mendizabal.chatgpt.site/circa/'
    here=Path(__file__).resolve().parent
    public=here/'n123_current' if (here/'n123_current').is_dir() else here/'public'
    expected=[(base,pub) for pub in [public/'index.html']]
    expected.extend((base+'n123/'+('' if f.name=='index.html' else f.name),f) for f in sorted(public.iterdir()) if f.name!='README.md')
    def probe(pair):
        url,f=pair
        req=urllib.request.Request(url,headers={'User-Agent':'SportsEdgeLab-PublicReleaseVerification/1.0','Cache-Control':'no-cache'})
        with urllib.request.urlopen(req,timeout=35) as response:
            payload=response.read()
            digest=sha256(payload).hexdigest()
            assert response.status==200 and digest==sha256(f.read_bytes()).hexdigest(),(url,response.status,digest)
            return {'url':url,'bytes':len(payload),'sha256':digest,'status':response.status}
    with ThreadPoolExecutor(8) as pool:receipts=list(pool.map(probe,expected))
    print(json.dumps({'verified':len(receipts),'responses':receipts},indent=2))
if __name__=='__main__':main()
