"""Public paired evaluation on invented or caller-supplied declared rows.

This is an evaluation implementation, not the private model recipe. It does
not authenticate source clocks, select a model or establish trading profit.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import random

try:
    from .uniform_comparison import compare_fixed_cohort, cohort_digest
except ImportError:  # Direct one-command use from any working directory.
    from uniform_comparison import compare_fixed_cohort, cohort_digest


def _number(value):
    try:
        finite = type(value) in (float, int) and math.isfinite(value)
    except OverflowError:
        finite = False
    if not finite:
        raise ValueError("Finite numeric values are required")
    return float(value)


def _matched_rows(result, *, complete=False):
    """Check the public comparison's fixed-cohort accounting before aggregating."""
    if not isinstance(result, dict):
        raise ValueError("An explicit comparison object is required")
    fixed_n = result.get("fixed_n")
    ledger = result.get("ledger")
    if type(fixed_n) is not int or fixed_n <= 0 or not isinstance(ledger, list):
        raise ValueError("A nonempty fixed cohort and explicit ledger are required")
    if any(not isinstance(r, dict) for r in ledger):
        raise ValueError("Ledger rows must be explicit observation objects")
    ids = [r.get("game_id") for r in ledger]
    if (any(not isinstance(g, str) or not g.strip() for g in ids)
            or len(ids) != len(set(ids))):
        raise ValueError("Ledger event identities must be unique and nonempty")
    fixed = [r for r in ledger if r.get("in_fixed_cohort") is True]
    if len(fixed) != fixed_n or cohort_digest(r["game_id"] for r in fixed) != result.get("fixed_cohort_sha256"):
        raise ValueError("Ledger membership differs from the declared fixed cohort")
    rows = sorted((r for r in ledger if r.get("state") == "MATCHED"), key=lambda r:r["game_id"])
    if any(r.get("in_fixed_cohort") is not True for r in rows):
        raise ValueError("An outside-cohort row cannot be matched")
    full = len(rows) == fixed_n
    expected = "COMPLETE_FIXED_COHORT" if full else "INCOMPLETE_FIXED_COHORT"
    if (result.get("headline_state") != expected or type(result.get("matched_n")) is not int
            or result["matched_n"] != len(rows)):
        raise ValueError("Comparison coverage counts or headline state are inconsistent")
    if complete and not full:
        raise ValueError("Do not silently bootstrap a shrunken provider subset")
    return rows


def calibration(rows, field, bins=10):
    """Equal-width home-win bins; no fitted calibration or threshold selection."""
    if type(bins) is not int or not 2 <= bins <= 100:
        raise ValueError("Use a declared bin count between 2 and 100")
    rows = list(rows)
    groups = [[] for _ in range(bins)]
    for row in rows:
        p, y = _number(row[field]), _number(row["actual"])
        if not 0 <= p <= 1 or y not in (0, 1):
            raise ValueError("Calibration requires probabilities and non-tied binary labels")
        groups[min(bins - 1, int(p * bins))].append((p, y))
    output = []
    for index, values in enumerate(groups):
        n = len(values)
        mean = sum(p for p, _ in values) / n if n else None
        rate = sum(y for _, y in values) / n if n else None
        output.append(dict(bin=index, lower=index/bins, upper=(index+1)/bins,
                           upper_inclusive=index == bins-1, n=n,
                           mean_home_probability=mean, observed_home_win_rate=rate))
    ece = (sum(r["n"] * abs(r["mean_home_probability"]-r["observed_home_win_rate"])
               for r in output if r["n"]) / len(rows)) if rows else None
    return {"bins": output, "ece": ece, "n": len(rows),
            "qualification": "Descriptive binning; small-bin rates are uncertain; no calibration fitted"}


