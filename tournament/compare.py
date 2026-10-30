"""Score strategy files on the quantgen case suites and write a leaderboard.

Run from Trading_Algorithm/ with the backtester's environment:

    uv run --project ../backtester python tournament/compare.py strategies/S1 strategies/S2 --suite dev

Suites: `quick` (8 cases x seed 1), `dev` (42 cases x seeds 1-2, for tuning), `heldout` (42 cases x seeds 3-5,
judging only), `full` (42 cases x seeds 1-5). Each strategy is a folder holding `trader.py` (named after the
folder) or a `.py` file. Real days -2, -1, 0 are always run as a sanity check unless `--no-real` is given.
"""

import argparse
import json
import sys
import time
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np
from quantgen.adapter.runner import MatchMode, run_day
from quantgen.adapter.strategy import Strategy
from quantgen.cases.case import TIERS, Case, load_catalog
from quantgen.generator.params import load_params
from quantgen.real_data import REAL_DAYS, load_real_day
from quantgen.scoring.metrics import TIER_WEIGHTS, CaseStats, overall
from quantgen.scoring.reference import REFERENCE_NAME, reference_strategy
from quantgen.scoring.run_suite import default_workers, run_suite
from quantgen.scoring.suites import QUICK_CASES, Suite
from quantgen.scoring.verdicts import WEAK, Verdict, all_verdicts

BACKTESTER = Path(__file__).resolve().parents[2] / "backtester"
PARAMS = BACKTESTER / "params" / "params.json"
SUITES = {
    "quick": Suite("quick", QUICK_CASES, (1,)),
    "dev": Suite("dev", None, (1, 2)),
    "heldout": Suite("heldout", None, (3, 4, 5)),
    "full": Suite("full", None, (1, 2, 3, 4, 5)),
}
BOOTSTRAP_REPS = 2000
BOOTSTRAP_SEED = 20261101
TICKS_PER_DAY = 10_000


@dataclass(frozen=True)
class RealDayResult:
    total: float
    product_pnl: Mapping[str, float]
    limit_breaches: int
    seconds: float


def load_strategy(path: Path) -> Strategy:
    file = path / "trader.py" if path.is_dir() else path
    if not file.is_file():
        raise SystemExit(f"{file}: no trader.py found")
    name = path.name if path.is_dir() else path.stem
    return Strategy(name=name, source=file.read_text(encoding="utf-8"))


def run_real(strategy: Strategy) -> dict[int, RealDayResult]:
    out = {}
    for day in REAL_DAYS:
        started = time.perf_counter()
        result = run_day(strategy, load_real_day(BACKTESTER, day), MatchMode.ALL, with_log=False)
        elapsed = time.perf_counter() - started
        out[day] = RealDayResult(result.total_pnl, dict(result.product_pnl), result.limit_breaches, elapsed)
    return out


def case_weights(cases: Sequence[Case]) -> np.ndarray:
    """Each case's share of the tier-weighted score: a tier's weight split equally over its cases."""
    present = {case.tier for case in cases}
    total = sum(TIER_WEIGHTS[tier] for tier in present)
    counts = {tier: sum(1 for case in cases if case.tier == tier) for tier in present}
    return np.array([TIER_WEIGHTS[case.tier] / total / counts[case.tier] for case in cases])


def paired_bootstrap(
    a: Sequence[CaseStats], b: Sequence[CaseStats], cases: Sequence[Case]
) -> tuple[float, float, float]:
    """Tier-weighted mean of (a - b) and its 95% CI, resampling cases within each tier. Both strategies saw the
    same generated days, so the per-case differences are paired."""
    diff = np.array([sa.mean_pnl - sb.mean_pnl for sa, sb in zip(a, b, strict=True)])
    weights = case_weights(cases)
    rng = np.random.default_rng(BOOTSTRAP_SEED)
    reps = np.zeros(BOOTSTRAP_REPS)
    for tier in TIERS:
        idx = np.array([i for i, case in enumerate(cases) if case.tier == tier])
        if idx.size == 0:
            continue
        draws = rng.choice(idx, size=(BOOTSTRAP_REPS, idx.size), replace=True)
        reps += weights[idx].sum() * diff[draws].mean(axis=1)
    low, high = np.percentile(reps, [2.5, 97.5])
    return float(weights @ diff), float(low), float(high)


