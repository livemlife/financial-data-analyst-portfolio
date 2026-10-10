from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
PROJECTS = [
    ROOT / "01_transaction_risk" / "run_analysis.py",
    ROOT / "02_customer_profitability" / "run_analysis.py",
    ROOT / "03_credit_early_warning" / "run_analysis.py",
]


def main() -> int:
    print("Enterprise Data Analyst Portfolio - running all projects")
    for script in PROJECTS:
        print(f"\n[RUN] {script.parent.name}")
        completed = subprocess.run([sys.executable, str(script)], cwd=script.parent)
        if completed.returncode != 0:
            print(f"[FAILED] {script.parent.name}")
            return completed.returncode
        print(f"[OK] {script.parent.name}")
    verification = subprocess.run([sys.executable, str(ROOT / "verify_outputs.py")], cwd=ROOT)
    if verification.returncode != 0:
        return verification.returncode
    print("\nAll projects completed. Open each project's outputs/summary.html.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
