"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                      TÉLÉCHARGEMENT DES DONNÉES                              ║
╚══════════════════════════════════════════════════════════════════════════════╝

Module pour télécharger les données depuis Kaggle.
"""

from pathlib import Path
from datetime import datetime
import pandas as pd
import kagglehub
from kagglehub import KaggleDatasetAdapter
from kagglehub.exceptions import DataCorruptionError

HANDLE = "shuyangli94/food-com-recipes-and-user-interactions"
RAW_DIR = Path("data/raw")
FILES = ["RAW_recipes.csv", "RAW_interactions.csv"]

def has_any_timestamped_copy(stem: str) -> bool:
    return any(RAW_DIR.glob(f"{stem}_*.csv"))

def main():
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")

    for fname in FILES:
        stem = Path(fname).stem                              # e.g., "RAW_recipes"
        out = RAW_DIR / f"{stem}{ts}.csv"                  # RAW_recipes<ts>.csv

        # Skip if any timestamped copy already exists
        if has_any_timestamped_copy(stem):
            print(f"Already present (timestamped copy exists), skip: {stem}_*.csv")
            continue

        try:
            # Light path: fetch just this file and save it with timestamp
            df = kagglehub.load_dataset(KaggleDatasetAdapter.PANDAS, HANDLE, fname)
            df.to_csv(out, index=False)
            print(f"Saved -> {out}")

        except DataCorruptionError:
            # Force-refresh the dataset cache, then read .csv or .csv.gz directly
            print("Cache corrupted. Redownloading dataset cache…")
            res = kagglehub.dataset_download(HANDLE, force_download=True)
            dpath = Path(res[0]) if isinstance(res, (tuple, list)) else Path(res)

            src_csv = dpath / fname
            gz_csv  = dpath / f"{fname}.gz"

            if src_csv.exists():
                pd.read_csv(src_csv).to_csv(out, index=False)
                print(f"Saved -> {out}")
            elif gz_csv.exists():
                pd.read_csv(gz_csv).to_csv(out, index=False)  # re-save plain CSV
                print(f"Saved -> {out}")
            else:
                raise FileNotFoundError(f"Could not find {fname} in {dpath}")

if __name__ == "__main__":
    main()