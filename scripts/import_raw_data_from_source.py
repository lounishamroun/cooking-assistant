import kagglehub
from kagglehub import KaggleDatasetAdapter
from pathlib import Path
from datetime import datetime
import shutil
import logging

logging.basicConfig(
    filename="data_set_download.log",
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)
file_path = "RAW_recipes.csv"
try:
    df = kagglehub.load_dataset(
        KaggleDatasetAdapter.PANDAS,
        "shuyangli94/food-com-recipes-and-user-interactions",
        file_path,
    )
    print("First 5 records:", df.head())
    logger.info("Loaded %s via kagglehub.load_dataset()", file_path)
except Exception as e:
    logger.error("Failed to load %s: %s", file_path, e)

HANDLE = "shuyangli94/food-com-recipes-and-user-interactions"
try:
    res = kagglehub.dataset_download(HANDLE)
    local_path = res[0] if isinstance(res, (tuple, list)) else res
    local_dir = Path(local_path)

    if not local_dir.exists():
        raise FileNotFoundError(f"Downloaded path not found: {local_dir}")

    logger.info("Downloaded dataset '%s' to %s", HANDLE, local_dir)
except Exception as e:
    logger.error("Couldn't download the dataset '%s': %s", HANDLE, e)
    raise  

ts = datetime.now().strftime("%Y%m%d-%H%M%S")
raw_dir = Path("data/raw")
raw_dir.mkdir(parents=True, exist_ok=True)
src_files = [local_dir] if local_dir.is_file() else [p for p in local_dir.iterdir() if p.is_file()]

if not src_files:
    logger.warning("No files found to copy from %s", local_dir)

for p in src_files:
    dst = raw_dir / f"{p.stem}_{ts}{p.suffix}"
    shutil.copy2(p, dst)
    print(f"Saved -> {dst}")
    logger.info("Saved -> %s", dst)
