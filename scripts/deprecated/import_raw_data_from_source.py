import kagglehub
from kagglehub import KaggleDatasetAdapter
from pathlib import Path
from datetime import datetime
import shutil
import logging


# -----------------------------------------------------------------------------
# Logging configuration
# We log to a file called "data_set_download.log" so we can trace what happened
# during data loading without spamming the console.
# -----------------------------------------------------------------------------
logging.basicConfig(
    filename="data_set_download.log",
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


# -----------------------------------------------------------------------------
# Constants
# HANDLE      : the Kaggle dataset ID we want to download
# RAW_DIR     : where we want to store our raw data inside this project
# -----------------------------------------------------------------------------
HANDLE = "shuyangli94/food-com-recipes-and-user-interactions"
RAW_DIR = Path("data/raw")


# -----------------------------------------------------------------------------
# Main logic
# This script is meant to be run once at project setup.
# - If data/raw already contains files, we assume the dataset is already synced
#   and we do nothing (we DO NOT download again).
# - Otherwise, we download the dataset with kagglehub, and copy the files into
#   data/raw, adding a timestamp to each filename.
#
# Why timestamp?
#   To "freeze" the raw source we used in this project (source of truth).
#   Later preprocessing can read from these timestamped copies.
# -----------------------------------------------------------------------------

def ensure_raw_data_once() -> None:
    """
    Ensure that the raw dataset is available locally under data/raw.

    Behavior:
    - If data/raw already exists AND is not empty:
        -> Do nothing (we skip re-download to avoid duplicates).
    - Else:
        -> Download the dataset from Kaggle (via kagglehub).
        -> Copy all files into data/raw with a timestamp suffix.
        -> Print and log what was saved.

    This function is idempotent for normal use: after first success,
    future calls will simply exit early.
    """

    # -------------------------------------------------------------------------
    # 1. If raw data already exists locally, skip everything.
    #    We treat what's in data/raw as the single source of truth
    #    for the rest of the project.
    # -------------------------------------------------------------------------
    if RAW_DIR.exists() and any(RAW_DIR.iterdir()):
        print(f"Raw data already present in {RAW_DIR}, skipping download.")
        logger.info("Raw data already present in %s, skipping download.", RAW_DIR)
        return

    # We got here, so either data/raw does not exist, or it's empty.
    # We'll download and stage the data now.

    # -------------------------------------------------------------------------
    # 2. (Optional sanity step)
    #    Try loading one known file ("RAW_recipes.csv") just to preview
    #    that kagglehub works. This is not critical to continue.
    # -------------------------------------------------------------------------
    file_path = "RAW_recipes.csv"
    try:
        df = kagglehub.load_dataset(
            KaggleDatasetAdapter.PANDAS,
            HANDLE,
            file_path,
        )
        print("First 5 records:", df.head())
        logger.info("Loaded %s via kagglehub.load_dataset()", file_path)
    except Exception as e:
        # We do not raise here, because even if preview fails,
        # the bulk dataset_download might still work.
        logger.error("Failed to load %s: %s", file_path, e)

    # -------------------------------------------------------------------------
    # 3. Download the full dataset using kagglehub.
    #    kagglehub.dataset_download() will:
    #      - download on the first call
    #      - return a cached path on later calls
    #    We handle both return shapes:
    #      * a string path
    #      * a (path, metadata) tuple/list
    # -------------------------------------------------------------------------
    try:
        res = kagglehub.dataset_download(HANDLE)

        # res can be either a single path-like value, or (path, metadata)
        local_path = res[0] if isinstance(res, (tuple, list)) else res
        local_dir = Path(local_path)

        if not local_dir.exists():
            raise FileNotFoundError(f"Downloaded path not found: {local_dir}")

        logger.info("Downloaded dataset '%s' to %s", HANDLE, local_dir)

    except Exception as e:
        # Here we *do* raise, because if the bulk download failed,
        # we do not have our data/raw and the project cannot continue.
        logger.error("Couldn't download the dataset '%s': %s", HANDLE, e)
        raise

    # -------------------------------------------------------------------------
    # 4. Prepare our destination folder (data/raw).
    #    We'll copy the original Kaggle files into this folder and
    #    add a timestamp into each filename so we "freeze" the snapshot.
    # -------------------------------------------------------------------------
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    # local_dir can be either:
    #   - a directory containing multiple files
    #   - a single file path
    if local_dir.is_file():
        src_files = [local_dir]
    else:
        src_files = [p for p in local_dir.iterdir() if p.is_file()]

    if not src_files:
        logger.warning("No files found to copy from %s", local_dir)

    # -------------------------------------------------------------------------
    # 5. Copy each file into data/raw, renaming it with the timestamp suffix.
    #    Example:
    #        RAW_recipes.csv  -> RAW_recipes_20251025-183000.csv
    # -------------------------------------------------------------------------
    for p in src_files:
        dst = RAW_DIR / f"{p.stem}_{timestamp}{p.suffix}"
        shutil.copy2(p, dst)
        print(f"Saved -> {dst}")
        logger.info("Saved -> %s", dst)


# -----------------------------------------------------------------------------
# Script entrypoint
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    ensure_raw_data_once()
