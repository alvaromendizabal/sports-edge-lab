"""Four tiny synthetic state fits. This does not reproduce football performance."""
import argparse
import json
import pathlib
import platform
import socket
from unittest import mock
import numpy as np
import pandas as pd
import scipy
from state_model import fit_predict, distribution_scores, FIXED_CONFIG, METHOD_MEMO
from state_tests import fixture


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=pathlib.Path,required=True)
    args=parser.parse_args()
    runs=[]
    with mock.patch.object(socket,'socket',side_effect=RuntimeError('Network is disabled in the synthetic demo')):
        for track in ['nfl','ncaaf']:
            train,evaluation=fixture(track)
            for arm in ['static','dynamic']:
                predictions,model,diagnostics=fit_predict(train,evaluation,track,arm,through=2023,years=[2023])
                actual=evaluation.set_index('game_id').loc[predictions.game_id]
                assert (pd.to_datetime(predictions.information_upper_bound_at,utc=True)<predictions.decision_at).all()
                assert predictions.game_id.tolist()==evaluation.game_id.tolist()
                runs.append({'track':track,'arm':arm,'training_rows':len(train),'evaluation_rows':len(evaluation),
                    'diagnostics':diagnostics,'distribution_scores':distribution_scores(actual.home_points.to_numpy(),actual.away_points.to_numpy(),predictions),
                    'predictions':json.loads(predictions.to_json(orient='records',date_format='iso'))})
    report={'status':'PASS','data_kind':'entirely_synthetic','synthetic_joint_fits':len(runs),'provider_calls':0,
        'actual_football_performance':False,'private_aws_workflow_verified':False,'v059_owner_run_completed':False,
        'environment':{'python':platform.python_version(),'numpy':np.__version__,'pandas':pd.__version__,'scipy':scipy.__version__},
        'fixed_config':FIXED_CONFIG,'method_note':METHOD_MEMO,'runs':runs,
        'limitations':['Four evaluation games per arm are a software smoke test, not statistical validation.',
                       'No real football data or owner asset pins are included.',
                       'The real V059 plan contains16jointfit attempts; this demonstration does not execute them.',
                       'Historical publication time and future distribution calibration remain unverified.']}
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
    print('PASS: four entirely synthetic joint fits; output='+str(args.output))


if __name__=='__main__':
    main()