def _scores(rows, target, field):
    if not rows:
        raise ValueError("A nonempty matched cohort is required")
    actual = [_number(r["actual"]) for r in rows]
    prediction = [_number(r[field]) for r in rows]
    n = len(rows)
    if target == "winner":
        if any(y not in (0, 1) for y in actual) or any(not 0 <= p <= 1 for p in prediction):
            raise ValueError("Winner scores require binary labels and probabilities")
        clipped = [max(1e-15, min(1-1e-15, p)) for p in prediction]
        return dict(log_loss=math.fsum(-y*math.log(p)-(1-y)*math.log1p(-p)
                                 for y,p in zip(actual,clipped))/n,
                    brier=math.fsum((y-p)**2 for y,p in zip(actual,prediction))/n,
                    accuracy=sum((p >= .5) == bool(y) for y,p in zip(actual,prediction))/n)
    if target not in {"margin", "total"}:
        raise ValueError("Unsupported target")
    if target == "total" and (any(y < 0 for y in actual) or any(p < 0 for p in prediction)):
        raise ValueError("Point totals cannot be negative")
    errors = [p-y for y,p in zip(actual,prediction)]
    if any(not math.isfinite(e) for e in errors):
        raise ValueError("Point errors must remain finite")
    return dict(mae=math.fsum(abs(e)/n for e in errors),
                rmse=math.hypot(*(e/math.sqrt(n) for e in errors)),
                bias=math.fsum(e/n for e in errors))


def _advantage(rows, target):
    model, reference = (_scores(rows,target,field) for field in ("model", "reference"))
    # Positive always favors the model. Signed bias itself has no better direction.
    names = ("log_loss", "brier", "accuracy") if target == "winner" else ("mae", "rmse")
    return {k: model[k]-reference[k] if k == "accuracy" else reference[k]-model[k]
            for k in names}


def paired_week_bootstrap(result, cluster_keys, *, seed=2024, resamples=2000):
    """Resample whole declared season/week clusters, keeping both forecasts paired.

    Cluster keys must explicitly cover the fixed matched cohort. These are
    percentile Monte Carlo intervals, not an exhaustive permutation calculation
    or a correction for choosing a hindsight winner among many candidates.
    Inference is conditional on these fixed predictions, events and declared
    clusters. It does not refit models or propagate source, fitting or selection
    uncertainty; resampling weeks assumes exchangeable clusters and cannot
    preserve dependence between successive weeks. Cluster labels are caller
    declarations, not independently authenticated schedule metadata.
    """
    if type(seed) is not int or type(resamples) is not int or not 100 <= resamples <= 100_000:
        raise ValueError("Declare an integer seed and 100–100000 resamples")
    rows = _matched_rows(result, complete=True)
    ids = [r["game_id"] for r in rows]
    if (not isinstance(cluster_keys, dict) or not rows or set(cluster_keys) != set(ids)
            or any(not isinstance(v,str) or not v.strip() for v in cluster_keys.values())):
        raise ValueError("Exact event-to-season/week cluster mapping required")
    if cohort_digest(ids) != result["fixed_cohort_sha256"]:
        raise ValueError("Matched event identities differ from the fixed cohort")
    target = result["target"]
    groups = {}
    for row in sorted(rows,key=lambda r:r["game_id"]):
        groups.setdefault(cluster_keys[row["game_id"]],[]).append(row)
    clusters = sorted(groups)
    if len(clusters) < 2:
        raise ValueError("At least two distinct season/week clusters are required")
    rng = random.Random(seed)
    observed = _advantage(rows,target)
    samples = {key: [] for key in observed}
    for _ in range(resamples):
        sampled = [row for _ in clusters for row in groups[rng.choice(clusters)]]
        for key, value in _advantage(sampled,target).items():
            samples[key].append(value)
    def quantile(values,q):
        ordered = sorted(values); position = (len(ordered)-1)*q
        lo, hi = math.floor(position), math.ceil(position)
        return ordered[lo] + (ordered[hi]-ordered[lo])*(position-lo)
    return dict(cohort_sha256=result["fixed_cohort_sha256"], games=len(rows),
                clusters=len(clusters), seed=seed, resamples=resamples,
                cluster_membership_sha256=hashlib.sha256(json.dumps(
                    sorted(cluster_keys.items()),separators=(",", ":")).encode()).hexdigest(),
                interval_method="paired whole-week percentile Monte Carlo bootstrap",
                positive_advantage_favors="model", selection_adjusted=False,
                conditional_on="fixed predictions, observed cohort and declared week clusters",
                model_refitted_in_resamples=False, source_uncertainty_propagated=False,
                interweek_dependence_preserved=False,
                intervals={k:dict(advantage=observed[k],lower_95=quantile(v,.025),
                                  upper_95=quantile(v,.975)) for k,v in samples.items()},
                qualification="Within-week pairs stay together. Exchangeable weeks are assumed; few weeks, adjacent-week dependence and hindsight selection limit inference. This is not a prospective edge test.")


