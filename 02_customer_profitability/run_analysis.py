from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
OUT = ROOT / "outputs"
RNG = np.random.default_rng(2026)


def sigmoid(x: np.ndarray) -> np.ndarray:
    return 1 / (1 + np.exp(-x))


def generate_data(n_customers: int = 8_000) -> tuple[pd.DataFrame, pd.DataFrame]:
    DATA.mkdir(exist_ok=True)
    ids = np.array([f"C{i:06d}" for i in range(1, n_customers + 1)])
    engagement = RNG.normal(0, 1, n_customers)
    wealth = RNG.normal(0, 1, n_customers)
    complaint_tendency = sigmoid(RNG.normal(-2.6, 0.8, n_customers))
    tenure = np.clip(RNG.gamma(2.5, 2.6, n_customers), 0.1, 30).round(1)
    channel = RNG.choice(["digital", "branch", "hybrid"], n_customers, p=[0.48, 0.20, 0.32])
    profile = pd.DataFrame(
        {
            "customer_id": ids,
            "age_band": RNG.choice(["20s", "30s", "40s", "50s", "60+"], n_customers, p=[0.13, 0.23, 0.27, 0.22, 0.15]),
            "region": RNG.choice(["Osaka", "Hyogo", "Kyoto", "Nara_Wakayama", "Other"], n_customers, p=[0.38, 0.21, 0.16, 0.10, 0.15]),
            "tenure_years": tenure,
            "primary_channel": channel,
        }
    )

    # Customers with weakening engagement form a realistic retention use case.
    decline = RNG.binomial(1, sigmoid(-1.2 - 0.55 * engagement), n_customers)
    monthly_rows = []
    for month in range(1, 12):
        trend = 1 - decline * 0.055 * (month - 1)
        transactions = np.maximum(0, RNG.poisson(np.clip((10 + 4.2 * engagement) * trend, 0.4, None)))
        balance = np.clip(np.exp(12.3 + 0.65 * wealth + 0.10 * engagement + RNG.normal(0, 0.25, n_customers)), 20_000, 30_000_000)
        fee = np.maximum(0, 650 + 170 * transactions + RNG.normal(0, 240, n_customers))
        interest = np.maximum(0, balance * (0.00060 + 0.00012 * np.maximum(wealth, -1)))
        service = 520 + 160 * (channel == "branch") + 55 * transactions
        rewards = 0.08 * fee + RNG.uniform(0, 120, n_customers)
        ecl = np.maximum(0, RNG.normal(180 + 65 * np.maximum(-wealth, 0), 90, n_customers))
        complaint = RNG.binomial(2, np.clip(complaint_tendency + decline * month * 0.003, 0, 0.75))
        digital = np.maximum(0, RNG.poisson(np.clip(8 + 5 * engagement - decline * 0.45 * month, 0.3, None)))
        for i in range(n_customers):
            monthly_rows.append((ids[i], month, int(transactions[i]), int(balance[i]), int(fee[i]), int(interest[i]), int(service[i]), int(rewards[i]), int(ecl[i]), int(complaint[i]), int(digital[i]), 1))

    recent_transactions = np.array([row[2] for row in monthly_rows[-n_customers:]])
    churn_logit = -2.45 + 1.65 * decline - 0.07 * recent_transactions + 0.55 * (channel == "branch") - 0.38 * np.log1p(tenure)
    churned = RNG.binomial(1, sigmoid(churn_logit))
    for i in range(n_customers):
        monthly_rows.append((ids[i], 12, 0 if churned[i] else int(max(0, RNG.poisson(max(recent_transactions[i], 0.3)))), 0, 0, 0, 0, 0, 0, 0, 0, int(1 - churned[i])))

    columns = [
        "customer_id", "month_no", "transaction_count", "deposit_balance_jpy",
        "fee_revenue_jpy", "interest_revenue_jpy", "service_cost_jpy",
        "rewards_cost_jpy", "expected_credit_loss_jpy", "complaint_count",
        "digital_login_count", "active_flag",
    ]
    monthly = pd.DataFrame(monthly_rows, columns=columns)
    profile.to_csv(DATA / "customer_profile.csv", index=False)
    monthly.to_csv(DATA / "monthly_activity.csv", index=False)
    return profile, monthly


