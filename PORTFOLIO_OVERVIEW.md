# データ分析ポートフォリオ一覧

PythonとSQLを使った、金融市場・業務プロセス・ソフトウェア品質の3つの分析プロジェクトです。分析課題、データの定義、結果、解釈の限界と再現手順を各プロジェクトに掲載しています。

## 01 金融市場の収益とリスク分析

公開月次データ282か月を使い、S&P 500の価格リターン、ボラティリティ、最大ドローダウンを分析しました。

**使用技術：** Python、Pandas、NumPy、SQL、SQLite、データ可視化

[プロジェクトを見る →](https://github.com/livemlife/financial-market-analysis-portfolio)

![金融市場の推移](https://raw.githubusercontent.com/livemlife/financial-market-analysis-portfolio/main/charts/market.svg)

## 02 業務KPIと処理プロセスの改善分析

模擬タスク2,880件を使い、作業時間・待ち時間・エラー率・SLAを分析しました。難易度構成を調整した比較も実施しています。

**使用技術：** Python、SQL、KPI設計、構成調整、ブートストラップ

[プロジェクトを見る →](https://github.com/livemlife/business-process-kpi-portfolio)

![業務プロセスの分析](https://raw.githubusercontent.com/livemlife/business-process-kpi-portfolio/main/charts/process.svg)

## 03 ソフトウェア品質と欠陥の分析

模擬欠陥779件を使い、検出傾向、本番検出比率、解決日数と未解決案件を分析しました。テスト実行数による正規化を併記しています。

**使用技術：** Python、SQL、品質KPI、欠陥分析、データ品質検証

[プロジェクトを見る →](https://github.com/livemlife/software-quality-defect-portfolio)

![ソフトウェア品質の分析](https://raw.githubusercontent.com/livemlife/software-quality-defect-portfolio/main/charts/defects.svg)

## 成果物とデータについて

各プロジェクトにCSV、Pythonコード、SQL、集計結果、図表と日語の説明を掲載しています。HTMLレポートはリポジトリをダウンロード・展開後、report.htmlをブラウザーで開いて閲覧できます。

金融プロジェクトは公開歴史データを使用しています。業務・品質プロジェクトは完全な模擬ケースであり、勤務先の内部データや実際の改善実績ではありません。Power BIは構築仕様とDAX例を提供しており、Desktopでの実装・検証は未実施です。
