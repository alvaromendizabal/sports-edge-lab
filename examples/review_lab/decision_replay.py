"""Outcome-free paper decisions and separate settlement on invented inputs.

This intentionally generic exercise is not the private football staking policy,
an exchange connector, a fill simulator, or evidence of trading profitability.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_FLOOR
import hashlib
import json
from pathlib import Path


@dataclass(frozen=True)
class Rule:
    league: str
    season: int
    week: int
    frozen_at: datetime
    lock_at: datetime
    budget: Decimal
    maximum_positions: int
    minimum_net_edge: Decimal
    maximum_quote_age: timedelta


@dataclass(frozen=True)
class Candidate:
    event_id: str
    league: str
    season: int
    week: int
    kickoff: datetime
    forecast_at: datetime
    model_available_at: datetime
    features_available_at: datetime
    quote_at: datetime
    unit_payoff_probability: Decimal
    ask: Decimal
    fee_per_contract: Decimal
    displayed_depth: int
    quote_timestamp_verified: bool


def _clock(value):
    if not isinstance(value,datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("timezone-aware clock required")


def _decimal(value):
    if not isinstance(value,Decimal) or not value.is_finite():
        raise ValueError("finite Decimal amount required")


def _canonical(value):
    def encode(x):
        if isinstance(x,datetime): return x.isoformat()
        if isinstance(x,Decimal): return str(x)
        if isinstance(x,timedelta): return x.total_seconds()
        raise TypeError(type(x).__name__)
    return json.dumps(value,default=encode,sort_keys=True,separators=(",",":"),allow_nan=False).encode()


def freeze_decision(rule: Rule, candidates: tuple[Candidate,...], expected_event_ids: frozenset[str], *, decided_at: datetime) -> dict:
    """Freeze a complete native-week universe without accepting any outcomes."""
    for clock in (rule.frozen_at,rule.lock_at,decided_at): _clock(clock)
    for amount in (rule.budget,rule.minimum_net_edge): _decimal(amount)
    if (not rule.league or type(rule.season) is not int or type(rule.week) is not int or rule.week<1
            or not rule.frozen_at<=decided_at<=rule.lock_at or rule.budget < 0 or rule.minimum_net_edge < 0
            or type(rule.maximum_positions) is not int or rule.maximum_positions < 1
            or not isinstance(rule.maximum_quote_age,timedelta) or rule.maximum_quote_age < timedelta(0)):
        raise ValueError("invalid predeclared decision rule")
    ids=[c.event_id for c in candidates]
    if any(not isinstance(x,str) or not x for x in ids) or len(ids)!=len(set(ids)) or set(ids)!=set(expected_event_ids):
        raise ValueError("complete unique candidate universe required")
    accepted=[];rejected=[]
    for c in candidates:
        if type(c.season)is not int or type(c.week)is not int or (c.league,c.season,c.week)!=(rule.league,rule.season,rule.week):
            raise ValueError("native league season and week mismatch")
        for clock in (c.kickoff,c.forecast_at,c.model_available_at,c.features_available_at,c.quote_at): _clock(clock)
        for amount in (c.unit_payoff_probability,c.ask,c.fee_per_contract): _decimal(amount)
        if (not 0<=c.unit_payoff_probability<=1 or not 0<c.ask<1 or c.fee_per_contract<0
                or type(c.displayed_depth) is not int or c.displayed_depth<0):
            raise ValueError("invalid contract probability, cost or depth")
        reasons=[]
        if c.kickoff<=rule.lock_at: reasons.append("KICKOFF_NOT_AFTER_LOCK")
        if max(c.model_available_at,c.features_available_at)>c.forecast_at: reasons.append("UNAVAILABLE_FORECAST_DEPENDENCY")
        if c.forecast_at>decided_at: reasons.append("LATE_FORECAST")
        if c.quote_at>decided_at or decided_at-c.quote_at>rule.maximum_quote_age: reasons.append("QUOTE_NOT_FRESH_AT_DECISION")
        if c.quote_timestamp_verified is not True: reasons.append("UNVERIFIED_QUOTE_TIMESTAMP")
        edge=c.unit_payoff_probability-c.ask-c.fee_per_contract
        if edge<=rule.minimum_net_edge: reasons.append("INSUFFICIENT_DECLARED_EDGE")
        if c.displayed_depth==0: reasons.append("NO_DISPLAYED_DEPTH")
        if reasons: rejected.append({"event_id":c.event_id,"reasons":reasons})
        else: accepted.append((edge,c))
    accepted.sort(key=lambda pair:(-pair[0],pair[1].event_id))
    slot=rule.budget/Decimal(rule.maximum_positions)
    positions=[]
    for edge,c in accepted[:rule.maximum_positions]:
        unit_cost=c.ask+c.fee_per_contract
        count=min(c.displayed_depth,int((slot/unit_cost).to_integral_value(rounding=ROUND_FLOOR)))
        if not count:
            rejected.append({"event_id":c.event_id,"reasons":["SLOT_CANNOT_BUY_ONE_CONTRACT"]});continue
        cost=Decimal(count)*unit_cost
        positions.append({"event_id":c.event_id,"contracts":count,"ask":str(c.ask),
            "fees":str(Decimal(count)*c.fee_per_contract),"total_cost":str(cost),
            "expected_profit":str(Decimal(count)*edge),"observed_fill":False})
    for _,c in accepted[rule.maximum_positions:]: rejected.append({"event_id":c.event_id,"reasons":["POSITION_CAP"]})
    spent=sum((Decimal(p['total_cost'])for p in positions),Decimal(0))
    record={"kind":"PAPER_DISPLAYED_DEPTH_SCENARIO","rule":asdict(rule),"decided_at":decided_at,
            "candidate_ids":sorted(ids),"candidate_evidence_sha256":hashlib.sha256(_canonical([asdict(c)for c in sorted(candidates,key=lambda c:c.event_id)])).hexdigest(),
            "positions":positions,"rejected":sorted(rejected,key=lambda r:r['event_id']),
            "total_cost":str(spent),"unspent_cash":str(rule.budget-spent),"actual_orders":0,
            "outcomes_used_in_selection":False}
    record=json.loads(_canonical(record))
    return {**record,"selection_sha256":hashlib.sha256(_canonical(record)).hexdigest()}


def verify_ledger(ledger:dict) -> None:
    body={k:v for k,v in ledger.items()if k!='selection_sha256'}
    if hashlib.sha256(_canonical(body)).hexdigest()!=ledger.get('selection_sha256'):
        raise ValueError("selection record changed")


def save_ledger(ledger:dict,path:Path) -> None:
    verify_ledger(ledger);raw=_canonical(ledger)+b'\n'
    if path.exists():
        if path.read_bytes()!=raw: raise ValueError("existing selection cannot be overwritten")
        return
    with path.open('xb')as stream:stream.write(raw)


def settle(ledger:dict,unit_payoffs:dict[str,Decimal]) -> dict:
    """Settle verified payoff amounts; unknown outcomes remain pending."""
    verify_ledger(ledger)
    positions=ledger['positions'];ids={p['event_id']for p in positions}
    if set(unit_payoffs)-ids:raise ValueError("settlement contains an unselected event")
    for value in unit_payoffs.values():
        _decimal(value)
        if not 0<=value<=1:raise ValueError("payoff outside explicit unit contract domain")
    settled=[];pending=[]
    for p in positions:
        if p['event_id']not in unit_payoffs:pending.append(p['event_id']);continue
        payout=Decimal(p['contracts'])*unit_payoffs[p['event_id']]
        settled.append({'event_id':p['event_id'],'payout':str(payout),'net_profit':str(payout-Decimal(p['total_cost']))})
    profit=sum((Decimal(p['net_profit'])for p in settled),Decimal(0))
    cost=Decimal(ledger['total_cost'])
    return {'selection_sha256':ledger['selection_sha256'],'settled':settled,'pending':pending,
            'realized_profit_on_settled_positions':str(profit),
            'complete_portfolio_profit':None if pending else str(profit),
            'complete_portfolio_roi':None if pending or cost==0 else str(profit/cost),
            'actual_executed_wagers':False}


def demonstration() -> dict:
    from datetime import timezone
    lock=datetime(2021,10,5,12,tzinfo=timezone.utc)
    rule=Rule('invented',2021,4,lock-timedelta(days=2),lock,Decimal('100'),2,Decimal('0.02'),timedelta(minutes=10))
    def candidate(name,p,depth):return Candidate(name,'invented',2021,4,lock+timedelta(days=1),lock-timedelta(hours=1),
        lock-timedelta(days=3),lock-timedelta(days=2),lock-timedelta(minutes=2),Decimal(p),Decimal('0.50'),Decimal('0.01'),depth,True)
    ledger=freeze_decision(rule,(candidate('a','.60',50),candidate('b','.48',100)),frozenset(('a','b')),decided_at=lock)
    return {'invented_only':True,'ledger':ledger,'partial_settlement':settle(ledger,{}),
            'complete_settlement':settle(ledger,{'a':Decimal(1)})}


if __name__=='__main__':print(json.dumps(demonstration(),indent=2))
