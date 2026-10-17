"""Strict official Sidearm HTML recovery. Offline parser; no provider calls.

Accepts only an exact manifest game. Every structured drive must equal a counted
DOM row. Embedded publisher JSON supplies explicit home/visitor and end periods.
A blank terminal result is never guessed: only a unique, matching official PBP
end-game panel permits exclusion as period bookkeeping. This is secondary data.
"""
from html.parser import HTMLParser
from dataclasses import dataclass,field
from datetime import datetime,timezone,timedelta
import hashlib,json,re,unicodedata
from collections import Counter

class ParseRejected(ValueError):pass
def need(v,reason):
 if not v:raise ParseRejected(reason)
def norm(v):return re.sub(r'[^a-z0-9]','',unicodedata.normalize('NFKD',str(v)).lower())
def sha(v):return hashlib.sha256(v).hexdigest()
def packed(v):return json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()
@dataclass
class Node:
 tag:str
 attrs:dict=field(default_factory=dict)
 children:list=field(default_factory=list)
 def all(self,tag=None):
  for x in self.children:
   if isinstance(x,Node):
    if tag is None or x.tag==tag:yield x
    yield from x.all(tag)
 def text(self):return ' '.join(' '.join(x.text() if isinstance(x,Node) else x for x in self.children).split())
class Tree(HTMLParser):
 def __init__(self):super().__init__(convert_charrefs=True);self.root=Node('root');self.stack=[self.root]
 def handle_starttag(self,t,a):
  n=Node(t,dict(a));self.stack[-1].children.append(n)
  if t not in {'area','base','br','col','embed','hr','img','input','link','meta','param','source','track','wbr'}:self.stack.append(n)
 def handle_startendtag(self,t,a):self.handle_starttag(t,a);self.handle_endtag(t)
 def handle_endtag(self,t):
  for i in range(len(self.stack)-1,0,-1):
   if self.stack[i].tag==t:self.stack=self.stack[:i];return
 def handle_data(self,d):self.stack[-1].children.append(d)
def table_rows(table):
 out=[]
 for r in table.all('tr'):
  cells=[n.text() for n in r.children if isinstance(n,Node) and n.tag in {'td','th'}]
  if cells:out.append(cells)
 return out

def nuxt_boxscore(root):
 scripts=[n for n in root.all('script') if n.attrs.get('id')=='__NUXT_DATA__']
 need(len(scripts)==1,'unsupported_or_missing_sidearm_structured_payload')
 try:data=json.loads(''.join(x for x in scripts[0].children if isinstance(x,str)))
 except (ValueError,TypeError) as e:raise ParseRejected('invalid_sidearm_json') from e
 need(isinstance(data,list),'invalid_sidearm_reference_table')
 memo={};active=set()
 def deref(i):
  need(isinstance(i,int) and not isinstance(i,bool),'invalid_reference')
  if i<0:return None
  need(i<len(data),'reference_out_of_range')
  if i in memo:return memo[i]
  need(i not in active,'cyclic_reference');active.add(i);x=data[i]
  if isinstance(x,dict):v={k:deref(j) for k,j in x.items()}
  elif isinstance(x,list):
   need(not x or not isinstance(x[0],str),'unsupported_tagged_reference')
   v=[deref(j) for j in x]
  else:v=x
  active.remove(i);memo[i]=v;return v
 matches=[x for x in data if isinstance(x,dict) and {'venue','homeTeamName','visitingTeamName','gameDate','homeScore','visitingScore','drives'}<=set(x)]
 need(len(matches)==1,'ambiguous_sidearm_boxscore')
 x=matches[0]
 return {k:deref(x[k]) for k in ['venue','homeTeamName','visitingTeamName','gameDate','homeScore','visitingScore','drives']}

def integer(v,lo,hi,label):
 need(not isinstance(v,bool) and re.fullmatch(r'-?\d+',str(v)) is not None,label)
 n=int(v);need(lo<=n<=hi,label);return n

def clock_seconds(v,label,maximum=900):
 m=re.fullmatch(r'(\d{1,2}):(\d{2})',str(v));need(m is not None,label)
 a,b=map(int,m.groups());need(0<=b<60 and 0<=60*a+b<=maximum,label);return 60*a+b