def product_means(stats: Sequence[CaseStats], cases: Sequence[Case]) -> dict[str, float]:
    """Tier-weighted mean PnL per product across the suite's cases."""
    weights = case_weights(cases)
    products = sorted({name for s in stats for name in s.product_mean_pnl})
    return {
        product: float(sum(w * s.product_mean_pnl.get(product, 0.0) for w, s in zip(weights, stats, strict=True)))
        for product in products
    }


def summarise(name: str, stats: Sequence[CaseStats], verdicts: Sequence[Verdict], cases: Sequence[Case]) -> dict:
    total = overall(stats)
    return {
        "strategy": name,
        "weighted_pnl": total.weighted_pnl,
        "worst_case": total.worst_case,
        "worst_case_pnl": total.worst_case_pnl,
        "worst_seed_pnl": min(s.worst_pnl for s in stats),
        "weak_cases": sum(1 for v in verdicts if v.rating == WEAK),
        "mean_drawdown": float(np.mean([s.mean_drawdown for s in stats])),
        "limit_breaches": sum(s.limit_breaches for s in stats),
        "crashes": sum(len(s.errors) for s in stats),
        "product_pnl": product_means(stats, cases),
        "cases": {
            s.case_id: {"tier": s.tier, "mean": s.mean_pnl, "worst": s.worst_pnl, "by_seed": dict(s.pnl_by_seed)}
            for s in stats
        },
        "verdicts": {v.case_id: {"rating": v.rating, "reason": v.reason} for v in verdicts},
    }


def _ranking_table(rows: Sequence[dict]) -> list[str]:
    lines = ["| Rank | Strategy | Weighted PnL | Worst case | Worst seed | Weak | Mean DD | Breaches | Crashes |"]
    lines.append("|---:|---|---:|---|---:|---:|---:|---:|---:|")
    for rank, r in enumerate(rows, start=1):
        lines.append(
            f"| {rank} | {r['strategy']} | {r['weighted_pnl']:,.0f} | {r['worst_case']} ({r['worst_case_pnl']:,.0f}) "
            f"| {r['worst_seed_pnl']:,.0f} | {r['weak_cases']} | {r['mean_drawdown']:,.0f} | {r['limit_breaches']} "
            f"| {r['crashes']} |"
        )
    return lines


def _pairs_table(pairs: Sequence[dict]) -> list[str]:
    lines = ["## Paired difference vs leader (tier-weighted, 95% case-bootstrap CI)", ""]
    lines += ["| Strategy | Leader minus strategy | 95% CI |", "|---|---:|---|"]
    lines += [f"| {p['strategy']} | {p['diff']:,.0f} | [{p['low']:,.0f}, {p['high']:,.0f}] |" for p in pairs]
    return lines


def _real_table(real: Mapping[str, Mapping[int, RealDayResult]]) -> list[str]:
    lines = ["## Real days", "", "| Strategy | Day -2 | Day -1 | Day 0 | Total | Breaches | ms/tick |"]
    lines.append("|---|---:|---:|---:|---:|---:|---:|")
    for name, days in real.items():
        cells = " | ".join(f"{days[d].total:,.0f}" for d in REAL_DAYS)
        total = sum(days[d].total for d in REAL_DAYS)
        breaches = sum(days[d].limit_breaches for d in REAL_DAYS)
        ms = 1000 * np.mean([days[d].seconds for d in REAL_DAYS]) / TICKS_PER_DAY
        lines.append(f"| {name} | {cells} | {total:,.0f} | {breaches} | {ms:.2f} |")
    return lines


