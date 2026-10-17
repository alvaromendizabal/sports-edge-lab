"""Public synthetic identity, provenance and DOM-count tests. Owner-only actual-source fixture tests are intentionally excluded."""
import copy,html,json,unittest
from gap_parser import parse_official_html

SPEC=dict(game_id='401525462',season=2023,home_id='59',away_id='97',home_name='Georgia Tech',away_name='Louisville',home_aliases=['Georgia Tech'],away_aliases=['Louisville'],home_points=34,away_points=39,home_fbs=1,away_fbs=1,kickoff='2023-09-01T23:30:00+00:00',expected_local_date='2023-09-01',source_url='https://gocards.com/sports/football/stats/2023/georgia-tech/boxscore/24318')
OBS='2026-10-17T22:42:26.088489+00:00'

def fixture(mutate=None,dom_mutate=None,panel=''):
 drives=[]
 for i in range(10):
  team='GT' if i%2==0 else 'LOU'
  drives.append(dict(vh='H' if i%2==0 else 'V',team=team,driveIndex=str(i+1),startQuarter=str(1+i//4),endQuarter=str(1+i//4),startSpot=team+'25',startTime='10:00',startHow='KO',endSpot=team+'50',endTime='07:00',endHow='PUNT',plays='5',yards='25',timeOfPosession='03:00'))
 b=dict(venue=dict(date='09/01/2023',homeName='Georgia Tech',visitorName='Louisville',homeId='GT',visitorId='LOU',startedOn='07:37 PM'),homeTeamName='Georgia Tech',visitingTeamName='Louisville',gameDate='09/01/2023',homeScore=34,visitingScore=39,drives=drives)
 if mutate:mutate(b)
 dom=[[str(d[k]) for k in ['team','startQuarter','startSpot','startTime','startHow','endSpot','endTime','endHow']]+[d['plays']+'-'+d['yards'],d['timeOfPosession']] for d in drives]
 if dom_mutate:dom_mutate(dom)
 refs=[]
 def ref(x):
  i=len(refs);refs.append(None)
  if isinstance(x,dict):refs[i]={k:ref(v) for k,v in x.items()}
  elif isinstance(x,list):refs[i]=[ref(v) for v in x]
  else:refs[i]=x
  return i
 ref(b)
 def tr(r):return '<tr>'+''.join('<td>'+html.escape(str(x))+'</td>' for x in r)+'</tr>'
 score='<table>'+tr(['Team','1','2','3','4','Total'])+tr(['Georgia Tech',0,28,0,6,34])+tr(['Louisville',6,7,10,16,39])+'</table>'
 table='<table>'+tr(['Team','Qtr','Drive Started','Drive Ended','Consumed'])+''.join(tr(r) for r in dom)+'</table>'
 return ('<html><script id="__NUXT_DATA__" type="application/json">'+json.dumps(refs)+'</script>'+score+table+panel+'</html>').encode()

def parse(raw,spec=None):return parse_official_html(raw,spec or SPEC,OBS)
def end_mutate(b):
 d=b['drives'][-1];d.update(startQuarter='4',endQuarter='0',startTime='01:05',endTime='',endHow='',plays='2',yards='-2',timeOfPosession='01:05')
END_PANEL='<div data-test-id="s-expansion-panel__root">2 Plays, -2 Yards, 01:05 Louisville drive start at 01:05. Kneel down. End of game, clock 00:00.</div>'

class GapParserTests(unittest.TestCase):
 def test_valid_rendered_crosscheck(self):
  r=parse(fixture());self.assertEqual(r['status'],'validated_secondary_source');self.assertEqual(len(r['normalized_drives']),10);self.assertEqual(r['audit']['counted_DOM_drive_rows'],10)
 def test_home_away_flip_rejected(self):
  r=parse(fixture(lambda b:b.update(homeTeamName='Louisville',visitingTeamName='Georgia Tech')));self.assertEqual(r['quarantine'][0]['reason'],'home_team_identity_conflict')
 def test_score_conflict_rejected(self):self.assertIn('score_conflict',parse(fixture(lambda b:b.update(homeScore=35)))['quarantine'][0]['reason'])
 def test_date_conflict_rejected(self):self.assertEqual(parse(fixture(lambda b:b.update(gameDate='09/02/2023')))['quarantine'][0]['reason'],'game_date_conflict')
 def test_dom_missing_row_rejected(self):self.assertIn('count_conflict',parse(fixture(dom_mutate=lambda d:d.pop()))['quarantine'][0]['reason'])
 def test_dom_yards_conflict_rejected(self):self.assertIn('value_conflict',parse(fixture(dom_mutate=lambda d:d[0].__setitem__(8,'5-26')))['quarantine'][0]['reason'])
 def test_unknown_result_not_guessed(self):self.assertEqual(parse(fixture(lambda b:b['drives'][0].update(endHow='UNKNOWN')))['quarantine'][0]['reason'],'unknown_positive_play_drive_result')
 def test_blank_result_not_guessed(self):self.assertEqual(parse(fixture(end_mutate))['quarantine'][0]['reason'],'blank_result_without_unique_exact_end_game_PBP')
 def test_exact_pbp_end_game_exclusion(self):
  r=parse(fixture(end_mutate,panel=END_PANEL));self.assertEqual(r['status'],'validated_secondary_source');self.assertEqual(len(r['normalized_drives']),9);self.assertEqual(r['excluded_rows'][0]['reason'],'explicit_PBP_end_game_bookkeeping')
 def test_mismatched_pbp_yards_rejected(self):self.assertNotEqual(parse(fixture(end_mutate,panel=END_PANEL.replace('-2 Yards','2 Yards')))['status'],'validated_secondary_source')
 def test_duplicate_drive_index_rejected(self):self.assertEqual(parse(fixture(lambda b:b['drives'][1].update(driveIndex='1')))['quarantine'][0]['reason'],'duplicate_drive_index')
 def test_nonintegral_period_rejected(self):self.assertEqual(parse(fixture(lambda b:b['drives'][0].update(startQuarter='1.5')))['quarantine'][0]['reason'],'invalid_start_period')
 def test_explicit_ot_excluded(self):
  r=parse(fixture(lambda b:b['drives'][-1].update(startQuarter='5',endQuarter='5')));self.assertEqual(r['status'],'validated_secondary_source');self.assertEqual(r['excluded_rows'][0]['reason'],'explicit_overtime')
 def test_ot_contradiction_rejected(self):self.assertEqual(parse(fixture(lambda b:b['drives'][-1].update(startQuarter='5',endQuarter='2')))['quarantine'][0]['reason'],'overtime_period_contradiction')
 def test_source_url_must_be_declared(self):self.assertEqual(parse_official_html(fixture(),SPEC,OBS,'https://other.example/x')['quarantine'][0]['reason'],'undeclared_source_url')
 def test_fcs_scope_rejected(self):
  s=copy.deepcopy(SPEC);s['away_fbs']=0;self.assertEqual(parse(fixture(),s)['quarantine'][0]['reason'],'not_exact_fbs_vs_fbs')
 def test_no_publication_time_invention(self):
  r=parse(fixture());self.assertIsNone(r['source_publication_at']);self.assertFalse(r['strict_point_in_time_verified']);self.assertEqual(r['conservative_available_at'],OBS)
 def test_one_missing_team_evidence_rejected(self):
  r=parse(fixture(lambda b:[b['drives'][i].update(plays='0') for i in [1,3]]));self.assertNotEqual(r['status'],'validated_secondary_source')
 def test_period_clock_contradiction_rejected(self):self.assertEqual(parse(fixture(lambda b:b['drives'][0].update(endQuarter='2')))['quarantine'][0]['reason'],'drive_period_clock_duration_conflict')
 def test_cross_half_drive_rejected(self):self.assertEqual(parse(fixture(lambda b:b['drives'][0].update(startQuarter='2',endQuarter='3')))['quarantine'][0]['reason'],'regulation_period_conflict')

if __name__=='__main__':unittest.main()