def build_mart(profile: pd.DataFrame, monthly: pd.DataFrame) -> pd.DataFrame:
    db_path = DATA / "customer_analytics.db"
    if db_path.exists():
        db_path.unlink()
    with sqlite3.connect(db_path) as conn:
        profile.to_sql("customer_profile", conn, index=False)
        monthly.to_sql("monthly_activity", conn, index=False)
        sql = (ROOT / "analysis.sql").read_text(encoding="utf-8")
        return pd.read_sql_query(sql, conn)


def write_html(metrics: dict, segment: pd.DataFrame) -> None:
    segment_rows = "".join(
        f"<tr><td>{r.segment}</td><td>{int(r.customers):,}</td><td>{r.avg_margin_jpy:,.0f}</td><td>{r.churn_rate:.1%}</td><td>{r.margin_at_risk_jpy:,.0f}</td></tr>"
        for r in segment.itertuples()
    )
    html = f"""<!doctype html><html lang='ja'><head><meta charset='utf-8'><title>顧客収益性×離反予測</title><style>
body{{font-family:Arial,'Yu Gothic',sans-serif;max-width:1040px;margin:36px auto;color:#18212b}}.cards{{display:grid;grid-template-columns:repeat(4,1fr);gap:14px}}.card{{background:#f4f6fb;padding:18px;border-left:5px solid #5A3E9B}}.v{{font-size:27px;font-weight:700}}img{{max-width:48%;margin:16px 1%;vertical-align:top}}table{{width:100%;border-collapse:collapse}}td,th{{padding:8px;border-bottom:1px solid #ddd;text-align:right}}td:first-child,th:first-child{{text-align:left}}</style></head><body>
<h1>顧客収益性 × 離反予測</h1><p>「売上が高い顧客」ではなく、サービス原価・特典・期待損失を控除した貢献利益と離反確率を組み合わせ、優先対応先を選定した。</p>
<div class='cards'><div class='card'><div>顧客数</div><div class='v'>{metrics['customers']:,}</div></div><div class='card'><div>離反率</div><div class='v'>{metrics['churn_rate']:.1%}</div></div><div class='card'><div>ROC-AUC</div><div class='v'>{metrics['roc_auc']:.3f}</div></div><div class='card'><div>優先対応</div><div class='v'>{metrics['priority_customers']:,}人</div></div></div>
<h2>顧客ポートフォリオ</h2><table><tr><th>区分</th><th>顧客数</th><th>平均貢献利益</th><th>離反率</th><th>リスク利益額</th></tr>{segment_rows}</table>
<h2>提案</h2><ul><li>高収益・高離反リスク層を優先し、全顧客一律のキャンペーンを避ける。</li><li>優先対応リストには期待利益保全額を付与し、営業工数配分に使える形にする。</li><li>施策後はホールドアウト群を設け、純増利益で効果検証する。</li></ul>
<img src='portfolio_matrix.png'><img src='churn_drivers.png'><p><small>データは個人情報を使用しない合成データ。金額・施策効果は仮定であり、実在企業を表さない。</small></p></body></html>"""
    (OUT / "summary.html").write_text(html, encoding="utf-8")