def matching_end_game_panel(root,d,full_names):
 """Return unique explicit PBP evidence, never an inferred result/clock."""
 matches=[]
 for n in root.all('div'):
  if n.attrs.get('data-test-id')!='s-expansion-panel__root':continue
  text=n.text()
  if not re.search(r'End of game,?\s+clock 00:00\.',text,re.I):continue
  starts=re.findall(r'([A-Za-z][A-Za-z .()\-]*?) drive start at (\d{1,2}:\d{2})\.',text)
  starts=[(a.strip(),b) for a,b in starts]
  if len(starts)!=1:continue
  name,clock=starts[0]
  if norm(name) not in {norm(x) for x in full_names} or clock!=d['startTime']:continue
  m=re.search(r'(?<!\d)(\d+) Plays,\s*(-?\d+) Yards,\s*(\d{1,2}:\d{2})',text)
  if not m or (int(m[1]),int(m[2]),m[3])!=(int(d['plays']),int(d['yards']),d['timeOfPosession']):continue
  # Require the final explicit statement after the drive, no later scoring text.
  if not re.search(r'End of game,?\s+clock 00:00\.$',text,re.I):continue
  matches.append(dict(pbp_panel_sha256=sha(text.encode()),pbp_panel_text=text,explicit_end='End of game, clock 00:00.',drive_start=clock))
 unique={x['pbp_panel_sha256']:x for x in matches}
 need(len(unique)==1,'blank_result_without_unique_exact_end_game_PBP')
 return next(iter(unique.values()))

RESULTS={'TD':'TD','FG':'FG','PUNT':'PUNT','DOWNS':'DOWNS','INT':'INT','FUMB':'FUMBLE','FGA':'MISSED FG','SAF':'SF','SAFETY':'SF'}
BOOKKEEPING={'HALF','KO','POSS'}

