# Power BI dashboard specification

## Page 1｜Credit overview（管理者）

- KPI：対象企業数、High社数、Highエクスポージャー、新規High移行数
- Sankey相当：BaselineからStressへのリスク帯移行
- 棒グラフ：業種別High比率・エクスポージャー

## Page 2｜Watchlist（営業・審査）

- 明細：企業ID、業種、売上、Baseline/Stress確率、悪化幅、財務指標
- 条件付き書式：High / Monitor / Low
- ドリルスルー：7四半期の指標推移

## Page 3｜Model governance（モデル管理）

- ROC-AUC、PR-AUC、Brier score
- 四半期別スコア分布、実績率、特徴量ドリフト
- データ更新日、欠損率、モデル版

## Example measures

```DAX
High Companies = CALCULATE(DISTINCTCOUNT(Watchlist[company_id]), Watchlist[stress_band] = "High")
New High = CALCULATE(DISTINCTCOUNT(Watchlist[company_id]), Watchlist[baseline_band] <> "High", Watchlist[stress_band] = "High")
Exposure at Risk = SUM(Watchlist[exposure_at_risk_jpy_m])
```

