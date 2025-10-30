"""
BAYESIAN SCORES CALCULATION

Module to calculate Bayesian Q-Scores and final scores.
Based on scripts/score_calculator.py
"""

import numpy as np
import pandas as pd
from typing import Dict, List

from ..config import BAYESIAN_PARAMS, SEASON_ORDER, TOP_N


def calculate_bayesian_scores(
    season_df: pd.DataFrame,
    season_mean: float,
    params: Dict[str, float]
) -> pd.DataFrame:
    """
    Calculates Bayesian Q-Score and final score for all recipes in a season.
    
    Steps:
    1. Count number of reviews per recipe in the season
    2. Calculate average rating per recipe (only rating > 0)
    3. Calculate Bayesian Q-Score with regression to seasonal mean
    4. Calculate popularity weight based on number of reviews
    5. Multiply Q-Score × Weight to get Final Score
    
    Args:
        season_df: DataFrame filtered for the season
        season_mean: Average rating for this season (float)
        params: Dictionary with kb, kpop, gamma
        
    Returns:
        DataFrame with columns: recipe_id, Q_Score_Bayesien, Poids_Popularite, Score_Final, etc.
    """
    # Total number of reviews in this season (including rating=0)
    recipe_review_counts = season_df.groupby('recipe_id').size().reset_index(
        name='reviews_in_season'
    )
    
    # Average rating per recipe (excludes rating=0)
    recipe_rating_means = season_df[season_df['rating'] > 0].groupby(
        'recipe_id'
    )['rating'].mean().reset_index(name='avg_rating')
    
    # Number of VALID reviews (rating > 0) - used for Bayesian calculation
    recipe_valid_counts = season_df[season_df['rating'] > 0].groupby(
        'recipe_id'
    ).size().reset_index(name='valid_reviews')
    
    # Merge all metrics
    score_df = recipe_review_counts.merge(
        recipe_rating_means, on='recipe_id', how='left'
    ).merge(
        recipe_valid_counts, on='recipe_id', how='left'
    )
    
    # Fill missing values (recipes without valid ratings)
    score_df['avg_rating'] = score_df['avg_rating'].fillna(0)
    score_df['valid_reviews'] = score_df['valid_reviews'].fillna(0)
    
    # Calculate Bayesian Q-Score
    score_df['Q_Score_Bayesien'] = (
        (score_df['avg_rating'] * score_df['valid_reviews'] + 
         season_mean * params['kb']) / 
        (score_df['valid_reviews'] + params['kb'])
    )
    
    # Calculate popularity weight
    score_df['Poids_Popularite'] = (
        1 - np.exp(-score_df['reviews_in_season'] / params['kpop'])
    ) ** params['gamma']
    
    # Calculate final score
    score_df['Score_Final'] = (
        score_df['Q_Score_Bayesien'] * score_df['Poids_Popularite']
    )
    
    return score_df


def calculate_top_n_by_type(
    merged_df: pd.DataFrame,
    recipes_df: pd.DataFrame,
    recipe_type: str,
    params: Dict[str, float],
    season_order: List[str] = SEASON_ORDER,
    top_n: int = TOP_N,
    verbose: bool = True
) -> Dict[str, pd.DataFrame]:
    """
    Calculates top N recipes for a given type, by season.
    
    Args:
        merged_df: Merged DataFrame with all data
        recipes_df: Recipes DataFrame (to get names)
        recipe_type: Recipe type ('plat', 'dessert', 'boisson')
        params: Parameter dictionary (kb, kpop, gamma)
        season_order: List of seasons in display order
        top_n: Number of recipes in top (default: 20)
        verbose: Display progress information
        
    Returns:
        Dictionary {season: DataFrame} with top N by season
    """
    if verbose:
        print(f"\n{'=' * 80}")
        print(f"CALCULATING TOP {top_n} FOR: {recipe_type.upper()}")
        print(f"{'=' * 80}")
    
    # Filter data for this recipe type
    type_df = merged_df[merged_df['type'] == recipe_type].copy()
    
    if len(type_df) == 0:
        print(f"⚠️  No data for type '{recipe_type}'")
        return {}
    
    # Calculate reference average for each season
    season_means = {}
    
    if verbose:
        print(f"\nSeasonal baseline averages:")
    
    for season in season_order:
        season_ratings = type_df[
            (type_df['season'] == season) & (type_df['rating'] > 0)
        ]['rating']
        
        if len(season_ratings) > 0:
            season_means[season] = season_ratings.mean()
        else:
            # Fallback to global type average
            season_means[season] = type_df[type_df['rating'] > 0]['rating'].mean()
        
        if verbose:
            print(f"   {season:12s} : {season_means[season]:.4f}")
    
    # Calculate scores for each season
    top_n_by_season = {}
    
    if verbose:
        print(f"\n🏆 Calculating tops by season:")
    
    for season in season_order:
        season_df = type_df[type_df['season'] == season]
        
        if len(season_df) == 0:
            if verbose:
                print(f"   {season:12s} : No data")
            continue
        
        # Calculate scores
        scores_df = calculate_bayesian_scores(
            season_df=season_df,
            season_mean=season_means[season],
            params=params
        )
        
        # Add recipe names
        scores_df = scores_df.merge(
            recipes_df[['id', 'name']],
            left_on='recipe_id',
            right_on='id',
            how='left'
        ).drop(columns=['id'])
        
        # Add season column
        scores_df['Saison'] = season
        
        # Sort by final score and keep top N
        top_n_df = scores_df.sort_values(
            'Score_Final', ascending=False
        ).head(top_n)
        
        # Store in dictionary
        top_n_by_season[season] = top_n_df
        
        # Display summary
        if verbose:
            print(f"   {season:12s} : Top {len(top_n_df)} calculated")
            print(f"                   Best score    : {top_n_df['Score_Final'].max():.4f}")
            print(f"                   Median score  : {top_n_df['Score_Final'].median():.4f}")
    
    if verbose:
        print(f"\n{'=' * 80}")
        print(f"Calculation completed for {recipe_type}")
        print(f"{'=' * 80}\n")
    
    return top_n_by_season


if __name__ == "__main__":
    print("Bayesian scores calculation module")
    print("Use this module via scripts or API")
