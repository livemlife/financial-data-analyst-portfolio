from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, brier_score_loss, roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
OUT = ROOT / "outputs"
RNG = np.random.default_rng(771)
FEATURES = [
    "sales_growth", "ebitda_margin", "cashflow_margin", "current_ratio",
    "debt_to_ebitda", "interest_coverage", "dso_days", "delinquency_days",
]


def sigmoid(x: np.ndarray) -> np.ndarray:
    return 1 / (1 + np.exp(-x))


def generate_data(n_firms: int = 5_000) -> pd.DataFrame:
    DATA.mkdir(exist_ok=True)
    ids = np.array([f"SME{i:06d}" for i in range(1, n_firms + 1)])
    sectors = RNG.choice(["manufacturing", "wholesale", "retail", "services", "construction"], n_firms, p=[0.25, 0.19, 0.18, 0.23, 0.15])
    base_quality = RNG.normal(0, 1, n_firms)
    base_sales = np.exp(RNG.normal(4.2, 0.8, n_firms))  # JPY million
    rows = []
    for q in range(1, 8):
        macro_shock = -0.035 if q >= 6 else 0.0
        sales_growth = RNG.normal(0.025 + 0.045 * base_quality + macro_shock, 0.10, n_firms)
        ebitda_margin = np.clip(RNG.normal(0.105 + 0.035 * base_quality + macro_shock / 2, 0.055, n_firms), -0.20, 0.40)
        cashflow_margin = np.clip(ebitda_margin - RNG.normal(0.022, 0.045, n_firms), -0.35, 0.35)
        current_ratio = np.clip(RNG.normal(1.50 + 0.20 * base_quality, 0.35, n_firms), 0.25, 3.5)
        debt_to_ebitda = np.clip(RNG.lognormal(1.0 - 0.20 * base_quality, 0.50, n_firms), 0.1, 16)
        interest_coverage = np.clip(RNG.lognormal(1.25 + 0.30 * base_quality, 0.65, n_firms), 0.05, 40)
        dso_days = np.clip(RNG.normal(53 - 6 * base_quality - 30 * macro_shock, 15, n_firms), 5, 160)
        delinquency_days = np.where(RNG.random(n_firms) < sigmoid(-3.0 - 0.75 * base_quality), RNG.choice([5, 15, 30, 60, 90], n_firms, p=[0.20, 0.22, 0.24, 0.20, 0.14]), 0)
        revenue = np.maximum(5, base_sales * (1 + sales_growth) ** q)
        risk_logit = (
            -4.65 - 3.4 * sales_growth - 4.3 * ebitda_margin - 2.8 * cashflow_margin
            - 0.75 * current_ratio + 0.24 * debt_to_ebitda - 0.17 * np.log1p(interest_coverage)
            + 0.012 * np.maximum(dso_days - 45, 0) + 0.025 * delinquency_days
            + 0.28 * (sectors == "construction")
        )
        distress = RNG.binomial(1, sigmoid(risk_logit))
        for i in range(n_firms):
            rows.append((ids[i], sectors[i], q, revenue[i], sales_growth[i], ebitda_margin[i], cashflow_margin[i], current_ratio[i], debt_to_ebitda[i], interest_coverage[i], dso_days[i], int(delinquency_days[i]), int(distress[i])))
    columns = ["company_id", "sector", "quarter", "revenue_jpy_m", *FEATURES, "distress_next_q"]
    df = pd.DataFrame(rows, columns=columns)
    df.to_csv(DATA / "sme_quarterly_financials.csv", index=False)
    return df


def band(p: pd.Series | np.ndarray) -> np.ndarray:
    return np.select([np.asarray(p) >= 0.04, np.asarray(p) >= 0.015], ["High", "Monitor"], default="Low")


def write_html(metrics: dict, migration: pd.DataFrame) -> None:
    rows = "".join(f"<tr><td>{r.baseline_band}</td><td>{r.stress_band}</td><td>{int(r.companies):,}</td></tr>" for r in migration.itertuples())
    html = f"""<!doctype html><html lang='ja'><head><meta charset='utf-8'><title>財務健全性・早期警戒</title><style>
body{{font-family:Arial,'Yu Gothic',sans-serif;max-width:1040px;margin:36px auto;color:#18212b}}.cards{{display:grid;grid-template-columns:repeat(4,1fr);gap:14px}}.card{{background:#f6f5f1;padding:18px;border-left:5px solid #B26A00}}.v{{font-size:27px;font-weight:700}}img{{max-width:48%;margin:16px 1%;vertical-align:top}}table{{border-collapse:collapse;width:70%}}td,th{{padding:8px;border-bottom:1px solid #ddd;text-align:right}}td:first-child,th:first-child{{text-align:left}}</style></head><body>
<h1>法人財務の早期警戒・ストレステスト</h1><p>四半期財務指標から翌四半期の要注意化を予測し、売上減少・金利負担増のストレスシナリオで監視先の増加を評価した。</p>
<div class='cards'><div class='card'><div>企業数</div><div class='v'>{metrics['companies']:,}</div></div><div class='card'><div>検証ROC-AUC</div><div class='v'>{metrics['roc_auc']:.3f}</div></div><div class='card'><div>平常時High</div><div class='v'>{metrics['baseline_high']:,}社</div></div><div class='card'><div>Stress時High</div><div class='v'>{metrics['stress_high']:,}社</div></div></div>
<h2>リスク帯の移行</h2><table><tr><th>平常時</th><th>ストレス時</th><th>企業数</th></tr>{rows}</table>
<h2>業務判断</h2><ul><li>スコアだけでなく悪化要因、残高、業種を添えたwatchlistを出力。</li><li>High移行先には財務資料の更新、返済状況確認、担当者レビューを優先。</li><li>時間順で学習・検証を分離し、将来情報の混入を防止。閾値は審査能力と損失許容度で調整する。</li></ul>
<img src='risk_distribution.png'><img src='risk_drivers.png'><p><small>本分析は業務設計を示す合成データのケーススタディであり、信用判断には使用できない。</small></p></body></html>"""
    (OUT / "summary.html").write_text(html, encoding="utf-8")


