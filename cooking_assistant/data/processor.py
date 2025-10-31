"""Data merging and seasonal enrichment.

This module provides a single helper ``prepare_merged_data`` that joins the
recipes dataset with interactions, parses review dates safely, adds a
season label (astronomical seasons) and extracts the review year.

The function performs lightweight validation of required columns and can
emit progress information for exploratory runs. It never mutates the input
DataFrames in-place.
"""

import pandas as pd
from typing import Optional

from ..analysis.seasonal import get_season_from_date


def prepare_merged_data(
    recipes_df: pd.DataFrame,
    interactions_df: pd.DataFrame,
    verbose: bool = True
) -> pd.DataFrame:
    """Merge recipes with interactions and enrich with seasonal metadata.

    The merged output contains one row per interaction joined to its
    corresponding recipe attributes. Review timestamps are converted to
    ``datetime64[ns]`` (coercing invalid values to ``NaT``), then mapped
    to seasons via :func:`cooking_assistant.analysis.seasonal.get_season_from_date`.

    Parameters
    ----------
    recipes_df : pd.DataFrame
        Must include columns ``id``, ``name``, ``type``.
    interactions_df : pd.DataFrame
        Must include columns ``recipe_id``, ``rating``, ``date``.
    verbose : bool, default True
        When True, prints progress and distribution summaries.

    Returns
    -------
    pd.DataFrame
        Columns (at minimum): ``recipe_id``, ``name``, ``type``, ``rating``,
        ``date``, ``date_parsed``, ``season``, ``year``. Additional columns
        from the interactions input are preserved.

    Raises
    ------
    ValueError
        If required columns are missing in either input DataFrame.
    """
    if verbose:
        print("DATA PREPARATION")
        print("=" * 40)
    
    # Check that required columns exist
    required_recipe_cols = ['id', 'name', 'type']
    required_interaction_cols = ['recipe_id', 'rating', 'date']
    
    missing_recipe = [col for col in required_recipe_cols if col not in recipes_df.columns]
    missing_interaction = [col for col in required_interaction_cols if col not in interactions_df.columns]
    
    if missing_recipe:
        raise ValueError(f"Missing columns in recipes_df: {missing_recipe}")
    if missing_interaction:
        raise ValueError(f"Missing columns in interactions_df: {missing_interaction}")
    
    # Merge recipes with interactions
    if verbose:
        print("\n Merging recipes with interactions")
    
    merged_df = interactions_df.merge(
        recipes_df[['id', 'name', 'type']],
        left_on='recipe_id',
        right_on='id',
        how='left'
    )
    
    if verbose:
        print(f"{len(merged_df):,} rows after merge")
    
    # Convert dates and add season
    if verbose:
        print("\n2 Converting dates and calculating seasons")
    
    merged_df['date_parsed'] = pd.to_datetime(merged_df['date'], errors='coerce')
    merged_df['season'] = merged_df['date_parsed'].apply(get_season_from_date)
    merged_df['year'] = merged_df['date_parsed'].dt.year
    
    if verbose:
        print("Seasons added")
    
    # Display statistics by type
    if verbose:
        print("\nDistribution by recipe type:")
        type_counts = merged_df['type'].value_counts().sort_index()
        for recipe_type, count in type_counts.items():
            percentage = (count / len(merged_df)) * 100
            print(f"   • {recipe_type:10s} : {count:>8,} reviews ({percentage:>5.2f}%)")
    
    # Display statistics by season
    if verbose:
        print("\nDistribution by season:")
        season_counts = merged_df['season'].value_counts()
        for season in ['Spring', 'Summer', 'Fall', 'Winter']:
            count = season_counts.get(season, 0)
            percentage = (count / len(merged_df)) * 100 if len(merged_df) > 0 else 0
            print(f"   • {season:10s} : {count:>8,} reviews ({percentage:>5.2f}%)")
        
        unknown = season_counts.get('Unknown', 0)
        if unknown > 0:
            print(f"   • {'Unknown':10s} : {unknown:>8,} reviews")
    
    if verbose:
        print("\n" + "=" * 80)
        print(f"Preparation completed: {len(merged_df):,} merged rows")
        print("=" * 80 + "\n")
    
    return merged_df


if __name__ == "__main__":
    # Test module
    from .loader import load_data
    
    recipes, interactions = load_data()
    merged = prepare_merged_data(recipes, interactions)
    
    print("\nPreparation test successful!")
    print(f"Columns: {list(merged.columns)}")
    print(f"Shape: {merged.shape}")
