# Power BI dashboard specification

## Page 1｜Risk overview（管理者）

- KPI：取引件数、不正率、アラート数、Precision、Recall、推定損失
- 折れ線：週別アラート率・確認結果
- 棒グラフ：カテゴリ別アラート率
- スライサー：期間、カテゴリ、国不一致、端末信頼性

## Page 2｜Alert operations（担当者）

- 明細：取引ID、顧客ID、金額、時刻、リスク確率、主要要因、確認状態
- 条件付き書式：High / Medium / Low
- ドリルスルー：同一顧客の直近取引履歴

## Page 3｜Model monitoring（分析者）

- PR曲線、閾値別Recall/Precision/期待コスト
- 特徴量分布の月次変化
- 判定結果の混同行列

## Example measures

```DAX
Alert Rate = DIVIDE(SUM(Transactions[alert]), COUNTROWS(Transactions))
Fraud Recall = DIVIDE([True Positive], [True Positive] + [False Negative])
Review Cost = [Alert Count] * 500
```