def main() -> None:
    OUT.mkdir(exist_ok=True)
    df = generate_data()
    train = df[df["quarter"] <= 6].copy()
    test = df[df["quarter"] == 7].copy()
    model = Pipeline([("scale", StandardScaler()), ("model", LogisticRegression(max_iter=1200))])
    model.fit(train[FEATURES], train["distress_next_q"])
    prob = model.predict_proba(test[FEATURES])[:, 1]
    test["baseline_probability"] = prob
    test["baseline_band"] = band(prob)

    stressed = test[FEATURES].copy()
    stressed["sales_growth"] -= 0.10
    stressed["ebitda_margin"] -= 0.03
    stressed["cashflow_margin"] -= 0.04
    stressed["current_ratio"] = np.maximum(0.20, stressed["current_ratio"] - 0.15)
    stressed["interest_coverage"] = np.maximum(0.01, stressed["interest_coverage"] * 0.65)
    stressed["debt_to_ebitda"] *= 1.18
    stress_prob = model.predict_proba(stressed)[:, 1]
    test["stress_probability"] = stress_prob
    test["stress_band"] = band(stress_prob)
    test["probability_change"] = test["stress_probability"] - test["baseline_probability"]
    test["exposure_at_risk_jpy_m"] = (test["revenue_jpy_m"] * test["stress_probability"] * 0.12).round(1)
    test.sort_values(["stress_probability", "exposure_at_risk_jpy_m"], ascending=False).head(500).to_csv(OUT / "early_warning_watchlist_top500.csv", index=False)

    migration = test.groupby(["baseline_band", "stress_band"], as_index=False).agg(companies=("company_id", "count"))
    migration.to_csv(OUT / "risk_band_migration.csv", index=False)
    importance = pd.DataFrame({"feature": FEATURES, "coefficient": model.named_steps["model"].coef_[0]})
    importance["abs_coefficient"] = importance["coefficient"].abs()
    importance = importance.sort_values("abs_coefficient", ascending=False)
    importance.to_csv(OUT / "risk_feature_importance.csv", index=False)

    sns.set_theme(style="whitegrid")
    fig, ax = plt.subplots(figsize=(8.5, 5.3))
    sns.kdeplot(test["baseline_probability"], label="Baseline", fill=True, alpha=0.25, color="#3975A5", ax=ax)
    sns.kdeplot(test["stress_probability"], label="Stress", fill=True, alpha=0.25, color="#B26A00", ax=ax)
    display_max = min(0.25, float(test["stress_probability"].quantile(0.995) * 1.15))
    ax.set_xlim(0, max(display_max, 0.06))
    ax.axvline(0.015, color="#777", linestyle="--", linewidth=1, label="Monitor threshold")
    ax.axvline(0.04, color="#9B2C2C", linestyle="--", linewidth=1, label="High threshold")
    ax.set(title="Risk Probability Under Stress", xlabel="Predicted probability"); ax.legend(); fig.tight_layout(); fig.savefig(OUT / "risk_distribution.png", dpi=160); plt.close(fig)
    top = importance.sort_values("coefficient")
    fig, ax = plt.subplots(figsize=(8.5, 5.2)); ax.barh(top["feature"], top["coefficient"], color=["#B26A00" if x > 0 else "#3975A5" for x in top["coefficient"]]); ax.axvline(0, color="#333", lw=0.8); ax.set(title="Drivers of Financial Distress", xlabel="Coefficient"); fig.tight_layout(); fig.savefig(OUT / "risk_drivers.png", dpi=160); plt.close(fig)

    metrics = {
        "companies": int(test["company_id"].nunique()),
        "test_distress_rate": float(test["distress_next_q"].mean()),
        "roc_auc": float(roc_auc_score(test["distress_next_q"], prob)),
        "pr_auc": float(average_precision_score(test["distress_next_q"], prob)),
        "brier_score": float(brier_score_loss(test["distress_next_q"], prob)),
        "baseline_high": int((test["baseline_band"] == "High").sum()),
        "stress_high": int((test["stress_band"] == "High").sum()),
        "new_high_under_stress": int(((test["baseline_band"] != "High") & (test["stress_band"] == "High")).sum()),
    }
    (OUT / "metrics.json").write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8")
    write_html(metrics, migration)
    print(json.dumps(metrics, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
