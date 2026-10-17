"""Exact-identity secondary-source recovery; never overwrite accepted ESPN features."""
import collections,re,unicodedata
import numpy as np
import pandas as pd
from common import GateError,require
from efficiency import aggregate,METRICS,COLLEGE_COLUMNS

# Explicit spelling pairs observed in the pinned NCAA team table and canonical
# same-game schedules. Every use still requires reciprocal IDs, scores and date.
NAME_ALIASES={
 'Army West Point':'Army','N.C. A&T':'North Carolina A&T','Fla. Atlantic':'Florida Atlantic',
 'South Fla.':'South Florida','Southeastern La.':'SE Louisiana','ETSU':'East Tennessee State',
 'Middle Tenn.':'Middle Tennessee','N.C. Central':'North Carolina Central','FIU':'Florida International',
 'Western Ky.':'Western Kentucky','NIU':'Northern Illinois','Central Conn. St.':'Central Connecticut',
 'Miami (FL)':'Miami','SFA':'Stephen F. Austin','LIU':'Long Island University',
 'Eastern Mich.':'Eastern Michigan','Ga. Southern':'Georgia Southern','ULM':'UL Monroe',
 'Southern California':'USC','Eastern Wash.':'Eastern Washington','Northern Ariz.':'Northern Arizona',
 'Lamar University':'Lamar','Central Mich.':'Central Michigan','Western Mich.':'Western Michigan'}

def basic_name(v):
 s=unicodedata.normalize('NFKD',str(v));s=''.join(c for c in s if not unicodedata.combining(c))
 return re.sub('[^a-z0-9]','',re.sub(r'\bst\.?\b','state',s.lower()))
ALIASES={basic_name(k):basic_name(v) for k,v in NAME_ALIASES.items()}
def norm(v):return ALIASES.get(basic_name(v),basic_name(v))
def ident(v):
 if isinstance(v,(bool,np.bool_)):return ''
 s=str(v)
 if re.fullmatch(r'[1-9][0-9]*(?:\.0+)?',s):return s.split('.')[0]
 return ''
def clean(v):
 if isinstance(v,dict):return {str(k):clean(x) for k,x in v.items()}
 if isinstance(v,(list,tuple)):return [clean(x) for x in v]
 if isinstance(v,np.generic):return clean(v.item())
 if isinstance(v,pd.Timestamp):return v.isoformat()
 if isinstance(v,float) and not np.isfinite(v):return None
 return v

def canonical_check(games):
 required={'track','game_id','home_id','away_id','home_name','away_name','home_points','away_points','season','kickoff','completed'}
 require(required<=set(games),'SCHEMA','Canonical game columns missing')
 require(not games.duplicated(['track','game_id']).any(),'DATA','Conflicting canonical games')

