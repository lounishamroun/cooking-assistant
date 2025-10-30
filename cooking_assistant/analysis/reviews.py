"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                ANALYSE DES TOP RECETTES PAR NOMBRE D'AVIS                    ║
╚══════════════════════════════════════════════════════════════════════════════╝

Module pour analyser les recettes les plus commentées par type et saison.
Basé sur scripts/top_reviews_analyzer.py
"""

import pandas as pd
import os
from datetime import datetime
from typing import Dict, Optional

from ..config import RECIPE_TYPES, SEASONS, JUSTIFICATION_DIR


def analyze_top_reviews_by_type_season(
    merged_df: pd.DataFrame,
    recipes_df: pd.DataFrame,
    output_dir: str = str(JUSTIFICATION_DIR),
    top_n: int = 100,
    verbose: bool = True
) -> Dict:
    """
    Analyse les top N recettes par nombre d'avis pour chaque type et saison.
    Génère des fichiers CSV pour l'analyse de justification des paramètres.
    
    Args:
        merged_df: DataFrame fusionné avec interactions et types de recettes
        recipes_df: DataFrame avec les informations des recettes
        output_dir: Répertoire pour sauvegarder les CSV
        top_n: Nombre de top recettes à extraire (défaut: 100)
        verbose: Afficher les informations de progression
        
    Returns:
        Dictionnaire avec les résultats organisés par type et saison
    """
    if verbose:
        print(f"\n{'=' * 80}")
        print(f"ANALYSE DES TOP {top_n} RECETTES PAR NOMBRE D'AVIS")
        print(f"{'=' * 80}")
    
    # Créer le répertoire de sortie
    os.makedirs(output_dir, exist_ok=True)
    
    # Stockage des résultats
    all_results = []
    results_by_type_season = {}
    
    # Analyser chaque combinaison type × saison
    for recipe_type in RECIPE_TYPES:
        if verbose:
            print(f"\nAnalyse de {recipe_type.upper()}...")
        
        # Filtrer par type de recette
        type_df = merged_df[merged_df['type'] == recipe_type].copy()
        
        results_by_type_season[recipe_type] = {}
        
        for season in SEASONS:
            # Filtrer par saison
            season_df = type_df[type_df['season'] == season].copy()
            
            if len(season_df) == 0:
                if verbose:
                    print(f"   {season:10s} : Aucune donnée")
                continue
            
            # Compter les avis par recette (tous les avis y compris rating=0)
            total_reviews = season_df.groupby('recipe_id').size().reset_index(name='total_reviews')
            
            # Compter seulement les notes valides (rating > 0)
            valid_ratings = season_df[season_df['rating'] > 0].groupby('recipe_id').agg({
                'rating': ['count', 'mean']
            }).reset_index()
            valid_ratings.columns = ['recipe_id', 'valid_reviews', 'avg_valid_rating']
            
            # Fusionner avec les notes valides
            review_stats = total_reviews.merge(valid_ratings, on='recipe_id', how='left')
            
            # Remplir les valeurs manquantes
            review_stats['valid_reviews'] = review_stats['valid_reviews'].fillna(0)
            review_stats['avg_valid_rating'] = review_stats['avg_valid_rating'].fillna(0)
            
            # Ajouter les noms de recettes
            review_stats = review_stats.merge(
                recipes_df[['id', 'name']],
                left_on='recipe_id',
                right_on='id',
                how='left'
            ).drop(columns=['id'])
            
            # Ajouter les métadonnées
            review_stats['type'] = recipe_type
            review_stats['season'] = season
            
            # Trier par total d'avis et prendre le top N
            top_recipes = review_stats.sort_values('total_reviews', ascending=False).head(top_n)
            
            # Stocker les résultats
            results_by_type_season[recipe_type][season] = top_recipes
            all_results.append(top_recipes)
            
            if verbose:
                print(f"   {season:10s} : {len(top_recipes)} recettes extraites")
                print(f"                 Max avis : {top_recipes['total_reviews'].max()}")
                print(f"                 Min avis : {top_recipes['total_reviews'].min()}")
                print(f"                 Note moy : {top_recipes['avg_valid_rating'].mean():.3f}")
    
    # Combiner tous les résultats
    combined_results = pd.concat(all_results, ignore_index=True)
    
    # Analyse des médianes
    if verbose:
        print(f"\n{'=' * 80}")
        print(f"ANALYSE DES MÉDIANES (TOP {top_n})")
        print(f"{'=' * 80}")
    
    median_analysis = []
    
    for recipe_type in RECIPE_TYPES:
        if verbose:
            print(f"\n{recipe_type.upper()}")
        
        for season in SEASONS:
            season_type_data = combined_results[
                (combined_results['type'] == recipe_type) & 
                (combined_results['season'] == season)
            ]
            
            if len(season_type_data) > 0:
                median_reviews = season_type_data['total_reviews'].median()
                max_reviews = season_type_data['total_reviews'].max()
                min_reviews = season_type_data['total_reviews'].min()
                
                median_analysis.append({
                    'Type_Recette': recipe_type,
                    'Saison': season,
                    'Mediane_Reviews_Top100': median_reviews,
                    'Max_Reviews_Top100': max_reviews,
                    'Min_Reviews_Top100': min_reviews,
                    'Nb_Recettes_Analysees': len(season_type_data)
                })
                
                if verbose:
                    print(f"   {season:10s} : {median_reviews:6.0f} avis (médiane)")
            else:
                if verbose:
                    print(f"   {season:10s} : Aucune donnée")
    
    # Créer le DataFrame des médianes
    median_df = pd.DataFrame(median_analysis) if median_analysis else pd.DataFrame()
    
    # Fusionner les statistiques médianes avec les résultats combinés
    if not median_df.empty:
        median_df_merge = median_df.rename(columns={
            'Type_Recette': 'type',
            'Saison': 'season',
            'Mediane_Reviews_Top100': 'median_reviews_type_season',
            'Max_Reviews_Top100': 'max_reviews_type_season',
            'Min_Reviews_Top100': 'min_reviews_type_season',
            'Nb_Recettes_Analysees': 'nb_recipes_in_top'
        })
        
        combined_results = combined_results.merge(
            median_df_merge,
            on=['type', 'season'],
            how='left'
        )
        
        if verbose:
            print("\nStatistiques médianes ajoutées au fichier combiné")
    
    # Générer le timestamp pour le nom de fichier
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    combined_filename = f"top_{top_n}_reviews_by_type_season_{timestamp}.csv"
    combined_filepath = os.path.join(output_dir, combined_filename)
    
    # Réorganiser les colonnes pour meilleure lisibilité
    column_order = [
        'season', 'type', 'recipe_id', 'name', 'total_reviews', 'valid_reviews',
        'median_reviews_type_season'
    ]
    
    # S'assurer que toutes les colonnes existent
    available_columns = [col for col in column_order if col in combined_results.columns]
    combined_results = combined_results[available_columns]
    
    combined_results.to_csv(combined_filepath, index=False, encoding='utf-8')
    
    if verbose:
        print(f"\n{'=' * 80}")
        print(f"Résultats sauvegardés : {combined_filename}")
        print(f"   Emplacement : {output_dir}")
        print(f"   Total lignes : {len(combined_results):,}")
        print(f"{'=' * 80}\n")
    
    return {
        'combined_results': combined_results,
        'by_type_season': results_by_type_season,
        'median_analysis': median_df if not median_df.empty else None,
        'files_created': {
            'combined': combined_filepath
        }
    }


if __name__ == "__main__":
    print("Module d'analyse des tops par nombre d'avis")
    print("Utilisez ce module via les scripts ou l'API")
