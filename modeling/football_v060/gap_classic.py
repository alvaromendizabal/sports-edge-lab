"""Offline, fail-closed classic Sidearm drive chart parser.

Does not repair source dates, infer drive outcomes or treat downloads as usable.
The official All Drives table is checked against both team-specific tables.
End periods require exact elapsed-clock/TOP arithmetic within one half.
"""
from datetime import datetime,timedelta
import re
try:
 from .gap_parser import (Tree,Node,table_rows,norm,need,integer,RESULTS,
                          BOOKKEEPING,sha,packed,ParseRejected)
except ImportError:
 from gap_parser import (Tree,Node,table_rows,norm,need,integer,RESULTS,
                         BOOKKEEPING,sha,packed,ParseRejected)


def classes(n):
 return set(n.attrs.get('class','').split())

def caption(t):
 values=[n.text() for n in t.all('caption')]
 need(len(values)<=1,'ambiguous_table_caption')
 return values[0] if values else ''

def seconds(value,label):
 m=re.fullmatch(r'(\d{1,2}):(\d{2})',value)
 need(m is not None,label)
 minute,second=int(m[1]),int(m[2]);need(second<60,label)
 return minute*60+second

def regulation_end_period(start,start_time,end_time,top):
 a=seconds(start_time,'invalid_start_clock');b=seconds(end_time,'invalid_end_clock');elapsed=seconds(top,'invalid_TOP')
 need(0<=a<=900 and 0<=b<=900 and 0<=elapsed<=1800,'invalid_regulation_clock_range')
 # A drive cannot span halftime. Solve, do not guess from clock ordering.
 half_end=2 if start<=2 else 4
 valid=[q for q in range(start,half_end+1) if (q-start)*900+a-b==elapsed]
 need(len(valid)==1,'drive_clock_TOP_period_conflict')
 return valid[0]

def period(value):
 if value in {'1st','2nd','3rd','4th'}:return int(value[0])
 if value=='OT':return 5
 m=re.fullmatch(r'(\d+)(?:OT|ot)',value)
 if m:return 4+integer(m[1],1,16,'invalid_overtime_period')
 raise ParseRejected('unknown_period_label')

def body_rows(t):
 rows=table_rows(t)
 need(len(rows)>=3,'missing_drive_table_body')
 need('Drive Started' in rows[0] and 'Drive Ended' in rows[0] and rows[1]==['Spot','Time','Obtained','Spot','Time','How Lost','Plays-Yds.','TOP'],'drive_table_header_conflict')
 body=[]
 for row in rows[2:]:
  need(len(row)==11,'malformed_classic_drive_row')
  need(row[0]==row[2]+'/'+row[4],'mobile_drive_row_conflict')
  body.append(row[1:])
 return body

