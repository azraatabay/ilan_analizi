import os
import glob
import pandas as pd

KLASOR = os.path.dirname(os.path.abspath(__file__))
MASAUSTU = os.path.dirname(KLASOR)   # Desktop

ATLA = ("venv", "node_modules", "chrome_profil", ".git")

for yol in glob.glob(os.path.join(MASAUSTU, "**", "*.csv"), recursive=True):
    if any(a in yol for a in ATLA):
        continue
    d = None
    for sep in [",", ";"]:
        try:
            d = pd.read_csv(yol, sep=sep, encoding="utf-8-sig")
        except Exception:
            continue
        if "metin" in d.columns:
            break
        d = None
    if d is not None:
        print(f"{len(d):>4} satır | {'kaynak' in d.columns and 'kaynak VAR' or 'kaynak yok'} | {yol}")
        print("       sütunlar:", list(d.columns))