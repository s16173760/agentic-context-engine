"""Compare baseline and ACE sessions for Smart Form Filler."""

from __future__ import annotations
import sys
import argparse
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd


LOGGER = logging.getLogger("smart_form_filler.compare")

ARTIFACTS_DIR = Path(__file__).resolve().parent / "artifacts"


def _load_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def _latest(pattern: str) -> Optional[Path]:
    candidates = sorted(ARTIFACTS_DIR.glob(pattern))
    return candidates[-1] if candidates else None


def _summarize(path: Path) -> Dict[str, Any]:
    data = _load_json(path)
    metrics = data.get("metrics", {})
    normalizations = data.get("normalizations_applied", {})
    return {
        "path": str(path),
        "time_seconds": metrics.get("total_time_seconds"),
        "steps": metrics.get("steps"),
        "validation_errors": metrics.get("validation_error_count"),
        "status": metrics.get("final_status"),
        "zero_error_first_try": metrics.get("zero_error_first_try"),
        "normalizations": len(normalizations) if isinstance(normalizations, dict) else None,
    }


def _compare(baseline: Dict[str, Any], ace: Dict[str, Any]) -> Dict[str, Any]:
    comparison = {
        "baseline_path": baseline["path"],
        "ace_path": ace["path"],
        "time_improvement_pct": None,
        "steps_improvement_pct": None,
        "errors_resolved": None,
    }

    if baseline["time_seconds"] and ace["time_seconds"] is not None:
        comparison["time_improvement_pct"] = round(
            ((baseline["time_seconds"] - ace["time_seconds"]) / baseline["time_seconds"]) * 100,
            2,
        )

    if baseline["steps"] and ace["steps"] is not None:
        comparison["steps_improvement_pct"] = round(
            ((baseline["steps"] - ace["steps"]) / baseline["steps"]) * 100,
            2,
        )

    if baseline["validation_errors"] is not None and ace["validation_errors"] is not None:
        comparison["errors_resolved"] = baseline["validation_errors"] - ace["validation_errors"]

    return comparison


def _print_summary(baseline: Dict[str, Any], ace_results: List[Dict[str, Any]], comparisons: List[Dict[str, Any]]) -> None:
    LOGGER.info("Baseline: %s", baseline)
    for ace in ace_results:
        LOGGER.info("ACE run: %s", ace)

    for cmp_result in comparisons:
        LOGGER.info("Comparison: %s", cmp_result)


def _save_excel(
    *,
    baseline: Dict[str, Any],
    ace_results: List[Dict[str, Any]],
    comparisons: List[Dict[str, Any]],
    output_path: Path,
) -> None:
    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        df_baseline = pd.DataFrame([baseline])
        df_baseline.to_excel(writer, sheet_name="Baseline", index=False)

        df_ace = pd.DataFrame(ace_results)
        df_ace.to_excel(writer, sheet_name="ACE Runs", index=False)

        df_cmp = pd.DataFrame(comparisons)
        df_cmp.to_excel(writer, sheet_name="Comparisons", index=False)

    LOGGER.info("Excel report saved to %s", output_path)


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare baseline vs ACE sessions")
    parser.add_argument(
        "--baseline",
        help="Path to baseline JSON. Defaults to latest session1_baseline_*.json.",
    )
    parser.add_argument(
        "--ace",
        nargs="*",
        help="Paths to ACE session JSON files. Defaults to latest session2_with_ace_*.json if ommitted.",
    )
    parser.add_argument(
        "--output",
        help="Optional Excel output path (e.g., comparison_report.xlsx)",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Logging level",
    )

    args = parser.parse_args()
    logging.basicConfig(
        level=getattr(logging, args.log_level.upper()),
        format="%(asctime)s | %(levelname)s | %(message)s",
    )

    baseline_path = Path(args.baseline).resolve() if args.baseline else _latest("session1_baseline_*.json")
    if not baseline_path or not baseline_path.exists():
        LOGGER.error("Baseline results not found. Run session1_baseline.py first.")
        sys.exit(1)

    ace_paths: List[Path]
    if args.ace:
        ace_paths = [Path(p).resolve() for p in args.ace]
    else:
        latest_ace = _latest("session2_with_ace_*.json")
        if not latest_ace:
            LOGGER.error("ACE results not found. Run session2_with_ace.py first.")
            sys.exit(1)
        ace_paths = [latest_ace]

    baseline_summary = _summarize(baseline_path)
    ace_summaries = [_summarize(path) for path in ace_paths]
    comparisons = [_compare(baseline_summary, ace) for ace in ace_summaries]

    _print_summary(baseline_summary, ace_summaries, comparisons)

    if args.output:
        output_path = Path(args.output).resolve()
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = ARTIFACTS_DIR / f"comparison_report_{timestamp}.xlsx"

    _save_excel(
        baseline=baseline_summary,
        ace_results=ace_summaries,
        comparisons=comparisons,
        output_path=output_path,
    )


if __name__ == "__main__":
    main()
