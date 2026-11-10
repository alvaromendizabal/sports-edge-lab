"""Export an exact committed NFL N063 review as a bounded static Site."""
from __future__ import annotations
import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path
from urllib.parse import unquote,urlsplit
from build_review_n063 import HERE, build, identity, load

ROOT=HERE.parents[1]
REPO="https://github.com/alvaromendizabal/sports-edge-lab"
RAW="https://raw.githubusercontent.com/alvaromendizabal/sports-edge-lab/"
INPUTS=("build_review_n063.py","season_review_n063.html","public_projection_n063.json.gz",
        "public_projection_n062.json.gz","test_public_n063.py","browser_n063.cjs",
        "browser_test.cjs","export_site_n063.py","season_review_n054.html","README.md",
        "README_N062_PREPARED_SNAPSHOT.md","CURRENT_METHODOLOGY.md","CURRENT_MODEL_CARD.md",
        "N063_REVIEW.md")

def require_commit(commit):
    if not isinstance(commit,str)or not re.fullmatch("[0-9a-f]{40}",commit):
        raise ValueError("Exact canonical forty-character commit required")
    return commit

def _html_parts(body):
    return re.split(r"(<script\b[^>]*>.*?</script\s*>)",body,flags=re.I|re.S)

def local_links(body):
    result=set()
    for index,part in enumerate(_html_parts(body)):
        if index%2:continue
        for target in re.findall(r'href="([^"]+)"',part):
            parsed=urlsplit(target)
            if parsed.scheme or parsed.netloc or target.startswith("#"):continue
            path=(HERE/unquote(parsed.path)).resolve()
            if not path.is_relative_to(ROOT)or not path.is_file()or path.is_symlink():
                raise ValueError("Unresolved or unsafe public link: "+target)
            result.add(path)
    return result

def projection(body,commit):
    require_commit(commit)
    def rewrite(match):
        target=match.group(1);parts=urlsplit(target)
        if parts.scheme or parts.netloc or target.startswith("#"):return match.group(0)
        path=(HERE/unquote(parts.path)).resolve()
        if not path.is_relative_to(ROOT)or not path.is_file()or path.is_symlink():
            raise ValueError("Unresolved bounded public link")
        prefix=RAW if path.name.endswith((".json",".json.gz"))else REPO+"/blob/"
        suffix=("#"+parts.fragment)if parts.fragment else""
        return 'href="'+prefix+commit+"/"+path.relative_to(ROOT).as_posix()+suffix+'"'
    output="".join(part if index%2 else re.sub(r'href="([^"]+)"',rewrite,part)
                   for index,part in enumerate(_html_parts(body)))
    original="Canonical source and dated reports are preserved in the NFL repository."
    if output.count(original)!=1:raise ValueError("Canonical publication marker missing or duplicated")
    return output.replace(original,'Canonical commit: <a href="'+REPO+"/commit/"+commit+'">'+commit+'</a>. <a href="provenance.json">Publication provenance</a>.')

def _committed_bytes(commit,path):
    return subprocess.check_output(["git","show",commit+":"+path.relative_to(ROOT).as_posix()],cwd=ROOT)

def validate_output_directory(output):
    output=Path(output).absolute()
    if any(p.is_symlink()for p in (output,*output.parents)):
        raise ValueError("Hosted output aliases are forbidden")
    if output.exists():
        if not output.is_dir():raise ValueError("Hosted output must be a directory")
        for item in output.iterdir():
            if item.name not in {"index.html","provenance.json"}or not item.is_file()or item.is_symlink():
                raise ValueError("Hosted output must contain only index.html and provenance.json")
    return output

def export(output,commit):
    require_commit(commit);output=validate_output_directory(output)
    current=(HERE/"season_review_n063.html").read_text()
    if current!=build():raise ValueError("Public HTML differs from pinned builder inputs")
    inputs={HERE/name for name in INPUTS}|local_links(current)
    pins={}
    for path in sorted(inputs):
        if any(p.is_symlink()for p in (path,*path.parents)):raise ValueError("Publication input aliases are forbidden")
        body=path.read_bytes()
        if body!=_committed_bytes(commit,path):raise ValueError("Uncommitted publication input: "+path.name)
        pins[path.relative_to(ROOT).as_posix()]=identity(body)
    data=load()["current"];body=projection(current,commit)
    provenance={"schema":"nfl.public.n063.site-provenance.v1","role":"bounded_public_static_snapshot",
        "canonical_repository":REPO,"canonical_commit":commit,"canonical_inputs":pins,
        "hosted_files":{"index.html":identity(body.encode())},"evidence_as_of":data["observed_at"],
        "schedule_observed_at":data["snapshot"]["source_observed_at"],"schedule_snapshot":data["snapshot"],
        "evidence_counts":data["counts"],"actual_owner_cycle":"N062","actual_owner_status":data["owner_actual"]["status"],
        "actual_owner_fits":data["owner_actual"]["new_fits"],"actual_owner_issued_rows":data["owner_actual"]["new_issued_rows"],
        "next_owner_cycle":"N063","next_owner_execution_status":data["n063_execution"]["status"],
        "new_publication_fits":0,"new_publication_issues":0,"new_publication_source_captures":0,
        "original_versus_reconstructed_distinctions_preserved":True,"rounded_cards_rescored":False,
        "retained_scoreboard_rows":1349,"automatic_promotion":False,"private_runtime_archives_published":False,
        "source_projection_physical":identity((HERE/"public_projection_n063.json.gz").read_bytes())}
    output.mkdir(parents=True,exist_ok=True)
    (output/"index.html").write_text(body)
    (output/"provenance.json").write_text(json.dumps(provenance,indent=2,sort_keys=True)+"\n")
    return provenance

if __name__=="__main__":
    parser=argparse.ArgumentParser();parser.add_argument("--commit",required=True);parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args();print(json.dumps(export(args.output,args.commit),indent=2))

