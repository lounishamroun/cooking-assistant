"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                      BAYESIAN SCORE CALCULATION                              ║
╚══════════════════════════════════════════════════════════════════════════════╝

This module contains functions to calculate Bayesian Q-Scores and final
scores for each recipe.
"""

import numpy as np


def calculate_scores_for_season(season_df, season_mean, params):
    """
    Calculates Bayesian Q-Score and final score for all recipes
    in a given season.
    
    Args:
        season_df: DataFrame of reviews for this season
        season_mean: Season average rating
        params: Parameters (kb, kpop, gamma)
    
    STEPS:
    ------
    1. Count number of reviews per recipe in the season
    2. Calculate average rating per recipe (only ratings > 0)
    3. Calculate Bayesian Q-Score with regression toward season mean
    4. Calculate popularity weight based on number of reviews
    5. Multiply Q-Score * Weight to get Final Score
    
    Args:
        season_df: DataFrame filtered for the season
        all_type_df: Complete DataFrame for the recipe type
        season_mean: Average rating for this season (float)
        params: Dict with kb, kpop, gamma
        
    Returns:
        pd.DataFrame: DataFrame with columns recipe_id, Q_Score_Bayesien,
                      Poids_Popularite, Score_Final, etc.
    """
    #The choice of bayesian parameters, treatment of ratings=0, choice of
    # having a same set of parameters for each season by recipe type
    # is explained in the Readme file of the folder bayesian_parameters_justification.
    
    # Total number of reviews in this season (including rating=0)
    recipe_review_counts = season_df.groupby('recipe_id').size().reset_index(
        name='reviews_in_season'
    )
    
    # Average rating per recipe (excludes ratings=0)
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
    
    # Calculate Popularity Weight
    score_df['Poids_Popularite'] = (
        1 - np.exp(-score_df['reviews_in_season'] / params['kpop'])
    ) ** params['gamma']
    
    
    # Calculate Final Score
    score_df['Score_Final'] = (
        score_df['Q_Score_Bayesien'] * score_df['Poids_Popularite']
    )
    
    return score_df


def calculate_top_n_by_type(merged_df, recipes_df, recipe_type, params, season_order, top_n=20):
    """
    Calculates the top N recipes for a given type, by season.
    
    Args:
        merged_df: Merged DataFrame with all data
        recipes_df: Recipes DataFrame (to get names)
        recipe_type: Recipe type (plat, dessert, boisson)
        params: Parameters dictionary (kb, kpop, gamma)
        season_order: List of seasons in display order
        top_n: Choice of top n performed (default: 20)
        
    Returns:
        dict: Dictionary {season: DataFrame} with top N by season
    """
    # Filter data for this recipe type
    type_df = merged_df[merged_df['type'] == recipe_type].copy()
    
    # Calculate baseline average for each season
    season_means = {}
    
    for season in season_order:
        season_ratings = type_df[
            (type_df['season'] == season) & (type_df['rating'] > 0)
        ]['rating']
        
        if len(season_ratings) > 0:
            season_means[season] = season_ratings.mean()
        else:
            season_means[season] = type_df[type_df['rating'] > 0]['rating'].mean()
        
        print(f"{season:12s}: {season_means[season]:.4f}")
    
    # Calculate scores for each season
    top_n_by_season = {}
    
    for season in season_order:
        
        season_df = type_df[type_df['season'] == season]
        
        if len(season_df) == 0:
            print(f"No data for season {season}")
            continue
        
        # Calculate scores
        scores_df = calculate_scores_for_season(
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
        print(f"Top {top_n} calculated for {season}")
        print(f"• Best score: {top_n_df['Score_Final'].max():.4f}")
        print(f"• Median score: {top_n_df['Score_Final'].median():.4f}")

    return top_n_by_season
