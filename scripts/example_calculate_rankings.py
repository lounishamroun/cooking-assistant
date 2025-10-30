"""
╔══════════════════════════════════════════════════════════════════════════════╗
║          SCRIPT EXEMPLE : Calcul des Top 20 par Type et Saison              ║
╚══════════════════════════════════════════════════════════════════════════════╝

Ce script montre comment utiliser les modules cooking_assistant pour :
1. Charger les données
2. Calculer les top 20 par type et saison
3. Sauvegarder les résultats

Remplace progressivement les anciens scripts monolithiques.
"""

import sys
from pathlib import Path

# Ajouter le projet au path si nécessaire
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from cooking_assistant.data import (
    load_classified_recipes,
    load_interactions,
    prepare_merged_data
)
from cooking_assistant.analysis import calculate_top_n_by_type
from cooking_assistant.config import (
    BAYESIAN_PARAMS,
    RECIPE_TYPES,
    RESULTS_DIR,
    TOP_N
)


def main():
    """Point d'entrée principal du script."""
    
    print("=" * 80)
    print("CALCUL DES TOP 20 RECETTES PAR TYPE ET SAISON")
    print("=" * 80)
    
    # 1. Charger les données
    print("\n📥 Étape 1 : Chargement des données")
    print("-" * 80)
    
    try:
        recipes_df = load_classified_recipes()
        interactions_df = load_interactions()
    except FileNotFoundError as e:
        print(f"\n❌ Erreur : {e}")
        print("\n💡 Conseil : Exécutez d'abord :")
        print("   1. python scripts/import_raw_data_from_source.py")
        print("   2. python scripts/01_classifier_generator.py")
        return 1
    
    # 2. Préparer les données fusionnées
    print("\n🔧 Étape 2 : Préparation et fusion des données")
    print("-" * 80)
    
    merged_df = prepare_merged_data(recipes_df, interactions_df, verbose=True)
    
    # 3. Calculer les tops pour chaque type
    print("\n📊 Étape 3 : Calcul des rankings")
    print("-" * 80)
    
    all_results = {}
    
    for recipe_type in RECIPE_TYPES:
        print(f"\n{'=' * 80}")
        print(f"Type : {recipe_type.upper()}")
        print(f"{'=' * 80}")
        
        # Récupérer les paramètres bayésiens pour ce type
        params = BAYESIAN_PARAMS[recipe_type]
        
        print(f"\nParamètres bayésiens :")
        print(f"  • kb (régression)    : {params['kb']}")
        print(f"  • kpop (popularité)  : {params['kpop']}")
        print(f"  • gamma (amplif.)    : {params['gamma']}")
        
        # Calculer les tops
        tops_by_season = calculate_top_n_by_type(
            merged_df=merged_df,
            recipes_df=recipes_df,
            recipe_type=recipe_type,
            params=params,
            top_n=TOP_N,
            verbose=True
        )
        
        all_results[recipe_type] = tops_by_season
        
        # Sauvegarder les résultats
        for season, top_df in tops_by_season.items():
            output_file = RESULTS_DIR / f"top{TOP_N}_{recipe_type}_{season.lower()}.csv"
            top_df.to_csv(output_file, index=False, encoding='utf-8')
            print(f"   💾 Sauvegardé : {output_file.name}")
    
    # 4. Résumé final
    print("\n" + "=" * 80)
    print("✅ TRAITEMENT TERMINÉ")
    print("=" * 80)
    
    total_files = sum(len(tops) for tops in all_results.values())
    print(f"\n📁 {total_files} fichiers CSV générés dans : {RESULTS_DIR}")
    
    print("\n📊 Résumé des résultats :")
    for recipe_type, tops in all_results.items():
        print(f"\n   {recipe_type.upper()} :")
        for season in tops.keys():
            print(f"      • {season:10s} : top{TOP_N}_{recipe_type}_{season.lower()}.csv")
    
    print("\n" + "=" * 80)
    print("🎉 Tous les rankings ont été calculés avec succès!")
    print("=" * 80 + "\n")
    
    return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
