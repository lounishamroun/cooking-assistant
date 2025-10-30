"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                   PRÉTRAITEMENT ET FUSION DES DONNÉES                        ║
╚══════════════════════════════════════════════════════════════════════════════╝

Module pour fusionner les recettes avec les interactions et ajouter les saisons.
Basé sur scripts/data_loader_preparation.py
"""

import pandas as pd
from typing import Optional

from ..analysis.seasonal import get_season_from_date


def prepare_merged_data(
    recipes_df: pd.DataFrame,
    interactions_df: pd.DataFrame,
    verbose: bool = True
) -> pd.DataFrame:
    """
    Fusionne les recettes avec les interactions et ajoute la colonne 'season'.
    
    Args:
        recipes_df: DataFrame des recettes (doit contenir 'id', 'name', 'type')
        interactions_df: DataFrame des interactions (doit contenir 'recipe_id', 'rating', 'date')
        verbose: Afficher les informations de progression
        
    Returns:
        DataFrame fusionné avec colonnes : recipe_id, name, type, rating, date, season, year
    """
    if verbose:
        print("\n" + "=" * 80)
        print("PRÉPARATION DES DONNÉES")
        print("=" * 80)
    
    # Vérifier que les colonnes nécessaires existent
    required_recipe_cols = ['id', 'name', 'type']
    required_interaction_cols = ['recipe_id', 'rating', 'date']
    
    missing_recipe = [col for col in required_recipe_cols if col not in recipes_df.columns]
    missing_interaction = [col for col in required_interaction_cols if col not in interactions_df.columns]
    
    if missing_recipe:
        raise ValueError(f"Colonnes manquantes dans recipes_df : {missing_recipe}")
    if missing_interaction:
        raise ValueError(f"Colonnes manquantes dans interactions_df : {missing_interaction}")
    
    # Fusionner les recettes avec les interactions
    if verbose:
        print("\n1️⃣  Fusion des recettes avec les interactions...")
    
    merged_df = interactions_df.merge(
        recipes_df[['id', 'name', 'type']],
        left_on='recipe_id',
        right_on='id',
        how='left'
    )
    
    if verbose:
        print(f"   ✓ {len(merged_df):,} lignes après fusion")
    
    # Convertir les dates et ajouter la saison
    if verbose:
        print("\n2️⃣  Conversion des dates et calcul des saisons...")
    
    merged_df['date_parsed'] = pd.to_datetime(merged_df['date'], errors='coerce')
    merged_df['season'] = merged_df['date_parsed'].apply(get_season_from_date)
    merged_df['year'] = merged_df['date_parsed'].dt.year
    
    if verbose:
        print("   ✓ Saisons ajoutées")
    
    # Afficher les statistiques par type
    if verbose:
        print("\nDistribution par type de recette :")
        type_counts = merged_df['type'].value_counts().sort_index()
        for recipe_type, count in type_counts.items():
            percentage = (count / len(merged_df)) * 100
            print(f"   • {recipe_type:10s} : {count:>8,} avis ({percentage:>5.2f}%)")
    
    # Afficher les statistiques par saison
    if verbose:
        print("\nDistribution par saison :")
        season_counts = merged_df['season'].value_counts()
        for season in ['Spring', 'Summer', 'Fall', 'Winter']:
            count = season_counts.get(season, 0)
            percentage = (count / len(merged_df)) * 100 if len(merged_df) > 0 else 0
            print(f"   • {season:10s} : {count:>8,} avis ({percentage:>5.2f}%)")
        
        unknown = season_counts.get('Unknown', 0)
        if unknown > 0:
            print(f"   • {'Unknown':10s} : {unknown:>8,} avis")
    
    if verbose:
        print("\n" + "=" * 80)
        print(f"Préparation terminée : {len(merged_df):,} lignes fusionnées")
        print("=" * 80 + "\n")
    
    return merged_df


if __name__ == "__main__":
    # Test du module
    from .loader import load_data
    
    recipes, interactions = load_data()
    merged = prepare_merged_data(recipes, interactions)
    
    print("\nTest de préparation réussi!")
    print(f"   Colonnes : {list(merged.columns)}")
    print(f"   Shape : {merged.shape}")