def identity_links(drives,schedule,teams,games,season,source):
 canonical_check(games)
 required={'contest_id','espn_game_id','season','team','drive_number','start_period','end_period','end_how','n_plays','yards'}
 require(required<=set(drives),'SCHEMA','NCAA drive columns missing')
 require({'contest_id','team_id','opponent_id','team_score','opponent_score','date','season'}<=set(schedule),'SCHEMA','NCAA schedule columns missing')
 require({'team_id','team_name','season'}<=set(teams),'SCHEMA','NCAA team columns missing')
 t=teams[['team_id','team_name','season']].drop_duplicates().copy();t['team_id']=t.team_id.map(ident)
 require((pd.to_numeric(t.season,errors='coerce')==season).all() and t.team_id.ne('').all() and not t.team_id.duplicated().any(),'DATA','NCAA team ID/season conflict')
 names=t.set_index('team_id').team_name.to_dict()
 g=games[(games.track=='ncaaf')&(games.season==season)&games.completed].copy();canon={r.game_id:r for r in g.itertuples()}
 raw=drives.copy();raw['_gid']=raw.espn_game_id.map(ident);raw['_contest']=raw.contest_id.map(ident)
 collisions=set(raw.groupby('_contest')._gid.nunique().loc[lambda x:x>1].index)
 sg={str(c):z for c,z in schedule.groupby(schedule.contest_id.map(ident))};links=[];bad=[]
 for gid,d in raw.groupby('_gid',sort=True):
  if gid not in canon:continue
  r=canon[gid]
  try:
   contests=set(d._contest);require(len(contests)==1 and '' not in contests,'DATA','ambiguous_contest_id');contest=next(iter(contests))
   require(contest not in collisions,'DATA','contest_maps_to_multiple_games')
   require((pd.to_numeric(d.season,errors='coerce')==season).all(),'DATA','drive_season_mismatch')
   require(contest in sg,'DATA','missing_schedule_contest')
   s=sg[contest].drop_duplicates().copy()
   # Exact duplicates may differ in display-only attendance, but required fields
   # must agree. Contradictory scores/dates or IDs remain separate and fail.
   cols=['team_id','opponent_id','team_score','opponent_score','date','season']+(['espn_game_id'] if 'espn_game_id' in s else [])
   s=s[cols].drop_duplicates();require(len(s)==2,'DATA','schedule_requires_two_reciprocal_rows')
   mapids={};short={};pairs={};records=[]
   for x in s.to_dict('records'):
    tid,oid=ident(x['team_id']),ident(x['opponent_id']);require(tid in names and oid in names and tid!=oid,'DATA','unknown_ncaa_team_id')
    require(x['season']==season,'DATA','schedule_season_mismatch')
    if 'espn_game_id' in x and ident(x['espn_game_id']):require(ident(x['espn_game_id'])==gid,'DATA','schedule_espn_id_conflict')
    matched=[(r.home_id,r.home_points,r.away_points),(r.away_id,r.away_points,r.home_points)]
    matched=[z for z in matched if norm(names[tid])==norm(r.home_name if z[0]==r.home_id else r.away_name)]
    require(len(matched)==1,'DATA','unresolved_team_name_identity')
    cid,points,opp=matched[0]
    require(pd.notna(x['team_score']) and pd.notna(x['opponent_score']) and (float(x['team_score']),float(x['opponent_score']))==(float(points),float(opp)),'DATA','score_conflict')
    date=pd.to_datetime(x['date'],format='%m/%d/%Y',errors='coerce');kick=pd.Timestamp(r.kickoff)
    require(kick.tzinfo is not None and not pd.isna(date) and date.date() in {kick.date(),kick.tz_convert('America/New_York').date()},'DATA','schedule_date_conflict')
    require(tid not in mapids,'DATA','duplicate_ncaa_team')
    mapids[tid]=cid;short[tid]=names[tid];pairs[tid]=oid;records.append(x)
   require(set(mapids.values())=={r.home_id,r.away_id} and all(pairs.get(pairs[k])==k for k in pairs),'DATA','nonreciprocal_team_ids')
   for rawname in d.team.dropna().unique():require(norm(rawname) in {norm(x) for x in short.values()},'DATA','drive_team_not_in_schedule')
   links.append(dict(game_id=gid,contest_id=contest,season=season,ncaa_to_canonical=mapids,ncaa_names=short,home_id=r.home_id,away_id=r.away_id,kickoff=r.kickoff,raw_rows=len(d),source=source,source_publication_at=None,strict_point_in_time_verified=False))
  except GateError as e:bad.append(dict(game_id=gid,season=season,reason=str(e),stage='identity',raw_rows=len(d)))
 return clean(links),bad

RESULTS={'TD':'TD','FG':'FG','PUNT':'PUNT','DOWNS':'DOWNS','INT':'INT','FUMB':'FUMBLE','FGA':'MISSED FG','SAF':'SF','SAFETY':'SF','HALF':'END OF HALF','KO':'KICKOFF','POSS':'POSSESSION (FOR OT DRIVES)'}
EXCLUDED={'HALF','KO','POSS'}