def main() -> None:
    OUT.mkdir(exist_ok=True)
    profile, monthly = generate_data()
    mart = build_mart(profile, monthly)
    numeric = ["tenure_years", "avg_monthly_transactions", "avg_deposit_balance_jpy", "contribution_margin_jpy", "complaint_count", "avg_digital_logins", "transaction_trend"]
    categorical = ["age_band", "region", "primary_channel"]
    X_train, X_test, y_train, y_test = train_test_split(mart[numeric + categorical], mart["churned"], test_size=0.25, random_state=42, stratify=mart["churned"])
    pre = ColumnTransformer([
        ("num", Pipeline([("imputer", SimpleImputer(strategy="median")), ("scale", StandardScaler())]), numeric),
        ("cat", OneHotEncoder(handle_unknown="ignore"), categorical),
    ])
    model = Pipeline([("pre", pre), ("model", LogisticRegression(max_iter=1200, class_weight="balanced"))])
    model.fit(X_train, y_train)
    test_prob = model.predict_proba(X_test)[:, 1]
    mart["churn_probability"] = model.predict_proba(mart[numeric + categorical])[:, 1]
    mart["expected_margin_at_risk_jpy"] = (mart["contribution_margin_jpy"].clip(lower=0) * mart["churn_probability"]).round(0)
    q75_margin = mart["contribution_margin_jpy"].quantile(0.75)
    q70_risk = mart["churn_probability"].quantile(0.70)
    mart["priority_flag"] = ((mart["contribution_margin_jpy"] >= q75_margin) & (mart["churn_probability"] >= q70_risk)).astype(int)
    mart["segment"] = np.select(
        [
            (mart["contribution_margin_jpy"] >= q75_margin) & (mart["churn_probability"] >= q70_risk),
            (mart["contribution_margin_jpy"] >= q75_margin),
            (mart["churn_probability"] >= q70_risk),
        ],
        ["High value / At risk", "High value / Stable", "Low value / At risk"],
        default="Core / Stable",
    )
    segment = mart.groupby("segment", as_index=False).agg(customers=("customer_id", "count"), avg_margin_jpy=("contribution_margin_jpy", "mean"), churn_rate=("churned", "mean"), margin_at_risk_jpy=("expected_margin_at_risk_jpy", "sum"))
    mart.sort_values("expected_margin_at_risk_jpy", ascending=False).head(500).to_csv(OUT / "retention_priority_top500.csv", index=False)
    segment.to_csv(OUT / "segment_summary.csv", index=False)

    names = [name.replace("num__", "").replace("cat__", "") for name in model.named_steps["pre"].get_feature_names_out()]
    coef = model.named_steps["model"].coef_[0]
    importance = pd.DataFrame({"feature": names, "coefficient": coef}).assign(abs_coefficient=lambda x: x.coefficient.abs()).sort_values("abs_coefficient", ascending=False)
    importance.to_csv(OUT / "churn_feature_importance.csv", index=False)

    sns.set_theme(style="whitegrid")
    sample = mart.sample(min(3000, len(mart)), random_state=42)
    fig, ax = plt.subplots(figsize=(8.5, 5.5))
    sns.scatterplot(data=sample, x="churn_probability", y="contribution_margin_jpy", hue="segment", alpha=0.65, s=28, ax=ax)
    ax.set(title="Customer Portfolio: Value × Churn Risk", xlabel="Churn probability", ylabel="Contribution margin (JPY)")
    fig.tight_layout(); fig.savefig(OUT / "portfolio_matrix.png", dpi=160); plt.close(fig)
    top = importance.head(10).sort_values("coefficient")
    fig, ax = plt.subplots(figsize=(9, 5.5)); ax.barh(top["feature"], top["coefficient"], color="#5A3E9B"); ax.axvline(0, color="#333", lw=0.8); ax.set(title="Drivers of Churn", xlabel="Coefficient"); fig.tight_layout(); fig.savefig(OUT / "churn_drivers.png", dpi=160); plt.close(fig)

    metrics = {
        "customers": int(len(mart)), "churn_rate": float(mart["churned"].mean()),
        "roc_auc": float(roc_auc_score(y_test, test_prob)), "pr_auc": float(average_precision_score(y_test, test_prob)),
        "priority_customers": int(mart["priority_flag"].sum()),
        "priority_margin_at_risk_jpy": int(mart.loc[mart["priority_flag"] == 1, "expected_margin_at_risk_jpy"].sum()),
    }
    (OUT / "metrics.json").write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8")
    write_html(metrics, segment)
    print(json.dumps(metrics, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