def parse_classic_html(raw,spec,observed_at,source_url=None):
 source_url=source_url or spec['source_url']
 result=dict(game_id=str(spec['game_id']),status='validation_rejected',source_url=source_url,
  source_family='official_school_drive_chart',source_sha256=sha(raw),source_bytes=len(raw),
  source_observed_at=observed_at,source_publication_at=None,strict_point_in_time_verified=False,
  interchangeable_with_espn=False,original_espn_gap_resolved=False,
  normalized_drives=[],excluded_rows=[],quarantine=[],audit={})
 try:
  need(isinstance(raw,bytes) and raw,'empty_or_nonbyte_document')
  need(source_url==spec['source_url'] or source_url in [x['url'] for x in spec.get('fallbacks',[])],'undeclared_source_url')
  need(spec.get('home_fbs')==1 and spec.get('away_fbs')==1 and spec['home_id']!=spec['away_id'],'not_exact_fbs_vs_fbs')
  observed=datetime.fromisoformat(observed_at.replace('Z','+00:00'));need(observed.tzinfo is not None,'unknown_observation_time')
  tr=Tree();tr.feed(raw.decode('utf-8-sig',errors='strict'));root=tr.root
  need(not any(n.attrs.get('id')=='__NUXT_DATA__' for n in root.all('script')),'classic_parser_received_nuxt')
  names={};team_panels={}
  for side,panel_side in [('home','home'),('away','away')]:
   panels=[n for n in root.all('div') if {'team',panel_side}<=classes(n)]
   need(len(panels)==1,'ambiguous_'+side+'_team_panel');panel=panels[0]
   logos=[n.attrs.get('alt','') for n in panel.all('img')]
   need(len(logos)==1 and logos[0].endswith(' logo'),'missing_'+side+'_identity_logo')
   name=logos[0][:-5];need(norm(name) in {norm(x) for x in spec[side+'_aliases']},side+'_team_identity_conflict')
   score=[n.text() for n in panel.all('span') if 'score' in classes(n)]
   need(len(score)==1,'ambiguous_'+side+'_score')
   need(integer(score[0],0,150,'invalid_score')==spec[side+'_points'],side+'_final_score_conflict')
   names[side]=name;team_panels[side]=sha(panel.text().encode())
  game_details=[]
  for dl in root.all('dl'):
   children=[n for n in dl.children if isinstance(n,Node)]
   if not any(n.tag=='dt' and n.text()=='Date:' for n in children):continue
   need(len(children)%2==0,'malformed_game_information')
   pairs=[]
   for i in range(0,len(children),2):
    need(children[i].tag=='dt' and children[i+1].tag=='dd','malformed_game_information')
    pairs.append((children[i].text().rstrip(':'),children[i+1].text()))
   need(len(dict(pairs))==len(pairs),'duplicate_game_information_key');game_details.append(dict(pairs))
  need(len(game_details)==1,'ambiguous_game_information');info=game_details[0]
  date=datetime.strptime(info['Date'],'%m/%d/%Y').date().isoformat()
  need(date==spec['expected_local_date'],'game_date_conflict')
  tables=list(root.all('table'));scores=[(i,t) for i,t in enumerate(tables) if caption(t)=='Team Score By Quarter']
  need(len(scores)==1,'ambiguous_or_missing_score_table');score_i,score_table=scores[0]
  score_rows=list(score_table.all('tr'));need(len(score_rows)==3,'incomplete_score_table')
  codes={};seen_sides=set();score_audit=[]
  for row in score_rows[1:]:
   cells=[n for n in row.children if isinstance(n,Node) and n.tag in {'td','th'}]
   need(len(cells)>=6,'malformed_score_row')
   full=[n.text() for n in cells[0].all('span') if 'hide-on-small-down' in classes(n)]
   short=[n.text() for n in cells[0].all('span') if 'hide-on-medium' in classes(n)]
   need(len(full)==len(short)==1,'missing_score_team_identity')
   matches=[side for side in ('home','away') if norm(full[0])==norm(names[side])]
   need(len(matches)==1,'score_team_identity_conflict');side=matches[0]
   need(side not in seen_sides and short[0] not in codes,'duplicate_score_team');seen_sides.add(side)
   values=[integer(n.text(),0,150,'invalid_period_score') for n in cells[1:]]
   need(values[-1]==spec[side+'_points'] and sum(values[:-1])==values[-1],'score_sum_or_final_conflict')
   codes[short[0]]=spec[side+'_id'];score_audit.append(dict(side=side,name=full[0],code=short[0],scores=values))
  need(seen_sides=={'home','away'},'incomplete_score_identities')
  all_tables=[(i,t)for i,t in enumerate(tables) if caption(t)=='All Drives']
  need(len(all_tables)==1,'ambiguous_or_missing_All_Drives_table');drive_i,drive_table=all_tables[0];dom=body_rows(drive_table)
  need(dom and {row[0] for row in dom}==set(codes),'incomplete_two_team_drive_table')
  team_indices=[];caption_warnings=[]
  for side in ('home','away'):
   section_id=('home' if side=='home' else 'visitor')+'-drives'
   sections=[n for n in root.all('section') if n.attrs.get('id')==section_id]
   need(len(sections)==1,'ambiguous_or_missing_'+side+'_drives_section')
   section=sections[0];need(section.attrs.get('aria-label')==names[side]+' Drives','team_drive_section_identity_conflict')
   candidates=list(section.all('table'));need(len(candidates)==1,'ambiguous_or_missing_'+side+'_drives_table')
   t=candidates[0];i=next(i for i,x in enumerate(tables) if x is t);team_indices.append(i)
   if caption(t)!=names[side]+' Drives':caption_warnings.append(dict(table_index=i,raw_caption=caption(t),verified_section_id=section_id,verified_aria_label=section.attrs.get('aria-label'),identity_basis='explicit_section_and_all_row_codes'))
   team_body=body_rows(t);expected=[r for r in dom if codes[r[0]]==spec[side+'_id']]
   need(team_body==expected,'All_Drives_team_table_value_conflict')
  need(len({packed(r)for r in dom})==len(dom),'duplicate_drive_row')
  result['audit']=dict(parser='classic_sidearm_v060',game_date=date,home_name=names['home'],away_name=names['away'],home_id=spec['home_id'],away_id=spec['away_id'],home_points=spec['home_points'],away_points=spec['away_points'],source_start_time=info.get('Kickoff Time'),canonical_scheduled_kickoff=spec['kickoff'],exact_kickoff_verified=False,identity_basis='explicit_home_away_panels_exact_names_date_final_scores',rendered_score_tables=[score_i],score_rows=score_audit,drive_table_index=drive_i,team_drive_table_indices=team_indices,counted_DOM_drive_rows=len(dom),counted_structured_drive_rows=None,DOM_drive_rows_sha256=sha(packed(dom)),raw_drive_rows=dom,home_away_panel_hashes=team_panels,source_caption_inconsistencies=caption_warnings,end_period_basis='exact_start_clock_end_clock_TOP_within_same_half')
  normalized=[];excluded=[];result['excluded_rows']=excluded
  for j,row in enumerate(dom):
   team,start_label,start_spot,start_clock,start_how,end_spot,end_clock,how,plays_yards,top=row
   need(team in codes,'unknown_drive_team');start=period(start_label)
   m=re.fullmatch(r'(\d+)-(?:\((-?\d+)\)|(-?\d+))',plays_yards)
   need(m is not None,'invalid_drive_plays_yards');plays=integer(m[1],0,40,'invalid_offensive_play_count');yards=integer(m[2] if m[2] is not None else m[3],-100,100,'invalid_drive_yards')
   rawrow=dict(row_number=j+1,drive_index=j+1,team_id=codes[team],raw=row)
   if start>4:
    excluded.append(dict(rawrow,reason='explicit_overtime'));continue
   if plays==0:excluded.append(dict(rawrow,reason='zero_offensive_plays'));continue
   need(how in RESULTS or how in BOOKKEEPING,'unknown_positive_play_drive_result')
   end=regulation_end_period(start,start_clock,end_clock,top)
   if how in BOOKKEEPING:
    if how=='HALF':need(end in {2,4} and end_clock=='00:00','period_bookkeeping_clock_conflict')
    excluded.append(dict(rawrow,reason='explicit_period_or_possession_bookkeeping'));continue
   normalized.append(dict(game_id=str(spec['game_id']),drive_id=str(j+1),season=int(spec['season']),team_id=codes[team],result=RESULTS[how],yards=yards,offensive_plays=plays,start_period=start,end_period=end))
  counts={tid:dict(drives=sum(x['team_id']==tid for x in normalized),plays=sum(x['offensive_plays']for x in normalized if x['team_id']==tid))for tid in codes.values()}
  need(all(x['drives']>=4 and x['plays']>=20 for x in counts.values()),'insufficient_two_team_regulation_evidence')
  result.update(status='validated_secondary_source',normalized_drives=normalized,excluded_rows=excluded)
  result['audit'].update(accepted_regulation_drive_rows=len(normalized),excluded_drive_rows=len(excluded),team_evidence=counts,original_source_complete=True)
  result['conservative_available_at']=max(observed,datetime.fromisoformat(spec['kickoff'].replace('Z','+00:00'))+timedelta(hours=24)).isoformat()
 except (ParseRejected,ValueError,KeyError,TypeError,UnicodeError) as e:
  result['quarantine']=[dict(stage='official_classic_HTML_validation',reason=str(e),source_sha256=result['source_sha256'])]
 return result
