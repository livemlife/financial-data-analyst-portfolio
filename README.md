# Enterprise Data Analyst Portfolio｜金融×業務改善

RPA・QA・業務改善の実務経験を土台に、**分析を作って終わらせず、現場の判断と効果検証までつなげる力**を示す3つのケーススタディです。金融機関の機密情報・個人情報は使用せず、再現可能な合成データで業務設計を表現しています。

- Location: Osaka, Japan
- Languages: Japanese（JLPT N1）, Chinese, Korean
- Experience: RPA, QA, Test Automation, Business Process Improvement

## 3 projects

| Project | Business decision | Key result | Skills |
|---|---|---:|---|
| [01 取引リスク・異常検知](01_transaction_risk/) | どの取引を人手確認へ回すか | ROC-AUC 0.848 / Recall 68.2% | Python, ML, 不均衡データ, 閾値・コスト設計 |
| [02 顧客収益性×離反予測](02_customer_profitability/) | 限られた営業工数を誰に使うか | ROC-AUC 0.759 / 優先29人 | SQL, SQLite, 顧客収益性, セグメント, BI |
| [03 財務健全性・早期警戒](03_credit_early_warning/) | どの法人を先にモニタリングするか | ROC-AUC 0.854 / StressでHigh +343社 | 財務指標, 時系列検証, ストレステスト |

## Why this portfolio

- **結論 → 数字 → 判断**の順で、非技術部門にも伝わる構成
- データ生成、SQL、前処理、モデル、可視化、施策対象リストまで再現可能
- Accuracyではなく、PR-AUC、誤検知コスト、利益保全額、リスク帯移行など業務に合うKPIを採用
- 学習と検証の分離、機密データ不使用、仮定と限界の明示により、金融・大企業で重要な統制を意識

## Quick start（Windows）

1. [Python 3.11+](https://www.python.org/downloads/) をインストールします。インストール画面で **Add Python to PATH** を選びます。
2. `setup_windows.bat` をダブルクリックします（初回のみ）。
3. `run_all_windows.bat` をダブルクリックします。
4. 各プロジェクトの `outputs/summary.html` がブラウザで開きます。

コマンドを使う場合：

```bash
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python run_all.py
```

macOS / Linuxでは、仮想環境のPythonを `.venv/bin/python` に読み替えてください。

## Repository map

```text
.
├─ 01_transaction_risk/       # 異常検知・運用閾値
├─ 02_customer_profitability/ # SQL顧客マート・収益性・離反
├─ 03_credit_early_warning/   # 法人財務・早期警戒・ストレス
├─ docs/                      # 職務経歴書、面接、GitHub活用ガイド
├─ setup_windows.bat
├─ run_all_windows.bat
└─ run_all.py
```

## Positioning

このポートフォリオは、研究職レベルの新規アルゴリズムではなく、**Data Analyst / BI / DXデータ活用**で求められる、課題整理・データ加工・分析・可視化・関係者説明・改善運用の一連の力を示すものです。RPAによる工数削減、QAで培った再現性・検証観点、プロジェクト推進経験との接続を面接で説明できます。

## Important note

全データは固定乱数で生成した合成データです。実在する企業・顧客・審査結果を表さず、実際の不正検知、与信判断、顧客施策へそのまま使用できません。モデル結果よりも、分析設計・判断基準・再現性を評価対象としています。

