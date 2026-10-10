from __future__ import annotations

import json
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
from sklearn.metrics import (
    average_precision_score,
    confusion_matrix,
    precision_recall_curve,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
OUT = ROOT / "outputs"
RNG = np.random.default_rng(42)


def sigmoid(x: np.ndarray) -> np.ndarray:
    return 1 / (1 + np.exp(-x))


def generate_data(n: int = 30_000) -> pd.DataFrame:
    DATA.mkdir(exist_ok=True)
    customer_id = RNG.integers(1, 5001, n)
    timestamps = pd.Timestamp("2025-01-01") + pd.to_timedelta(
        RNG.integers(0, 365 * 24 * 60, n), unit="m"
    )
    category = RNG.choice(
        ["grocery", "restaurant", "travel", "electronics", "cash", "other"],
        n,
        p=[0.25, 0.22, 0.10, 0.10, 0.08, 0.25],
    )
    amount = np.clip(RNG.lognormal(6.2, 1.05, n), 100, 500_000).round(0)
    account_age_days = RNG.integers(5, 3650, n)
    device_trusted = RNG.binomial(1, 0.88, n)
    country_mismatch = RNG.binomial(1, 0.045, n)
    failed_auth_24h = np.clip(RNG.poisson(0.20, n), 0, 8)
    txn_count_1h = np.clip(RNG.poisson(1.15, n) + 1, 1, 12)
    hour = timestamps.hour.to_numpy()
    night = ((hour <= 4) | (hour >= 23)).astype(int)
    risky_category = np.isin(category, ["electronics", "cash", "travel"]).astype(int)

    logit = (
        -6.2
        + 1.65 * np.log1p(amount / 10_000)
        + 2.00 * (1 - device_trusted)
        + 2.80 * country_mismatch
        + 0.85 * failed_auth_24h
        + 0.34 * np.maximum(txn_count_1h - 2, 0)
        + 1.00 * night
        + 0.65 * risky_category
        - 0.00018 * account_age_days
    )
    fraud = RNG.binomial(1, sigmoid(logit))
    df = pd.DataFrame(
        {
            "transaction_id": [f"T{i:07d}" for i in range(1, n + 1)],
            "customer_id": [f"C{x:05d}" for x in customer_id],
            "timestamp": timestamps,
            "amount_jpy": amount.astype(int),
            "merchant_category": category,
            "account_age_days": account_age_days,
            "device_trusted": device_trusted,
            "country_mismatch": country_mismatch,
            "failed_auth_24h": failed_auth_24h,
            "txn_count_1h": txn_count_1h,
            "is_fraud": fraud,
        }
    ).sort_values("timestamp")
    df.to_csv(DATA / "transactions.csv", index=False)
    return df


def choose_threshold(y_true: pd.Series, probability: np.ndarray) -> pd.DataFrame:
    rows = []
    for threshold in np.arange(0.02, 0.81, 0.01):
        pred = (probability >= threshold).astype(int)
        tn, fp, fn, tp = confusion_matrix(y_true, pred, labels=[0, 1]).ravel()
        # False negatives are assumed to cost JPY 50k; a manual review costs JPY 500.
        cost = fn * 50_000 + fp * 500
        rows.append(
            {
                "threshold": round(float(threshold), 2),
                "precision": precision_score(y_true, pred, zero_division=0),
                "recall": recall_score(y_true, pred, zero_division=0),
                "alerts": int(tp + fp),
                "false_positive": int(fp),
                "false_negative": int(fn),
                "estimated_cost_jpy": int(cost),
            }
        )
    return pd.DataFrame(rows)


def plot_results(y_true: pd.Series, probability: np.ndarray, features: pd.DataFrame) -> None:
    sns.set_theme(style="whitegrid")
    precision, recall, _ = precision_recall_curve(y_true, probability)
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(recall, precision, color="#0067A3", linewidth=2)
    ax.set(xlabel="Recall", ylabel="Precision", title="Precision–Recall Curve (Holdout)")
    fig.tight_layout()
    fig.savefig(OUT / "precision_recall_curve.png", dpi=160)
    plt.close(fig)

    top = features.head(10).sort_values("coefficient")
    fig, ax = plt.subplots(figsize=(9, 5.5))
    colors = ["#C43D3D" if x > 0 else "#3975A5" for x in top["coefficient"]]
    ax.barh(top["feature"], top["coefficient"], color=colors)
    ax.axvline(0, color="#333333", linewidth=0.8)
    ax.set(title="Drivers of Transaction Risk", xlabel="Logistic-regression coefficient")
    fig.tight_layout()
    fig.savefig(OUT / "risk_drivers.png", dpi=160)
    plt.close(fig)


def write_html(metrics: dict, best: pd.Series) -> None:
    html = f"""<!doctype html><html lang='ja'><head><meta charset='utf-8'>
<title>取引リスク・異常検知</title><style>
body{{font-family:Arial,'Yu Gothic',sans-serif;max-width:1040px;margin:36px auto;color:#18212b}}
.cards{{display:grid;grid-template-columns:repeat(4,1fr);gap:14px}}.card{{background:#f3f7fa;padding:18px;border-left:5px solid #0067A3}}
.v{{font-size:28px;font-weight:700}}img{{max-width:48%;margin:16px 1%;vertical-align:top}}table{{border-collapse:collapse}}td,th{{padding:8px;border-bottom:1px solid #ddd}}
</style></head><body><h1>取引リスク・異常検知</h1>
<p>30,000件の匿名化想定取引を対象に、検知精度だけでなく誤検知コストを含めて運用閾値を設計した。</p>
<div class='cards'><div class='card'><div>不正率</div><div class='v'>{metrics['fraud_rate']:.2%}</div></div>
<div class='card'><div>ROC-AUC</div><div class='v'>{metrics['roc_auc']:.3f}</div></div>
<div class='card'><div>PR-AUC</div><div class='v'>{metrics['pr_auc']:.3f}</div></div>
<div class='card'><div>推奨閾値</div><div class='v'>{best['threshold']:.2f}</div></div></div>
<h2>業務判断</h2><ul><li>FN 50,000円、レビュー500円という仮定で総期待コストが最小の閾値を採用。</li>
<li>推奨閾値でPrecision {best['precision']:.1%}、Recall {best['recall']:.1%}、アラート{int(best['alerts']):,}件。</li>
<li>実運用では担当者処理能力、損失額、顧客体験に合わせて閾値を再調整する。</li></ul>
<img src='precision_recall_curve.png'><img src='risk_drivers.png'>
<p><small>データは機密情報を使用せず、業務仮説に基づき生成した合成データ。結果は実在企業を表さない。</small></p></body></html>"""
    (OUT / "summary.html").write_text(html, encoding="utf-8")


def main() -> None:
    OUT.mkdir(exist_ok=True)
    df = generate_data()
    df["hour"] = pd.to_datetime(df["timestamp"]).dt.hour
    split = int(len(df) * 0.8)
    train, test = df.iloc[:split], df.iloc[split:]
    numeric = [
        "amount_jpy", "account_age_days", "device_trusted", "country_mismatch",
        "failed_auth_24h", "txn_count_1h", "hour",
    ]
    categorical = ["merchant_category"]
    pre = ColumnTransformer(
        [
            ("num", Pipeline([("imputer", SimpleImputer(strategy="median")), ("scale", StandardScaler())]), numeric),
            ("cat", OneHotEncoder(handle_unknown="ignore"), categorical),
        ]
    )
    model = Pipeline([("pre", pre), ("model", LogisticRegression(max_iter=1200, class_weight="balanced"))])
    model.fit(train[numeric + categorical], train["is_fraud"])
    prob = model.predict_proba(test[numeric + categorical])[:, 1]
    thresholds = choose_threshold(test["is_fraud"], prob)
    best = thresholds.loc[thresholds["estimated_cost_jpy"].idxmin()]

    feature_names = [name.replace("num__", "").replace("cat__", "") for name in model.named_steps["pre"].get_feature_names_out()]
    coefficients = model.named_steps["model"].coef_[0]
    importance = pd.DataFrame({"feature": feature_names, "coefficient": coefficients})
    importance["abs_coefficient"] = importance["coefficient"].abs()
    importance = importance.sort_values("abs_coefficient", ascending=False)
    importance.to_csv(OUT / "feature_importance.csv", index=False)
    thresholds.to_csv(OUT / "threshold_cost_table.csv", index=False)

    scored = test[["transaction_id", "customer_id", "timestamp", "amount_jpy", "is_fraud"]].copy()
    scored["risk_probability"] = prob
    scored["alert"] = (prob >= best["threshold"]).astype(int)
    scored.sort_values("risk_probability", ascending=False).head(500).to_csv(OUT / "top_500_alerts.csv", index=False)

    metrics = {
        "rows": int(len(df)),
        "fraud_rate": float(df["is_fraud"].mean()),
        "roc_auc": float(roc_auc_score(test["is_fraud"], prob)),
        "pr_auc": float(average_precision_score(test["is_fraud"], prob)),
        "threshold": float(best["threshold"]),
        "precision": float(best["precision"]),
        "recall": float(best["recall"]),
        "alerts": int(best["alerts"]),
        "estimated_cost_jpy": int(best["estimated_cost_jpy"]),
    }
    (OUT / "metrics.json").write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8")
    plot_results(test["is_fraud"], prob, importance)
    write_html(metrics, best)
    print(json.dumps(metrics, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
