"""Generate static NCAA review pages from the committed sanitized aggregates."""
from __future__ import annotations
import argparse
import hashlib
from html import escape
import json
from pathlib import Path

from progress import demo_scenarios

ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
HOST='https://alvaro-ncaa-research-review.alv-mendizabal.chatgpt.site'


def evidence(league):
    data=json.loads((ROOT/'tracks'/league/'evidence.json').read_text())
    if data['schema']!='sports-edge-lab.public.ncaa-review.v1' or data['league']!=league:raise ValueError('evidence identity')
    if [r['name'] for r in data['providers']]!=['Kalshi','Polymarket','DraftKings']:raise ValueError('exclusive provider scope')
    if data['market_advantage']['demonstrated'] is not False:raise ValueError('unqualified market claim')
    if data['evaluation']['current_outcomes_used_for_selection'] is not False:raise ValueError('current selection leakage')
    for model in data['models']:
        if set(model['panels'])!={'pooled','2025','2026'}:raise ValueError('season closure')
        if model['panels']['pooled']['N']!=model['panels']['2025']['N']+model['panels']['2026']['N']:
            raise ValueError('pooled game count')
        for panel in model['panels'].values():
            if model['target']=='win' and sum(b['N'] for b in panel['calibration_bins'])!=panel['N']:
                raise ValueError('calibration support')
    return data


def render_track(data):
    league=data['league'];sibling='ncaaw' if league=='ncaam' else 'ncaam'
    template=(HERE/'dashboard.html.tmpl').read_text()
    embedded=json.dumps(data,sort_keys=True,separators=(',',':'),allow_nan=False).replace('<','\\u003c')
    for key,value in {'__TITLE__':escape(data['league_label']),'__SIBLING__':sibling,
        '__SIBLING_LABEL__':"women's basketball" if sibling=='ncaaw' else "men's basketball",
        '__LEAGUE__':league,'__EVIDENCE__':embedded,
        '__PROGRESS_DEMO__':json.dumps(demo_scenarios(),sort_keys=True,separators=(',',':'),allow_nan=False).replace('<','\\u003c')}.items():template=template.replace(key,value)
    return template


