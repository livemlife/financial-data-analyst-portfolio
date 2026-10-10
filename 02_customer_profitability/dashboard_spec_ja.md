# Power BI dashboard specification

## Page 1｜Portfolio（管理者）

- KPI：顧客数、貢献利益、離反率、利益リスク額、優先対象数
- 散布図：離反確率 × 貢献利益（顧客セグメントで色分け）
- 積み上げ棒：地域・チャネル別の利益と離反

## Page 2｜Retention action（営業）

- 明細：顧客ID、利益、離反確率、利用トレンド、苦情数、推奨優先度
- スライサー：地域、チャネル、セグメント、担当者
- ドリルスルー：月次利用推移

## Page 3｜Experiment（施策責任者）

- 接触群／比較群の離反率、利益、接触コスト
- 純増利益と信頼区間

## Example measures

```DAX
Contribution Margin = SUM(CustomerMart[annualized_revenue_jpy]) - SUM(CustomerMart[annualized_cost_jpy])
Margin at Risk = SUMX(CustomerMart, CustomerMart[contribution_margin_jpy] * CustomerMart[churn_probability])
Priority Customers = CALCULATE(DISTINCTCOUNT(CustomerMart[customer_id]), CustomerMart[priority_flag] = 1)
```