def parse_official_html(raw,spec,observed_at,source_url=None):
 """Return validated normalized_drives or quarantine; raw is always retained upstream."""
 source_url=source_url or spec['source_url']
 result=dict(game_id=str(spec['game_id']),status='validation_rejected',source_url=source_url,source_family='official_school_drive_chart',source_sha256=sha(raw),source_bytes=len(raw),source_observed_at=observed_at,source_publication_at=None,strict_point_in_time_verified=False,interchangeable_with_espn=False,original_espn_gap_resolved=False,normalized_drives=[],excluded_rows=[],quarantine=[],audit={})
 try:
  need(isinstance(raw,bytes) and raw,'empty_or_nonbyte_document')
  need(source_url==spec['source_url'] or source_url in [x['url'] for x in spec.get('fallbacks',[])],'undeclared_source_url')
  need(spec.get('home_fbs')==1 and spec.get('away_fbs')==1 and spec['home_id']!=spec['away_id'],'not_exact_fbs_vs_fbs')
  dt=datetime.fromisoformat(observed_at.replace('Z','+00:00'));need(dt.tzinfo is not None,'unknown_observation_time')
  tree=Tree();tree.feed(raw.decode('utf-8-sig',errors='strict'));root=tree.root
  if not any(n.attrs.get('id')=='__NUXT_DATA__' for n in root.all('script')):
   from gap_classic import parse_classic_html
   return parse_classic_html(raw,spec,observed_at,source_url)
  b=nuxt_boxscore(root)
  for side,k in [('home','homeTeamName'),('away','visitingTeamName')]:
   need(norm(b[k]) in {norm(x) for x in spec[side+'_aliases']},side+'_team_identity_conflict')
   need(integer(b['homeScore' if side=='home' else 'visitingScore'],0,150,'invalid_score')==spec[side+'_points'],side+'_final_score_conflict')
  date=datetime.strptime(b['gameDate'],'%m/%d/%Y').date().isoformat()
  need(date==spec['expected_local_date'],'game_date_conflict')
  need(b['venue']['date']==b['gameDate'],'venue_date_conflict')
  need(norm(b['venue']['homeName'])==norm(b['homeTeamName']) and norm(b['venue']['visitorName'])==norm(b['visitingTeamName']),'venue_identity_conflict')
  codes={b['venue']['homeId']:spec['home_id'],b['venue']['visitorId']:spec['away_id']};need(len(codes)==2,'ambiguous_team_code')
  # Source table confirms both final scores independently of structured payload.
  score_tables=[];drive_tables=[]
  for i,t in enumerate(root.all('table')):
   rows=table_rows(t)
   if not rows:continue
   head=' '.join(rows[0]).lower()
   if rows[0][0].lower()=='team' and rows[0][-1].lower() in {'total','t'} and len(rows)==3:
    pairs=[]
    for r in rows[1:]:
     if len(r)>=6 and r[-1].isdigit():pairs.append((norm(r[0]),int(r[-1])))
    if set(pairs)=={(norm(b['homeTeamName']),spec['home_points']),(norm(b['visitingTeamName']),spec['away_points'])}:
     for r in rows[1:]:need(all(str(x).isdigit() for x in r[1:]) and sum(int(x) for x in r[1:-1])==int(r[-1]),'rendered_period_score_sum_conflict')
     score_tables.append(i)
   if 'drive started' in head and 'drive ended' in head:
    body=[r for r in rows if len(r)==10 and r[0] in codes]
    if {r[0] for r in body}==set(codes):drive_tables.append((i,body))
  need(score_tables,'missing_matching_rendered_score_table')
  need(drive_tables,'missing_complete_two_team_DOM_drive_table')
  need(all(rows==drive_tables[0][1] for _,rows in drive_tables),'conflicting_rendered_drive_tables')
  table_index,dom=drive_tables[0];drives=b['drives'];need(isinstance(drives,list) and drives,'missing_structured_drives')
  need(len(dom)==len(drives),'DOM_structured_drive_count_conflict')
  expected=[]
  for d in drives:
   expected.append([str(d.get(k,'')) for k in ['team','startQuarter','startSpot','startTime','startHow','endSpot','endTime','endHow']]+[str(d['plays'])+'-'+str(d['yards']),str(d['timeOfPosession'])])
  need(dom==expected,'DOM_structured_drive_value_conflict')
  result['audit']=dict(game_date=date,home_name=b['homeTeamName'],away_name=b['visitingTeamName'],home_id=spec['home_id'],away_id=spec['away_id'],home_points=spec['home_points'],away_points=spec['away_points'],source_start_time=b['venue'].get('startedOn'),canonical_scheduled_kickoff=spec['kickoff'],exact_kickoff_verified=False,identity_basis='exact_home_visitor_names_date_final_scores',rendered_score_tables=score_tables,drive_table_index=table_index,counted_DOM_drive_rows=len(dom),counted_structured_drive_rows=len(drives),DOM_drive_rows_sha256=sha(packed(dom)),raw_drive_rows=dom)
  normalized=[];excluded=[];result['excluded_rows']=excluded;indices=set()
  for j,d in enumerate(drives):
   index=integer(d['driveIndex'],1,200,'invalid_drive_index');need(index not in indices,'duplicate_drive_index');indices.add(index)
   team=d['team'];need(team in codes,'unknown_drive_team')
   need(d.get('vh')==('H' if codes[team]==spec['home_id'] else 'V'),'drive_home_visitor_conflict')
   plays=integer(d['plays'],0,40,'invalid_offensive_play_count');yards=integer(d['yards'],-100,100,'invalid_drive_yards')
   start=integer(d['startQuarter'],1,20,'invalid_start_period');end=integer(d['endQuarter'],0,20,'invalid_end_period');how=d['endHow']
   rawrow=dict(row_number=j+1,drive_index=index,team_id=codes[team],raw=d)
   if plays==0:excluded.append(dict(rawrow,reason='zero_offensive_plays'));continue
   if start>4:
    need(end>=start,'overtime_period_contradiction');excluded.append(dict(rawrow,reason='explicit_overtime'));continue
   if how in BOOKKEEPING:excluded.append(dict(rawrow,reason='explicit_period_or_possession_bookkeeping'));continue
   if not how:
    need(start==4 and end==0 and not d['endTime'] and j==len(drives)-1,'blank_nonterminal_drive_result')
    need(clock_seconds(d['startTime'],'invalid_start_clock')==clock_seconds(d['timeOfPosession'],'invalid_drive_duration'),'end_game_duration_conflict')
    names=spec['home_aliases'] if codes[team]==spec['home_id'] else spec['away_aliases']
    proof=matching_end_game_panel(root,d,names)
    excluded.append(dict(rawrow,reason='explicit_PBP_end_game_bookkeeping',proof=proof));continue
   need(how in RESULTS,'unknown_positive_play_drive_result')
   need(1<=start<=end<=4 and not (start<=2<end),'regulation_period_conflict')
   start_s=clock_seconds(d['startTime'],'invalid_start_clock');end_s=clock_seconds(d['endTime'],'invalid_end_clock');top_s=clock_seconds(d['timeOfPosession'],'invalid_drive_duration',3600)
   need(start_s-end_s+900*(end-start)==top_s,'drive_period_clock_duration_conflict')
   normalized.append(dict(game_id=str(spec['game_id']),drive_id=str(index),season=int(spec['season']),team_id=codes[team],result=RESULTS[how],yards=yards,offensive_plays=plays,start_period=start,end_period=end))
  counts={tid:dict(drives=sum(x['team_id']==tid for x in normalized),plays=sum(x['offensive_plays'] for x in normalized if x['team_id']==tid)) for tid in codes.values()}
  need(all(x['drives']>=4 and x['plays']>=20 for x in counts.values()),'insufficient_two_team_regulation_evidence')
  result.update(status='validated_secondary_source',normalized_drives=normalized,excluded_rows=excluded)
  result['audit'].update(accepted_regulation_drive_rows=len(normalized),excluded_drive_rows=len(excluded),team_evidence=counts,original_source_complete=True)
  result['conservative_available_at']=max(dt,datetime.fromisoformat(spec['kickoff'].replace('Z','+00:00'))+timedelta(hours=24)).isoformat()
 except (ParseRejected,ValueError,KeyError,TypeError,UnicodeError) as e:
  result['quarantine']=[dict(stage='official_HTML_validation',reason=str(e),source_sha256=result['source_sha256'])]
 return result
