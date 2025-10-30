"""
CSV DATA LOADING

Module to load CSV files (recipes, interactions, classifications).
Based on scripts/data_loader_preparation.py
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
    """
    Loads the raw recipes file (RAW_recipes_*.csv).
    
    Args:
        data_dir: Directory containing raw data
        
    Returns:
        DataFrame with recipes
        
    Raises:
        FileNotFoundError: If no recipes file is found
    """
    recipes_file = get_latest_file_with_prefix(RAW_RECIPES_PREFIX, data_dir)
    
    print(f"Loading recipes from: {recipes_file.name}")
    df = pd.read_csv(recipes_file, encoding='utf-8')
    print(f"   ✓ {len(df):,} recipes loaded")
    
    return df


def load_interactions(data_dir: Path = RAW_DATA_DIR) -> pd.DataFrame:
    """
    Loads the interactions/reviews file (RAW_interactions_*.csv).
    
    Args:
        data_dir: Directory containing raw data
        
    Returns:
        DataFrame with interactions (reviews)
        
    Raises:
        FileNotFoundError: If no interactions file is found
    """
    interactions_file = get_latest_file_with_prefix(RAW_INTERACTIONS_PREFIX, data_dir)
    
    print(f"Loading interactions from: {interactions_file.name}")
    df = pd.read_csv(interactions_file, encoding='utf-8')
    print(f"   ✓ {len(df):,} interactions loaded")
    
    return df


def load_classified_recipes(file_path: Path = RECIPES_CLASSIFIED_FILE) -> pd.DataFrame:
    """
    Loads the classified recipes file (with 'type' column).
    
    Args:
        file_path: Path to the classified recipes file
        
    Returns:
        DataFrame with classified recipes
        
    Raises:
        FileNotFoundError: If the file doesn't exist
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
    """
    Loads both recipes and interactions.
    
    Args:
        data_dir: Directory containing the data
        
    Returns:
        Tuple (recipes_df, interactions_df)
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
