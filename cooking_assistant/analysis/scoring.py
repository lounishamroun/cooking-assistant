"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                   CALCUL DES SCORES BAYÉSIENS                                ║
╚══════════════════════════════════════════════════════════════════════════════╝

Module pour calculer les Q-Scores bayésiens et scores finaux.
Basé sur scripts/score_calculator.py
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
    Calcule le Q-Score bayésien et le score final pour toutes les recettes d'une saison.
    
    Étapes :
    1. Compter le nombre d'avis par recette dans la saison
    2. Calculer la note moyenne par recette (seulement rating > 0)
    3. Calculer le Q-Score bayésien avec régression vers la moyenne saisonnière
    4. Calculer le poids de popularité basé sur le nombre d'avis
    5. Multiplier Q-Score × Poids pour obtenir le Score Final
    
    Args:
        season_df: DataFrame filtré pour la saison
        season_mean: Note moyenne pour cette saison (float)
        params: Dictionnaire avec kb, kpop, gamma
        
    Returns:
        DataFrame avec colonnes : recipe_id, Q_Score_Bayesien, Poids_Popularite, Score_Final, etc.
    """
    # Nombre total d'avis dans cette saison (y compris rating=0)
    recipe_review_counts = season_df.groupby('recipe_id').size().reset_index(
        name='reviews_in_season'
    )
    
    # Note moyenne par recette (exclut rating=0)
    recipe_rating_means = season_df[season_df['rating'] > 0].groupby(
        'recipe_id'
    )['rating'].mean().reset_index(name='avg_rating')
    
    # Nombre d'avis VALIDES (rating > 0) - utilisé pour le calcul bayésien
    recipe_valid_counts = season_df[season_df['rating'] > 0].groupby(
        'recipe_id'
    ).size().reset_index(name='valid_reviews')
    
    # Fusionner toutes les métriques
    score_df = recipe_review_counts.merge(
        recipe_rating_means, on='recipe_id', how='left'
    ).merge(
        recipe_valid_counts, on='recipe_id', how='left'
    )
    
    # Remplir les valeurs manquantes (recettes sans notes valides)
    score_df['avg_rating'] = score_df['avg_rating'].fillna(0)
    score_df['valid_reviews'] = score_df['valid_reviews'].fillna(0)
    
    # Calculer le Q-Score bayésien
    score_df['Q_Score_Bayesien'] = (
        (score_df['avg_rating'] * score_df['valid_reviews'] + 
         season_mean * params['kb']) / 
        (score_df['valid_reviews'] + params['kb'])
    )
    
    # Calculer le poids de popularité
    score_df['Poids_Popularite'] = (
        1 - np.exp(-score_df['reviews_in_season'] / params['kpop'])
    ) ** params['gamma']
    
    # Calculer le score final
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
    Calcule le top N des recettes pour un type donné, par saison.
    
    Args:
        merged_df: DataFrame fusionné avec toutes les données
        recipes_df: DataFrame des recettes (pour obtenir les noms)
        recipe_type: Type de recette ('plat', 'dessert', 'boisson')
        params: Dictionnaire de paramètres (kb, kpop, gamma)
        season_order: Liste des saisons dans l'ordre d'affichage
        top_n: Nombre de recettes dans le top (défaut: 20)
        verbose: Afficher les informations de progression
        
    Returns:
        Dictionnaire {season: DataFrame} avec le top N par saison
    """
    if verbose:
        print(f"\n{'=' * 80}")
        print(f"CALCUL DU TOP {top_n} POUR : {recipe_type.upper()}")
        print(f"{'=' * 80}")
    
    # Filtrer les données pour ce type de recette
    type_df = merged_df[merged_df['type'] == recipe_type].copy()
    
    if len(type_df) == 0:
        print(f"⚠️  Aucune donnée pour le type '{recipe_type}'")
        return {}
    
    # Calculer la moyenne de référence pour chaque saison
    season_means = {}
    
    if verbose:
        print(f"\nMoyennes saisonnières de base :")
    
    for season in season_order:
        season_ratings = type_df[
            (type_df['season'] == season) & (type_df['rating'] > 0)
        ]['rating']
        
        if len(season_ratings) > 0:
            season_means[season] = season_ratings.mean()
        else:
            # Fallback sur la moyenne globale du type
            season_means[season] = type_df[type_df['rating'] > 0]['rating'].mean()
        
        if verbose:
            print(f"   {season:12s} : {season_means[season]:.4f}")
    
    # Calculer les scores pour chaque saison
    top_n_by_season = {}
    
    if verbose:
        print(f"\n🏆 Calcul des tops par saison :")
    
    for season in season_order:
        season_df = type_df[type_df['season'] == season]
        
        if len(season_df) == 0:
            if verbose:
                print(f"   {season:12s} : Aucune donnée")
            continue
        
        # Calculer les scores
        scores_df = calculate_bayesian_scores(
            season_df=season_df,
            season_mean=season_means[season],
            params=params
        )
        
        # Ajouter les noms de recettes
        scores_df = scores_df.merge(
            recipes_df[['id', 'name']],
            left_on='recipe_id',
            right_on='id',
            how='left'
        ).drop(columns=['id'])
        
        # Ajouter la colonne saison
        scores_df['Saison'] = season
        
        # Trier par score final et garder le top N
        top_n_df = scores_df.sort_values(
            'Score_Final', ascending=False
        ).head(top_n)
        
        # Stocker dans le dictionnaire
        top_n_by_season[season] = top_n_df
        
        # Afficher le résumé
        if verbose:
            print(f"   {season:12s} : Top {len(top_n_df)} calculé")
            print(f"                   Meilleur score : {top_n_df['Score_Final'].max():.4f}")
            print(f"                   Score médian   : {top_n_df['Score_Final'].median():.4f}")
    
    if verbose:
        print(f"\n{'=' * 80}")
        print(f"Calcul terminé pour {recipe_type}")
        print(f"{'=' * 80}\n")
    
    return top_n_by_season


if __name__ == "__main__":
    print("Module de calcul des scores bayésiens")
    print("Utilisez ce module via les scripts ou l'API")
