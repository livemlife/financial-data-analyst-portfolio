from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
CHECKS = {
    "01_transaction_risk": {
        "required": ["summary.html", "metrics.json", "precision_recall_curve.png", "top_500_alerts.csv"],
        "metric": "roc_auc",
        "minimum": 0.75,
    },
    "02_customer_profitability": {
        "required": ["summary.html", "metrics.json", "portfolio_matrix.png", "retention_priority_top500.csv"],
        "metric": "roc_auc",
        "minimum": 0.70,
    },
    "03_credit_early_warning": {
        "required": ["summary.html", "metrics.json", "risk_distribution.png", "early_warning_watchlist_top500.csv"],
        "metric": "roc_auc",
        "minimum": 0.75,
    },
}


def main() -> int:
    errors: list[str] = []
    for project, rule in CHECKS.items():
        out = ROOT / project / "outputs"
        for filename in rule["required"]:
            path = out / filename
            if not path.exists() or path.stat().st_size == 0:
                errors.append(f"{project}: missing or empty {filename}")
        metrics_path = out / "metrics.json"
        if metrics_path.exists():
            metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
            value = float(metrics[rule["metric"]])
            if value < float(rule["minimum"]):
                errors.append(f"{project}: {rule['metric']}={value:.3f} below {rule['minimum']}")
        print(f"[CHECKED] {project}")
    if errors:
        print("\nVerification failed:")
        for error in errors:
            print(f"- {error}")
        return 1
    print("\nAll required outputs passed verification.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