def render_landing(data):
    cards=[]
    for d in data:
        model=next(m for m in d['models'] if m['target']=='win' and 'LogLoss' in m['selected_for'])
        p=model['panels']['pooled'];league=d['league'];label="Men's basketball" if league=='ncaam' else "Women's basketball"
        cards.append(f'<a class="card" href="{HOST}/tracks/{league}/index.html"><div class="label">{label}</div><div class="score">{p["LogLoss"]:.4f}<span>historical log loss</span></div><p>{p["N"]:,} games · two separately evaluated seasons</p><strong>Explore the evidence <span aria-hidden="true">↗</span></strong></a>')
    return '''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="description" content="Sports Edge Lab college basketball: objective-specific historical evidence, uncertainty and reproducible engineering contracts."><title>NCAA Evidence Review · Sports Edge Lab</title><style>
*{box-sizing:border-box}body{margin:0;background:#f4f3ed;color:#172723;font:16px/1.65 system-ui,sans-serif}main{max-width:1110px;margin:auto;padding:36px 32px 42px}a{color:#136a55;text-underline-offset:4px}a:focus-visible{outline:3px solid #285b86;outline-offset:5px}header{display:flex;align-items:center;justify-content:space-between;padding-bottom:30px;border-bottom:1px solid #cedbd0;font-size:13px}.brand{font-weight:750;letter-spacing:-.035em;font-size:18px;color:#172723;text-decoration:none}.tag{font-size:11px;letter-spacing:.17em;text-transform:uppercase;font-weight:700;color:#136a55;margin-top:64px}h1{font-size:clamp(44px,7vw,78px);line-height:1.04;letter-spacing:-.065em;max-width:840px;margin:20px 0 26px}h1 span{color:#136a55}.intro{max-width:740px;color:#53665a;font-size:19px;margin:0}.cards{display:grid;grid-template-columns:1fr 1fr;gap:22px;margin:42px 0 25px}.card{display:block;border:1px solid #c8d8ca;background:#fffefb;border-radius:18px;padding:28px;text-decoration:none;color:#172723;transition:transform .15s,border-color .15s}.card:hover{border-color:#136a55;transform:translateY(-3px)}.label{font-size:15px;font-weight:700}.score{font-size:59px;line-height:1.15;letter-spacing:-.06em;margin-top:20px;font-variant-numeric:tabular-nums}.score span{display:block;font-size:12px;letter-spacing:0;color:#596b65;font-weight:400;margin-top:9px}.card p{font-size:13px;color:#596b65;margin:18px 0 25px}.card strong{font-size:13px;display:flex;justify-content:space-between;color:#136a55}.note{font-size:13px;color:#596b65;max-width:900px}.status{margin-top:34px;padding:22px 24px;border-radius:14px;background:#fcf0d5;border:1px solid #e7d7b2}.status strong{color:#714217;font-size:14px}.status p{margin:8px 0 0;font-size:13px;color:#66513a}.links{display:grid;grid-template-columns:1fr 1fr 1fr;gap:20px;border-top:1px solid #cedbd0;margin-top:44px;padding-top:26px}.links a{font-weight:700;font-size:13px}.links p{font-size:12px;color:#596b65}.footer{font-size:11px;color:#68796e;margin-top:40px}@media(max-width:640px){main{padding:25px 20px}.tag{margin-top:40px}h1{font-size:47px}.intro{font-size:16px}.cards,.links{grid-template-columns:1fr}.cards{gap:15px;margin-top:30px}.card{padding:25px}.score{font-size:50px}.links{gap:7px}.status{padding:18px}.footer{line-height:1.8}}@media(prefers-reduced-motion:reduce){.card{transition:none}.card:hover{transform:none}}
</style></head><body><main><header><a class="brand" href="https://github.com/alvaromendizabal/sports-edge-lab">Sports Edge Lab</a><span>College basketball / 2026</span></header><div class="tag">Evidence review · 03 November 2026</div><h1>Forecasts you can<br><span>interrogate.</span></h1><p class="intro">Explore the historical models by objective, inspect the uncertainty, and follow the engineering contracts that keep current-season claims separate.</p><section class="cards" aria-label="Separate NCAA basketball reviews">'''+''.join(cards)+'''</section><p class="note">These are development-exposed historical selections on exact shared cohorts, not untouched test results or a prospective betting record. Men's and women's populations remain separate. The public model IDs disclose results while keeping active research recipes private.</p><section class="status"><strong>Latest execution: 108 historical target fits committed; current refresh incomplete.</strong><p>The B033 attempt completed its registered historical study across both leagues, then stopped when current-source refresh selected another project’s summary. It waited 69.1 minutes before 21.6 minutes of scientific work. The current game inventory and provider comparisons were not refreshed. Open either track to inspect the stage evidence, retained coverage and an executable progress/ETA demonstration. Historical headline selections remain preserved; no current market advantage is claimed.</p></section><section class="links" aria-label="Review resources"><div><a href="https://github.com/alvaromendizabal/sports-edge-lab/tree/main/examples/ncaa_review">Run the invented example ↗</a><p>Chronological scoring, explicit fees, measured admission and honest progress estimates. Python standard library only.</p></div><div><a href="https://github.com/alvaromendizabal/sports-edge-lab/blob/main/examples/ncaa_review/README.md">Read the methodology ↗</a><p>Selection exposure, calibration, point errors and week-level descriptive uncertainty, with meaningful negative tests.</p></div><div><a href="https://github.com/alvaromendizabal/sports-edge-lab/blob/main/docs/PUBLICATION_BOUNDARY.md">Inspect the publication boundary ↗</a><p>Sanitized aggregates and generic contracts are public. Private data, active weights and execution artifacts remain private.</p></div></section><footer class="footer">Built by Alvaro Mendizabal · Sports Edge Lab<br>Static, self-contained review pages. No tracking, external fonts, third-party scripts or live provider requests.</footer></main></body></html>
'''


def outputs():
    data=[evidence(league) for league in ('ncaam','ncaaw')]
    return {**{ROOT/'tracks'/d['league']/'index.html':render_track(d) for d in data},
            ROOT/'docs/ncaa/index.html':render_landing(data)}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--check',action='store_true');args=p.parse_args()
    receipts=[]
    for path,text in outputs().items():
        if args.check:
            if not path.is_file() or path.read_text()!=text:raise SystemExit('Stale generated page: '+str(path.relative_to(ROOT)))
        else:path.parent.mkdir(parents=True,exist_ok=True);path.write_text(text)
        b=text.encode();receipts.append({'path':str(path.relative_to(ROOT)),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()})
    print(json.dumps({'status':'EXACT_GENERATION_VERIFIED' if args.check else 'GENERATED','pages':receipts},indent=2))


if __name__=='__main__':main()
