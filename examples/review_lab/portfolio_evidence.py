"""Persist an invented paper decision before settlement; keep venue alternatives separate.

This extends decision_replay rather than implementing a second selection rule.
Evidence classes are an interface contract, not an exchange-proof verifier.
A local hash proves byte integrity, not that a file existed at a historical time.
"""
from __future__ import annotations
from dataclasses import dataclass
from decimal import Decimal
import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from .decision_replay import save_ledger, verify_ledger, settle, demonstration as decision_demo


@dataclass(frozen=True)
class Commitment:
    selection_sha256: str
    saved_bytes_sha256: str
    evidence_class: str
    commitment_sha256: str


PRICE_CLASSES = ('UNAVAILABLE', 'DISPLAY_ONLY', 'ARCHIVED_ASK_DEPTH_FEES')


def _commitment_hash(selection, saved_bytes, evidence):
    return hashlib.sha256(json.dumps([selection,saved_bytes,evidence],separators=(',',':')).encode()).hexdigest()


def commit(ledger: dict, path: Path, evidence_class: str) -> Commitment:
    """Persist outcome-free selection. Caller must independently verify evidence."""
    if evidence_class not in PRICE_CLASSES:
        raise ValueError('unsupported evidence class; actual execution is a separate receipt system')
    verify_ledger(ledger)
    save_ledger(ledger, path)
    saved=hashlib.sha256(path.read_bytes()).hexdigest();selection=ledger['selection_sha256']
    return Commitment(selection,saved,evidence_class,_commitment_hash(selection,saved,evidence_class))


def settle_committed(path: Path, commitment: Commitment, unit_payoffs: dict[str, Decimal]) -> dict:
    """Read the already committed selection; outcomes never re-enter selection."""
    if commitment.evidence_class not in PRICE_CLASSES:
        raise ValueError('unsupported price evidence class')
    if commitment.commitment_sha256!=_commitment_hash(commitment.selection_sha256,commitment.saved_bytes_sha256,commitment.evidence_class):
        raise ValueError('evidence commitment changed')
    raw=path.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=commitment.saved_bytes_sha256:
        raise ValueError('saved commitment bytes changed')
    ledger=json.loads(raw);verify_ledger(ledger)
    if ledger['selection_sha256']!=commitment.selection_sha256:
        raise ValueError('selection identity changed')
    result=settle(ledger,unit_payoffs)
    executable=commitment.evidence_class=='ARCHIVED_ASK_DEPTH_FEES'
    return {'selection_sha256':commitment.selection_sha256,'evidence_class':commitment.evidence_class,
            'interpretation':'hypothetical displayed-depth replay; no observed fills',
            'simulated_profit':result['complete_portfolio_profit'] if executable else None,
            'simulated_roi':result['complete_portfolio_roi'] if executable else None,
            'pending':result['pending'],'actual_profit':None,'actual_executed_wagers':False,
            'historical_existence_proved_by_local_hash':False,
            'missing_profit_reason':None if executable and not result['pending'] else
                'PENDING_OUTCOMES' if executable else 'EXECUTABLE_PRICE_EVIDENCE_UNAVAILABLE'}


def compare_venue_alternatives(ledgers: dict[str, dict]) -> dict:
    """Three optional venue scenarios share one capital allocation, not three."""
    if not ledgers:raise ValueError('at least one alternative required')
    identities=[];scenarios=[]
    for name,ledger in sorted(ledgers.items()):
        if not isinstance(name,str) or not name:raise ValueError('named alternative required')
        verify_ledger(ledger);rule=ledger['rule']
        identities.append((rule['league'],rule['season'],rule['week'],Decimal(rule['budget']),tuple(ledger['candidate_ids'])))
        scenarios.append({'scenario':name,'selection_sha256':ledger['selection_sha256'],
                          'budget':rule['budget'],'spent_in_this_alternative':ledger['total_cost'],
                          'cash_in_this_alternative':ledger['unspent_cash']})
    if len(set(identities))!=1:raise ValueError('venue comparisons require the same league week and budget')
    league,season,week,budget,_=identities[0]
    return {'league':league,'season':season,'week':week,'capital_allocated_once':str(budget),
            'scenarios_are_mutually_exclusive':True,'scenario_profits_must_not_be_added':True,
            'alternatives':scenarios}


def demonstration() -> dict:
    # Every event, amount and quote comes from the existing invented fixture.
    ledger=decision_demo()['ledger']
    with TemporaryDirectory() as folder:
        path=Path(folder)/'selection.json'
        commitment=commit(ledger,path,'ARCHIVED_ASK_DEPTH_FEES')
        pending=settle_committed(path,commitment,{})
        result=settle_committed(path,commitment,{'a':Decimal(1)})
        display_path=Path(folder)/'display_selection.json';display_commitment=commit(ledger,display_path,'DISPLAY_ONLY')
        display=settle_committed(display_path,display_commitment,{'a':Decimal(1)})
    return {'invented_only':True,'orders_sent':0,'pending':pending,'hypothetical_result':result,
            'display_price_result':display,'venue_alternatives':compare_venue_alternatives(
                {'venue_a':ledger,'venue_b':ledger,'best_available_venue':ledger})}


if __name__=='__main__':print(json.dumps(demonstration(),indent=2))