def _product_table(rows: Sequence[dict]) -> list[str]:
    products = sorted({p for r in rows for p in r["product_pnl"]})
    lines = ["## Tier-weighted PnL by product", ""]
    lines += ["| Product | " + " | ".join(r["strategy"] for r in rows) + " |", "|---|" + "---:|" * len(rows)]
    for p in products:
        lines.append(f"| {p} | " + " | ".join(f"{r['product_pnl'].get(p, 0.0):,.0f}" for r in rows) + " |")
    return lines


def _weak_list(rows: Sequence[dict]) -> list[str]:
    lines = ["## Weak cases", ""]
    for r in rows:
        weak = [f"{case} ({v['reason']})" for case, v in r["verdicts"].items() if v["rating"] == WEAK]
        lines.append(f"- **{r['strategy']}:** " + ("; ".join(weak) if weak else "none"))
    return lines


def leaderboard_markdown(suite: Suite, rows: Sequence[dict], pairs: Sequence[dict], real: Mapping) -> str:
    sections = [[f"# Leaderboard: {suite.name} suite (seeds {list(suite.seeds)})"], _ranking_table(rows)]
    if pairs:
        sections.append(_pairs_table(pairs))
    if real:
        sections.append(_real_table(real))
    sections += [_product_table(rows), _weak_list(rows)]
    return "\n\n".join("\n".join(section) for section in sections) + "\n"


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("strategies", nargs="+", type=Path, help="strategy folders or .py files")
    parser.add_argument("--suite", choices=sorted(SUITES), default="quick")
    parser.add_argument("--cases", nargs="+", help="restrict to these case ids")
    parser.add_argument("--no-real", action="store_true", help="skip the real days -2, -1, 0")
    parser.add_argument("--workers", type=int, default=default_workers())
    parser.add_argument("--out", type=Path, default=Path("tournament/results"), help="folder for JSON + Markdown")
    parser.add_argument("--tag", default=None, help="output file stem (default: suite name)")
    return parser


def _progress(done: int, total: int) -> None:
    print(f"\r{done}/{total} days", end="\n" if done == total else "", file=sys.stderr, flush=True)


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    strategies = [load_strategy(path) for path in args.strategies]
    names = [s.name for s in strategies]
    if len(set(names)) != len(names) or REFERENCE_NAME in names:
        raise SystemExit(f"strategy names must be unique and not '{REFERENCE_NAME}': {names}")
    base = SUITES[args.suite]
    suite = Suite(base.name, tuple(args.cases), base.seeds) if args.cases else base
    cases = suite.cases(load_catalog())

    everyone = [*strategies, reference_strategy()]
    result = run_suite(everyone, load_params(PARAMS), cases, suite, MatchMode.ALL, args.workers, _progress)
    judged = [*names, REFERENCE_NAME]
    stats = {name: result.stats(name) for name in judged}
    verdicts = all_verdicts(stats, judged, REFERENCE_NAME)
    rows = sorted((summarise(n, stats[n], verdicts[n], cases) for n in judged), key=lambda r: -r["weighted_pnl"])
    leader = rows[0]["strategy"]
    pairs = []
    for row in rows[1:]:
        diff, low, high = paired_bootstrap(stats[leader], stats[row["strategy"]], cases)
        pairs.append({"strategy": row["strategy"], "diff": diff, "low": low, "high": high})
    real = {} if args.no_real else {s.name: run_real(s) for s in strategies}

    args.out.mkdir(parents=True, exist_ok=True)
    stem = args.tag or suite.name
    real_json = {name: {str(d): asdict(res) for d, res in days.items()} for name, days in real.items()}
    payload = {"suite": suite.name, "seeds": list(suite.seeds), "rows": rows, "pairs": pairs, "real": real_json}
    (args.out / f"{stem}.json").write_text(json.dumps(payload, indent=1), encoding="utf-8")
    markdown = leaderboard_markdown(suite, rows, pairs, real)
    (args.out / f"{stem}.md").write_text(markdown, encoding="utf-8")
    print(markdown)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
