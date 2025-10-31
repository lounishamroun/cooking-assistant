"""Kaggle dataset downloader.

Provides a timestamped acquisition routine for the Food.com dataset. If a
timestamped copy (or base file) already exists the download step is skipped
to keep runs idempotent. Automatically handles cache corruption by forcing
redownload.
"""

from pathlib import Path
from datetime import datetime
import pandas as pd
import kagglehub
from kagglehub import KaggleDatasetAdapter
from kagglehub.exceptions import DataCorruptionError

# Support running as both package (python -m cooking_assistant.data.downloader)
# and as a standalone script (python cooking_assistant/data/downloader.py).
try:
    from ..config import RAW_DATA_DIR  # package-relative
except ImportError:
    import sys
    from pathlib import Path as _Path
    # Add project root to path so absolute import works
    _ROOT = _Path(__file__).resolve().parents[2]
    if str(_ROOT) not in sys.path:
        sys.path.insert(0, str(_ROOT))
    from cooking_assistant.config import RAW_DATA_DIR  # absolute fallback

HANDLE = "shuyangli94/food-com-recipes-and-user-interactions"
RAW_DIR = RAW_DATA_DIR  # Use centralized configuration
FILES = ["RAW_recipes.csv", "RAW_interactions.csv"]

def has_any_timestamped_copy(stem: str) -> bool:
    return any(RAW_DIR.glob(f"{stem}_*.csv")) or any(RAW_DIR.glob(f"{stem}.csv"))

def main():
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")

    for fname in FILES:
        stem = Path(fname).stem                              # e.g., "RAW_recipes"
        out = RAW_DIR / f"{stem}_{ts}.csv"                  # RAW_recipes<ts>.csv

        # Skip if any copy already exists (timestamped or not)
        if has_any_timestamped_copy(stem):
            print(f"Already present, skip: {stem}")
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