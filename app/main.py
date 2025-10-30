#!/usr/bin/env python3
"""
COOKING ASSISTANT - PIPELINE COMPLET

Script principal qui exécute l'ensemble du pipeline pour obtenir les top 20 recettes
par type et saison.

Pipeline complet :
1. Téléchargement des données depuis Kaggle
2. Classification des recettes par type (plat, dessert, boisson)  
3. Calcul des scores bayésiens et génération des top 20

Résultats finaux dans data/processed/ :
- top20_plat_for_each_season.csv
- top20_dessert_for_each_season.csv  
- top20_boisson_for_each_season.csv
"""

import sys
import time
import subprocess
from pathlib import Path
from datetime import datetime

# Ajouter le projet au path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from cooking_assistant.data.downloader import main as download_data
from scripts.top_recipe_rankings import main as calculate_rankings


def print_header():
    """Affiche l'en-tête du pipeline."""
    print("COOKING ASSISTANT - PIPELINE COMPLET")
    print(f"Démarrage : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()


def print_step(step_num, title, description=""):
    """Affiche le titre d'une étape."""
    print(f"\nÉTAPE {step_num} : {title}")
    if description:
        print(f"   {description}")
    print()


def run_classification_script():
    """
    Exécute le script de classification 01_classifier_generator.py
    
    Returns:
        bool: True si succès, False si échec
    """
    try:
        # Obtenir le chemin du script
        script_path = project_root / "scripts" / "01_classifier_generator.py"
        python_exe = project_root / ".venv" / "bin" / "python"
        
        # Exécuter le script de classification
        result = subprocess.run([
            str(python_exe), 
            str(script_path)
        ], 
        cwd=str(project_root),
        capture_output=True, 
        text=True,
        timeout=600  # 10 minutes max
        )
        
        if result.returncode == 0:
            print("Classification terminée avec succès")
            return True
        else:
            print(f"Erreur dans la classification :")
            print(f"   Code de sortie : {result.returncode}")
            if result.stderr:
                print(f"   Erreur : {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("Timeout : La classification a pris trop de temps")
        return False
    except Exception as e:
        print(f"Erreur lors de l'exécution de la classification : {e}")
        return False


def execute_step(step_func, step_name, *args, **kwargs):
    """
    Exécute une étape et mesure le temps d'exécution.
    
    Args:
        step_func: Fonction à exécuter
        step_name: Nom de l'étape pour l'affichage
        *args, **kwargs: Arguments pour la fonction
        
    Returns:
        bool: True si succès, False si échec
    """
    start_time = time.time()
    
    try:
        print(f"\nLancement de {step_name}...")
        result = step_func(*args, **kwargs)
        
        elapsed = time.time() - start_time
        minutes = int(elapsed // 60)
        seconds = int(elapsed % 60)
        
        print(f"{step_name} terminé avec succès !")
        print(f"Temps d'exécution : {minutes}m {seconds}s")
        
        return True
        
    except Exception as e:
        elapsed = time.time() - start_time
        minutes = int(elapsed // 60)
        seconds = int(elapsed % 60)
        
        print(f"Erreur dans {step_name} :")
        print(f"{str(e)}")
        print(f"Temps avant échec : {minutes}m {seconds}s")
        
        return False


def execute_script_step(script_func, step_name):
    """
    Exécute une étape script et mesure le temps d'exécution.
    """
    start_time = time.time()
    
    try:
        print(f"\nLancement de {step_name}...")
        success = script_func()
        
        elapsed = time.time() - start_time
        minutes = int(elapsed // 60)
        seconds = int(elapsed % 60)
        
        if success:
            print(f"{step_name} terminé avec succès !")
        else:
            print(f"{step_name} a échoué !")
            
        print(f"Temps d'exécution : {minutes}m {seconds}s")
        
        return success
        
    except Exception as e:
        elapsed = time.time() - start_time
        minutes = int(elapsed // 60)
        seconds = int(elapsed % 60)
        
        print(f"Erreur dans {step_name} :")
        print(f"   {str(e)}")
        print(f"Temps avant échec : {minutes}m {seconds}s")
        
        return False


def main():
    """
    Pipeline principal pour générer les top 20 recettes.
    
    Returns:
        int: Code de sortie (0 = succès, 1 = échec)
    """
    print_header()
    
    total_start = time.time()
    
    try:
        # ══════════════════════════════════════════════════════════════════
        # ÉTAPE 1 : Téléchargement des données depuis Kaggle
        # ══════════════════════════════════════════════════════════════════
        print_step(1, "TÉLÉCHARGEMENT DES DONNÉES", 
                   "Récupération des datasets depuis Kaggle")
        
        if not execute_step(download_data, "Téléchargement Kaggle"):
            return 1
        
        # ══════════════════════════════════════════════════════════════════
        # ÉTAPE 2 : Classification des recettes par type
        # ══════════════════════════════════════════════════════════════════
        print_step(2, "CLASSIFICATION DES RECETTES", 
                   "Analyse ML pour déterminer le type (plat, dessert, boisson)")
        
        if not execute_script_step(run_classification_script, "Classification ML"):
            return 1
        
        # ══════════════════════════════════════════════════════════════════
        # ÉTAPE 3 : Calcul des top 20 par type et saison
        # ══════════════════════════════════════════════════════════════════
        print_step(3, "CALCUL DES TOP 20 FINAUX", 
                   "Scores bayésiens et génération des CSV finaux")
        
        if not execute_step(calculate_rankings, "Calcul des rankings"):
            return 1
        
        # ══════════════════════════════════════════════════════════════════
        # RÉSUMÉ FINAL
        # ══════════════════════════════════════════════════════════════════
        total_elapsed = time.time() - total_start
        total_minutes = int(total_elapsed // 60)
        total_seconds = int(total_elapsed % 60)
        
        print("\n" + "=" * 80)
        print("PIPELINE COMPLET TERMINÉ AVEC SUCCÈS !")
        print("=" * 80)
        
        print(f"\nRÉSULTATS GÉNÉRÉS :")
        print(f"Dossier : data/processed/")
        print(f"Fichiers :")
        print(f"   • top20_plat_for_each_season.csv      (80 recettes)")
        print(f"   • top20_dessert_for_each_season.csv   (80 recettes)")  
        print(f"   • top20_boisson_for_each_season.csv   (80 recettes)")
        print(f"Total : 240 recettes analysées")
        
        print(f"\nTEMPS TOTAL : {total_minutes}m {total_seconds}s")
        print(f"Fin : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        print(f"\nVos données sont prêtes pour l'analyse !")
        print("=" * 80)
        
        return 0
        
    except KeyboardInterrupt:
        print(f"\n\nPipeline interrompu par l'utilisateur")
        return 1
        
    except Exception as e:
        print(f"\n\nErreur fatale dans le pipeline :")
        print(f"   {str(e)}")
        return 1


if __name__ == "__main__":
    """Point d'entrée du script."""
    exit_code = main()
    sys.exit(exit_code)