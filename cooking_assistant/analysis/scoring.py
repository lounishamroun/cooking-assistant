"""Bayesian scoring utilities.

Implements the shrinkage quality score (Q-Score) and combined popularity
adjusted final score used for seasonal top rankings.
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
    """Compute Q-Score, popularity weight and final score for a season slice.

    Parameters
    ----------
    season_df : pd.DataFrame
        Interaction rows for a single season (must include ``recipe_id`` and
        ``rating`` columns).
    season_mean : float
        Baseline average rating for the season and recipe type.
    params : Dict[str, float]
        Bayesian parameters: ``kb`` (shrinkage strength), ``kpop`` (popularity
        saturation scale), ``gamma`` (popularity exponent).

    Returns
    -------
    pd.DataFrame
        One row per recipe with columns ``reviews_in_season``, ``avg_rating``,
        ``valid_reviews``, ``Q_Score_Bayesien``, ``Poids_Popularite``, ``Score_Final``.
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
    """Produce per-season top-N ranking for a given recipe type.

    Parameters
    ----------
    merged_df : pd.DataFrame
        Full merged interactions dataset including ``season`` & ``type``.
    recipes_df : pd.DataFrame
        Recipe catalog for name lookup (columns ``id``, ``name``).
    recipe_type : str
        One of the values in ``RECIPE_TYPES``.
    params : Dict[str, float]
        Bayesian parameter set for this recipe type.
    season_order : List[str], default ``SEASON_ORDER``
        Ordering used to iterate and display seasons.
    top_n : int, default ``TOP_N``
        Number of recipes kept per season after sorting by final score.
    verbose : bool, default True
        When True prints intermediate progress and summaries.

    Returns
    -------
    Dict[str, pd.DataFrame]
        Mapping season → DataFrame of top-N scored recipes.
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
