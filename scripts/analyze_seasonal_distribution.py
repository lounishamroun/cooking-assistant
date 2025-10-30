"""
╔══════════════════════════════════════════════════════════════════════════════╗
║          ANALYSE DE LA DISTRIBUTION SAISONNIÈRE PAR TYPE                     ║
╚══════════════════════════════════════════════════════════════════════════════╝

Script pour analyser la distribution des avis par saison et type de recette.
Génère un CSV avec les statistiques pour la justification des paramètres.
"""

import sys
from pathlib import Path

# Ajouter le projet au path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import pandas as pd
from cooking_assistant.data import load_classified_recipes, load_interactions
from cooking_assistant.analysis import get_season_from_date
from cooking_assistant.config import RECIPE_TYPES, SEASONS, JUSTIFICATION_DIR


def analyze_seasonal_distribution(merged_df: pd.DataFrame = None) -> dict:
    """
    Analyse la distribution des avis par saison et type de recette.
    
    Args:
        merged_df: DataFrame pré-chargé avec colonnes season et type (optionnel)
    
    Returns:
        dict: Résultats de l'analyse avec clés 'total_reviews', 'results', 'filepath'
    """
    print("\n" + "=" * 80)
    print("ANALYSE DE LA DISTRIBUTION SAISONNIÈRE PAR TYPE")
    print("=" * 80)
    
    # Charger les données si non fournies
    if merged_df is None:
        print("\n📥 Chargement des données...")
        
        interactions_df = load_interactions()
        recipes_df = load_classified_recipes()
        
        print(f"   ✓ {len(interactions_df):,} interactions")
        print(f"   ✓ {len(recipes_df):,} recettes classifiées")
        
        # Nettoyer les interactions
        print("\n🔧 Nettoyage des données...")
        interactions_df['date'] = pd.to_datetime(interactions_df['date'], errors='coerce')
        interactions_df = interactions_df.dropna(subset=['date'])
        
        print(f"   ✓ {len(interactions_df):,} avis avec dates valides")
        
        # Ajouter les saisons
        print("\n🌸 Ajout des saisons...")
        interactions_df['season'] = interactions_df['date'].apply(get_season_from_date)
        
        # Fusionner avec les recettes
        print("\n🔗 Fusion des données...")
        merged_df = interactions_df.merge(
            recipes_df[['id', 'type']], 
            left_on='recipe_id',
            right_on='id',
            how='inner'
        )
        
        print(f"   ✓ {len(merged_df):,} avis avec type identifié")
    else:
        print("\n✓ Utilisation des données pré-chargées")
        print(f"  {len(merged_df):,} avis")
    
    # Calculer les distributions par type
    results = []
    total_all = len(merged_df)
    
    print("\n" + "=" * 80)
    print("DISTRIBUTION PAR TYPE DE RECETTE")
    print("=" * 80)
    
    for recipe_type in RECIPE_TYPES:
        type_data = merged_df[merged_df['type'] == recipe_type]
        total_type = len(type_data)
        percentage_of_total = (total_type / total_all * 100) if total_all > 0 else 0
        
        print(f"\n📊 {recipe_type.upper()} : {total_type:,} avis ({percentage_of_total:.1f}% du total)")
        print("-" * 80)
        
        for season in SEASONS:
            season_count = len(type_data[type_data['season'] == season])
            percentage_of_type = (season_count / total_type * 100) if total_type > 0 else 0
            
            results.append({
                'Type_Recette': recipe_type,
                'Saison': season,
                'Nombre_Reviews': season_count,
                'Pourcentage_du_Type': round(percentage_of_type, 2),
                'Pourcentage_du_Total': round((season_count / total_all * 100), 2)
            })
            
            print(f"   {season:10s} : {season_count:8,} avis ({percentage_of_type:5.1f}%)")
    
    # Créer le DataFrame des résultats
    results_df = pd.DataFrame(results)
    
    # Sauvegarder
    print("\n" + "=" * 80)
    print("💾 SAUVEGARDE DES RÉSULTATS")
    print("=" * 80)
    
    filename = "distribution_saisonniere_par_type.csv"
    filepath = JUSTIFICATION_DIR / filename
    
    # Créer le dossier si nécessaire
    JUSTIFICATION_DIR.mkdir(parents=True, exist_ok=True)
    
    results_df.to_csv(filepath, index=False, encoding='utf-8')
    
    print(f"\n✓ Fichier sauvegardé : {filename}")
    print(f"  📁 Emplacement : {JUSTIFICATION_DIR}")
    print(f"  📊 {len(results_df)} lignes")
    
    # Afficher un résumé global
    print("\n" + "=" * 80)
    print("RÉSUMÉ GLOBAL")
    print("=" * 80)
    print(f"\nTotal des avis analysés : {total_all:,}")
    
    for recipe_type in RECIPE_TYPES:
        type_total = results_df[results_df['Type_Recette'] == recipe_type]['Nombre_Reviews'].sum()
        percentage = (type_total / total_all * 100) if total_all > 0 else 0
        print(f"  • {recipe_type:10s} : {type_total:8,} ({percentage:5.1f}%)")
    
    print("\n" + "=" * 80)
    print("✅ ANALYSE TERMINÉE")
    print("=" * 80 + "\n")
    
    return {
        'total_reviews': total_all,
        'results': results,
        'filepath': str(filepath),
        'dataframe': results_df
    }


def main():
    """Point d'entrée du script."""
    try:
        analysis_results = analyze_seasonal_distribution()
        return 0
    except Exception as e:
        print(f"\n❌ Erreur : {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
