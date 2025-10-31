"""CSV loading utilities for core datasets.

Centralized helpers to retrieve the most recent timestamped raw recipe and
interaction files and the classified recipe file produced by the
multi‑signal classifier. All functions return new DataFrames and avoid
in-place mutation.
"""

import pandas as pd
from pathlib import Path
from typing import Tuple

from ..config import (
    RAW_DATA_DIR,
    INTERIM_DATA_DIR,
    RAW_RECIPES_PREFIX,
    RAW_INTERACTIONS_PREFIX,
    RECIPES_CLASSIFIED_FILE,
    get_latest_file_with_prefix
)


def load_recipes(data_dir: Path = RAW_DATA_DIR) -> pd.DataFrame:
    """Load the latest raw recipes CSV matching ``RAW_recipes*``.

    Parameters
    ----------
    data_dir : Path, default ``RAW_DATA_DIR``
        Directory containing raw timestamped files.

    Returns
    -------
    pd.DataFrame
        Raw recipes data.

    Raises
    ------
    FileNotFoundError
        If no matching file is found.
    """
    recipes_file = get_latest_file_with_prefix(RAW_RECIPES_PREFIX, data_dir)
    
    print(f"Loading recipes from: {recipes_file.name}")
    df = pd.read_csv(recipes_file, encoding='utf-8')
    print(f"   ✓ {len(df):,} recipes loaded")
    
    return df


def load_interactions(data_dir: Path = RAW_DATA_DIR) -> pd.DataFrame:
    """Load the latest raw interactions CSV matching ``RAW_interactions*``.

    Parameters
    ----------
    data_dir : Path, default ``RAW_DATA_DIR``
        Directory containing raw timestamped files.

    Returns
    -------
    pd.DataFrame
        User–recipe interaction records (ratings + metadata).

    Raises
    ------
    FileNotFoundError
        If no matching file is found.
    """
    interactions_file = get_latest_file_with_prefix(RAW_INTERACTIONS_PREFIX, data_dir)
    
    print(f"Loading interactions from: {interactions_file.name}")
    df = pd.read_csv(interactions_file, encoding='utf-8')
    print(f"   ✓ {len(df):,} interactions loaded")
    
    return df


def load_classified_recipes(file_path: Path = RECIPES_CLASSIFIED_FILE) -> pd.DataFrame:
    """Load the classifier output containing the ``type`` column.

    Parameters
    ----------
    file_path : Path, default ``RECIPES_CLASSIFIED_FILE``
        Location of the persisted classification output.

    Returns
    -------
    pd.DataFrame
        Recipes annotated with a final predicted type.

    Raises
    ------
    FileNotFoundError
        If the file does not exist.
    """
    if not file_path.exists():
        raise FileNotFoundError(
            f"Classified recipes file not found: {file_path}\n"
            "Please run the classification script first (01_classifier_generator.py)"
        )
    
    print(f"Loading classified recipes from: {file_path.name}")
    df = pd.read_csv(file_path, encoding='utf-8')
    print(f"   ✓ {len(df):,} classified recipes loaded")
    
    return df


def load_data(data_dir: Path = RAW_DATA_DIR) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Convenience wrapper returning recipes and interactions DataFrames.

    Parameters
    ----------
    data_dir : Path, default ``RAW_DATA_DIR``
        Directory in which raw timestamped files live.

    Returns
    -------
    (pd.DataFrame, pd.DataFrame)
        ``(recipes_df, interactions_df)``.
    """
    print("=" * 80)
    print("LOADING DATA")
    print("=" * 80)
    
    recipes_df = load_recipes(data_dir)
    interactions_df = load_interactions(data_dir)
    
    print()
    return recipes_df, interactions_df


if __name__ == "__main__":
    # Test loading
    recipes, interactions = load_data()
    print(f"\nTest successful!")
    print(f"   Recipes: {len(recipes)} rows")
    print(f"   Interactions: {len(interactions)} rows")
