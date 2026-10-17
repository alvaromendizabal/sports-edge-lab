"""Offline synthetic workflow, not a reproduction of private football scores."""
import argparse
import importlib.metadata
import json
from pathlib import Path
from unittest import mock
import numpy as np
import pandas as pd
from common import atomic_json,require
from data import split_rows
from experiments import ARMS,TASKS,columns,prepare
from families import fit_model,predict_model
from fixtures import fixture_data
from metrics import score


def run_demo():
    # The fixture's added QB/efficiency columns are synthetic Gaussian values.
    # They exercise shape/clock/model interfaces, not real football information.
    with mock.patch('socket.socket.connect',side_effect=RuntimeError('Network disabled in public demo')),mock.patch('socket.create_connection',side_effect=RuntimeError('Network disabled in public demo')):
        fixture=fixture_data();frame,audit=prepare(fixture['frame']);rows=[]
        for track,families in ARMS.items():
            for task in TASKS:
                train,test=split_rows(frame,track,task,2021,[2022])
                release=pd.to_datetime(train.kickoff,utc=True).max()+pd.Timedelta(hours=24)
                decision=pd.to_datetime(test.decision_at,utc=True).min()
                require(release<decision,'DATA','Training outcomes overlap evaluation decision')
                require(set(train.game_id).isdisjoint(test.game_id),'DATA','Train/evaluation game overlap')
                for family in families:
                    model=fit_model(train[columns(track)],train[task],task,family,epochs=8 if family=='mlp' else None)
                    predictions=predict_model(model,test[columns(track)])
                    require(np.isfinite(predictions).all(),'MODEL','Nonfinite demo predictions')
                    rows.append(dict(track=track,task=task,family=family,train_rows=len(train),evaluation_rows=len(test),features=len(columns(track)),train_through=2021,evaluation_season=2022,latest_training_label_release=release.isoformat(),first_evaluation_decision=decision.isoformat(),mlp_fixture_epochs=model['fixture_epochs_override'],metrics=score(test[task],predictions,task)))
        return dict(status='PASS',data_kind='entirely_synthetic',actual_football_performance=False,private_aws_workflow_verified=False,provider_calls=0,network_enabled=False,synthetic_fits=len(rows),seed=5801,temporal_audit=audit,results=rows,versions={n:importlib.metadata.version(n) for n in ['numpy','pandas','scikit-learn','scipy','pyarrow','joblib','threadpoolctl']},limitations=['Synthetic added feature columns do not demonstrate real QB or efficiency feature extraction.','MLP smoke fits use eight fixture epochs; the research default is 200.','Historical source publication time remains unknown; no strict historical point-in-time claim.','No model quality, betting edge, profitability, tracking access or private AWS execution claim.'])


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,default=Path('demo_report.json'));args=parser.parse_args()
    result=run_demo();atomic_json(args.output,result)
    print(json.dumps({'status':result['status'],'synthetic_fits':result['synthetic_fits'],'output':str(args.output),'actual_football_performance':False},indent=2))


if __name__=='__main__':main()