def normalize_drives(raw,links,games,source):
 canonical_check(games);r=raw.copy();r['_gid']=r.espn_game_id.map(ident);r['_contest']=r.contest_id.map(ident)
 grouped={k:g for k,g in r.groupby('_gid')};eligible_all=[];quarantine=[];excluded=collections.Counter();proof=[];eligible_links={}
 for link in links:
  gid=link['game_id'];d=grouped[gid];rows=[]
  try:
   cols=['contest_id','drive_number','season','team','start_period','end_period','end_how','n_plays','yards','espn_game_id']
   d=d[cols].drop_duplicates();require(not d.drive_number.duplicated().any(),'DATA','conflicting_drive_number')
   names={norm(name):link['ncaa_to_canonical'][tid] for tid,name in link['ncaa_names'].items()};require(len(names)==2,'DATA','ambiguous_drive_team_names')
   for x in d.to_dict('records'):
    require(ident(x['contest_id'])==link['contest_id'] and x['season']==link['season'],'DATA','drive_context_conflict')
    number=ident(x['drive_number']);require(bool(number),'DATA','invalid_drive_number')
    n,y=pd.to_numeric(x['n_plays'],errors='coerce'),pd.to_numeric(x['yards'],errors='coerce')
    require(pd.notna(n) and np.isfinite(n) and n==int(n) and 0<=n<=40,'DATA','invalid_drive_plays')
    if n==0:excluded['zero_offensive_plays']+=1;continue
    result=x['end_how'];require(result in RESULTS,'DATA','unknown_positive_play_drive_result')
    if result in EXCLUDED:excluded['period_or_possession_bookkeeping']+=1;continue
    start,end=pd.to_numeric(x['start_period'],errors='coerce'),pd.to_numeric(x['end_period'],errors='coerce')
    require(pd.notna(start) and pd.notna(end) and np.isfinite(start) and np.isfinite(end) and start==int(start) and end==int(end) and 1<=start<=end<=20,'DATA','invalid_drive_period')
    if start>4 or end>4:excluded['overtime_or_crossing_overtime']+=1;continue
    require(pd.notna(y) and np.isfinite(y) and y==int(y) and -100<=y<=100,'DATA','invalid_drive_yards')
    team=names.get(norm(x['team']));require(team is not None,'DATA','drive_team_identity')
    rows.append(dict(game_id=gid,drive_id=number,season=link['season'],team_id=team,result=RESULTS[result],yards=y,offensive_plays=n,start_period=start,end_period=end))
   require(bool(rows),'DATA','no_eligible_regulation_drives')
   eligible_all.extend(rows);eligible_links[gid]=link
   proof.append(dict(game_id=gid,season=link['season'],accepted_drive_rows=len(rows),source=source))
  except GateError as e:quarantine.append(dict(game_id=gid,season=link['season'],reason=str(e),stage='normalization',raw_rows=len(d)))
 cols=['track','game_id','team_id','opponent_id',*METRICS['ncaaf'],'source_family','source_observed_at','source_publication_at','conservative_available_at','strict_point_in_time_verified','interchangeable_with_espn','source_key','source_sha256']
 if eligible_all:
  out,a,unexpected=aggregate(pd.DataFrame(eligible_all,columns=COLLEGE_COLUMNS),'ncaaf',games,source['key'])
  require(not unexpected,'DATA','Prevalidated NCAA rows failed the unchanged aggregation gate')
  accepted=set(out.game_id)
  for gid,link in eligible_links.items():
   if gid not in accepted:quarantine.append(dict(game_id=gid,season=link['season'],reason='insufficient_two_team_evidence',stage='normalization',raw_rows=link['raw_rows']))
  out['source_family']='ncaa_drive_summary';out['source_observed_at']=source['observed_at'];out['source_publication_at']=None
  observed=pd.Timestamp(source['observed_at']);require(observed.tzinfo is not None,'SOURCE_STATE','Unknown observation time')
  out['conservative_available_at']=out.game_id.map(lambda gid:max(observed,pd.Timestamp(eligible_links[gid]['kickoff'])+pd.Timedelta(hours=24)).isoformat())
  out['strict_point_in_time_verified']=False;out['interchangeable_with_espn']=False;out['source_key']=source['key'];out['source_sha256']=source['sha256']
  proof=[dict(x,accepted_team_rows=2) for x in proof if x['game_id'] in accepted]
 else:out=pd.DataFrame(columns=cols)

 return out,quarantine,dict(accepted_games=out.game_id.nunique(),accepted_team_rows=len(out),quarantined_games=len(quarantine),excluded_rows=dict(excluded)),clean(proof)