def confidence_diagnostics(result):
    if result.get("target") != "winner":
        raise ValueError("Winner confidence is not a point-margin probability")
    rows = _matched_rows(result)
    output = []
    for row in rows:
        p = _number(row["model"]); reference = _number(row["reference"]); y = _number(row["actual"])
        if not 0 <= p <= 1 or not 0 <= reference <= 1 or y not in (0,1):
            raise ValueError("Invalid probability or label")
        if (p >= .5) == (reference >= .5):
            continue
        confidence = p if p >= .5 else 1-p
        output.append(dict(game_id=row["game_id"], model_pick="HOME" if p >= .5 else "AWAY",
                           reference_pick="HOME" if reference >= .5 else "AWAY",
                           model_pick_probability=confidence,
                           model_won=(p >= .5)==bool(y),
                           confidence_in_50s=.5 <= confidence < .6))
    losses = [r for r in output if not r["model_won"]]
    return dict(disagreements=output, model_only_right=len(output)-len(losses),
                reference_only_right=len(losses),
                losing_disagreements_in_50s=sum(r["confidence_in_50s"] for r in losses),
                fixed_n=result["fixed_n"], matched_n=len(rows),
                fixed_cohort_sha256=result["fixed_cohort_sha256"],
                evaluated_cohort_sha256=cohort_digest(r["game_id"] for r in rows),
                coverage_scope=result["headline_state"],
                confidence_band="50% inclusive to 60% exclusive; chosen side, not home probability",
                winner_equality_rule="p >= 0.5 chooses HOME",
                qualification="Counts describe the explicit matched subset if coverage is incomplete; they are not an all-season or prospective betting record.",
                selection_performed=False, staking_rule=None, profit_claimed=False)


def invented_fixture():
    common = dict(target="winner",orientation="HOME",settlement="FULL_GAME_NON_TIE",
                  value_basis="CONDITIONAL_NON_TIE_PROBABILITY")
    games, models, references, clusters = [], [], [], {}
    for i in range(12):
        gid = f"invented-event-{i+1:02d}"; week=f"invented-season:REG_{i//3+1:02d}"
        decision=f"2025-10-{3+7*(i//3):02d}T18:00:00Z"
        earlier=f"2025-10-{3+7*(i//3):02d}T17:00:00Z"
        games.append(dict(game_id=gid,week=week,decision_at=decision,actual=[1,0,1,0][i%4]))
        clusters[gid]=week
        for output,series,p in [(models,"invented-model",[.56,.72,.49,.38][i%4]),
                                (references,"invented-reference",[.45,.61,.62,.55][i%4])]:
            output.append(dict(common,game_id=gid,series_id=series,value=p,
                               decision_at=decision,source_at=earlier,available_at=earlier,
                               created_at="2026-01-01T00:00:00Z"))
    ids=[r["game_id"] for r in games]
    contract=dict(common,model_id="invented-model",reference_id="invented-reference",
                  game_ids=ids,cohort_sha256=cohort_digest(ids))
    return contract,games,models,references,clusters


def demo():
    contract,games,models,references,clusters=invented_fixture()
    comparison=compare_fixed_cohort(contract,games,models,references)
    rows=[r for r in comparison["ledger"] if r["state"]=="MATCHED"]
    return dict(evidence_class="INVENTED_ENGINEERING_FIXTURE_NOT_REAL_NFL_PERFORMANCE",
                comparison=comparison,uncertainty=paired_week_bootstrap(comparison,clusters),
                calibration={f:calibration(rows,f) for f in ("model","reference")},
                disagreements=confidence_diagnostics(comparison),
                real_model_fits=0,source_requests=0,orders=0,private_recipe_published=False)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--demo",action="store_true",required=True)
    parser.add_argument("--output",type=Path)
    args=parser.parse_args();body=(json.dumps(demo(),indent=2,sort_keys=True,allow_nan=False)+"\n").encode()
    if args.output:
        args.output.parent.mkdir(parents=True,exist_ok=True)
        if args.output.exists() and args.output.read_bytes()!=body:
            raise ValueError("Existing output differs; choose a separate output path")
        if not args.output.exists():
            with args.output.open("xb") as stream:stream.write(body)
        print(json.dumps(dict(file=str(args.output),sha256=hashlib.sha256(body).hexdigest(),
                              bytes=len(body),evidence_class="INVENTED_ENGINEERING_FIXTURE")))
    else:print(body.decode(),end="")


if __name__=="__main__":main()
