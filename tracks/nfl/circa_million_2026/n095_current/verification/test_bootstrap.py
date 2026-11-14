"""Ordinary CPython launcher round-trip. All model, source, and owner bytes here are synthetic."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import zipfile


def sha(data):
    return hashlib.sha256(data).hexdigest()


def pins(files):
    return {name: {'sha256': sha(body), 'bytes': len(body)} for name, body in files.items()}


def encoded(obj):
    return json.dumps(obj, sort_keys=True).encode()


def archive(path, files):
    with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED) as z:
        for name, body in files.items():
            z.writestr(name, body)


def check(launcher):
    with tempfile.TemporaryDirectory() as tmp:
        home = Path(tmp)
        previous, latest, overlay = home/'previous.pyz', home/'latest.zip', home/'overlay.pyz'
        baseline = b'["example"]'
        ret = {'science/games.json': baseline}
        ret['RETURN_MANIFEST.json'] = encoded({'release':'N094', 'identity':{'project':'nfl'}, 'fixture':False, 'files':pins(ret)})
        archive(latest, ret)
        inherited = {'__main__.py':b'', 'n094_durable.py':b"def guard(path):\n    return path.name.startswith('old_')\n", 'old-baseline':b'[]'}
        inherited['N094_RECOVERY_MANIFEST.json'] = encoded({'files':[{'role':'baseline_games','member':'old-baseline',**pins({'old-baseline':b'[]'})['old-baseline']}]})
        inherited['N094_CODE_MANIFEST.json'] = encoded({'files':pins(inherited)})
        archive(previous, inherited)
        pt, rt = sha(previous.read_bytes()), sha(latest.read_bytes())
        config = {'BUCKET':'fixture', 'PREVIOUS':pt, 'NEWEST':rt,'PARENT_NAME':previous.name,'RETURN_NAME':latest.name,
                  'OBJECTS':[(previous.name,pt,previous.stat().st_size,'fake'),(latest.name,rt,latest.stat().st_size,'fake')],
                  'BASELINES':{'baseline_games':'science/games.json'},'STAMP':(2026,1,1,0,0,0),'REGION':'test',
                  'EXPECTED_OWNER':'test','PROJECT_REL':('project',),'HOME_PATH':tmp,'CACHE_REL':('cache','bootstrap'),
                  'AUTH_REL':('cache','auth'),'OLD_RETURN_GUARD':'old_','NEW_RETURN_GUARD':'new_'}
        sentinel = b"def main():\n    import sys,os,hashlib\n    p=sys.argv[0]; assert hashlib.sha256(open(p,'rb').read()).hexdigest()==sys.argv[sys.argv.index('--expected-sha256')+1]\n    assert os.environ['N095_BOOTSTRAP_SHA256'];print('SYNTHETIC_OWNER_ENTRY_REACHED');return 0\n"
        mods = {'n095_runner.py':sentinel, 'n095_bootstrap_config.py':''.join(f'{k}={v!r}\n' for k,v in config.items()).encode()}
        def pack(module_pins):
            archive(overlay,{**mods,'OVERLAY.json':encoded({'files':module_pins}),'__main__.py':Path(launcher).read_bytes()})
            return sha(overlay.read_bytes())
        def run(digest, *opts):
            return subprocess.run([sys.executable,str(overlay),'--expected-sha256',digest,*opts],capture_output=True,text=True)
        digest = pack(pins(mods))
        assert run(digest,'--overlay-self-test').returncode==0
        bad = run('0'*64,'--overlay-self-test')
        assert bad.returncode and 'N095_OVERLAY_SHA256_MISMATCH' in bad.stderr
        first = run(digest,'--fixture-root',tmp)
        assert first.returncode==0, first.stdout+first.stderr
        assert '"authenticated_warm_reuse": false' in first.stdout and 'SYNTHETIC_OWNER_ENTRY_REACHED' in first.stdout
        second = run(digest,'--fixture-root',tmp)
        assert second.returncode==0 and '"authenticated_warm_reuse": true' in second.stdout
        proof=next((home/'project'/'cache'/'bootstrap').glob('*.proof.json'))
        proof.write_bytes(b'{"broken":true}')
        third=run(digest,'--fixture-root',tmp)
        assert third.returncode==0 and '"authenticated_warm_reuse": false' in third.stdout
        corrupt=pins(mods);corrupt['n095_runner.py']['sha256']='a'*64
        invalid=run(pack(corrupt),'--overlay-self-test')
        assert invalid.returncode and 'N095_OVERLAY_MEMBER' in invalid.stderr
        print('PASS CPython synthetic launcher SHA, member CRC/SHA, cold/warm dispatch, damaged proof and rejection')
if __name__=='__main__':
    check(sys.argv[1])