def concordance(secondary,baseline):
 require(not secondary.duplicated(['track','game_id','team_id']).any() and not baseline.duplicated(['track','game_id','team_id']).any(),'DATA','Duplicate efficiency identity')
 metrics=list(METRICS['ncaaf']);m=secondary.merge(baseline[baseline.track=='ncaaf'],on=['track','game_id','team_id','opponent_id'],suffixes=('_ncaa','_espn'),validate='one_to_one');rows=[];all_exact=np.ones(len(m),dtype=bool)
 for k in metrics:
  delta=m[k+'_ncaa'].to_numpy(float)-m[k+'_espn'].to_numpy(float);require(np.isfinite(delta).all(),'DATA','Nonfinite source comparison');exact=np.isclose(delta,0,rtol=0,atol=1e-10);all_exact &=exact
  rows.append(dict(metric=k,team_games=len(m),exact_matches=int(exact.sum()),mean_difference=float(delta.mean()) if len(delta) else None,median_absolute_difference=float(np.median(abs(delta))) if len(delta) else None,p95_absolute_difference=float(np.quantile(abs(delta),.95)) if len(delta) else None,max_absolute_difference=float(abs(delta).max()) if len(delta) else None))
 return clean(dict(overlap_team_games=len(m),overlap_games=m.game_id.nunique(),all_metrics_exact_team_games=int(all_exact.sum()),all_metrics_exact_fraction=float(all_exact.mean()) if len(m) else None,metrics=rows,interchangeability_approved=False,baseline_replacement_permitted=False,decision='Keep secondary-source provenance and missingness explicit; require a controlled modeling ablation before use. Differences do not establish which provider is correct.'))

def resolve_queue(queue,secondary,identity_bad,drive_bad,games,baseline):
 require(len(queue)==len({str(r['game_id']) for r in queue}),'DATA','Duplicate recovery queue ID');canonical_check(games)
 require(not baseline.duplicated(['track','game_id','team_id']).any(),'DATA','Duplicate frozen baseline')
 canon=games[games.track=='ncaaf'].set_index('game_id');oldids=set(baseline[baseline.track=='ncaaf'].game_id);selected={str(r['game_id']) for r in queue}
 for r in queue:
  gid=str(r['game_id']);require(gid in canon.index and gid not in oldids,'DATA','Queue no longer represents a missing canonical game');g=canon.loc[gid]
  require(g.completed and (r['home_id'],r['away_id'],r['season'])==(g.home_id,g.away_id,g.season),'DATA','Queue/canonical context conflict')
 additions=secondary[secondary.game_id.isin(selected)].copy();require(not additions.duplicated(['game_id','team_id']).any(),'DATA','Duplicate recovery row')
 got=set(additions.game_id);bad={r['game_id']:r for r in identity_bad+drive_bad};ledger=[]
 for r in queue:
  gid=str(r['game_id']);status='validated_secondary_source' if gid in got else 'current_source_update_needed' if r['season']==2026 else 'source_validation_rejected' if gid in bad else 'absent_from_alternate_archive'
  ledger.append(dict(**r,recovery_status=status,secondary_source_covered=gid in got,recovery_reason=None if gid in got else bad.get(gid,{}).get('reason',status),original_espn_gap_resolved=False,baseline_replaced=False))
 return additions,ledger,dict(selected_games=len(queue),secondary_recovered_games=len(got),remaining_without_valid_secondary=len(selected-got),original_espn_gap_games=len(queue),baseline_rows_preserved=len(baseline),by_status=dict(collections.Counter(r['recovery_status'] for r in ledger)),model_fits=0,provider_calls=0)
