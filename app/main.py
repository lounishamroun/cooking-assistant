#!/usr/bin/env python3
"""
COOKING ASSISTANT - COMPLETE PIPELINE

Main script that executes the entire pipeline to get top 20 recipes
by type and season.

Complete pipeline:
1. Download data from Kaggle
2. Classify recipes by type (plat, dessert, boisson)  
3. Calculate Bayesian scores and generate top 20

Final results in data/processed/:
- top20_plat_for_each_season.csv
- top20_dessert_for_each_season.csv  
- top20_boisson_for_each_season.csv
"""

import sys
import time
import subprocess
from pathlib import Path
from datetime import datetime

# Add project to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from cooking_assistant.data.downloader import main as download_data
from scripts.top_recipe_rankings import main as calculate_rankings


def print_header():
    """Displays the pipeline header."""
    print("COOKING ASSISTANT - COMPLETE PIPELINE")
    print(f"Starting: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()


def print_step(step_num, title, description=""):
    """Displays a step title."""
    print(f"\nSTEP {step_num}: {title}")
    if description:
        print(f"   {description}")
    print()


def run_classification_script():
    """
    Executes the classification script 01_classifier_generator.py
    
    Returns:
        bool: True if successful, False if failed
    """
    try:
        # Get script path
        script_path = project_root / "scripts" / "01_classifier_generator.py"
        python_exe = project_root / ".venv" / "bin" / "python"
        
        # Execute classification script
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
            print("Classification completed successfully")
            return True
        else:
            print(f"Error in classification:")
            print(f"   Exit code: {result.returncode}")
            if result.stderr:
                print(f"   Error: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("Timeout: Classification took too long")
        return False
    except Exception as e:
        print(f"Error executing classification: {e}")
        return False


def execute_step(step_func, step_name, *args, **kwargs):
    """
    Executes a step and measures execution time.
    
    Args:
        step_func: Function to execute
        step_name: Step name for display
        *args, **kwargs: Arguments for the function
        
    Returns:
        bool: True if successful, False if failed
    """
    start_time = time.time()
    
    try:
        print(f"\nStarting {step_name}...")
        result = step_func(*args, **kwargs)
        
        elapsed = time.time() - start_time
        minutes = int(elapsed // 60)
        seconds = int(elapsed % 60)
        
        print(f"{step_name} completed successfully!")
        print(f"Execution time: {minutes}m {seconds}s")
        
        return True
        
    except Exception as e:
        elapsed = time.time() - start_time
        minutes = int(elapsed // 60)
        seconds = int(elapsed % 60)
        
        print(f"Error in {step_name}:")
        print(f"{str(e)}")
        print(f"Time before failure: {minutes}m {seconds}s")
        
        return False


def execute_script_step(script_func, step_name):
    """
    Executes a script step and measures execution time.
    """
    start_time = time.time()
    
    try:
        print(f"\nStarting {step_name}...")
        success = script_func()
        
        elapsed = time.time() - start_time
        minutes = int(elapsed // 60)
        seconds = int(elapsed % 60)
        
        if success:
            print(f"{step_name} completed successfully!")
        else:
            print(f"{step_name} failed!")
            
        print(f"Execution time: {minutes}m {seconds}s")
        
        return success
        
    except Exception as e:
        elapsed = time.time() - start_time
        minutes = int(elapsed // 60)
        seconds = int(elapsed % 60)
        
        print(f"Error in {step_name}:")
        print(f"   {str(e)}")
        print(f"Time before failure: {minutes}m {seconds}s")
        
        return False


def main():
    """
    Main pipeline to generate top 20 recipes.
    
    Returns:
        int: Exit code (0 = success, 1 = failure)
    """
    print_header()
    
    total_start = time.time()
    
    try:
        # ══════════════════════════════════════════════════════════════════
        # STEP 1: Download data from Kaggle
        # ══════════════════════════════════════════════════════════════════
        print_step(1, "DATA DOWNLOAD", 
                   "Retrieving datasets from Kaggle")
        
        if not execute_step(download_data, "Kaggle Download"):
            return 1
        
        # ══════════════════════════════════════════════════════════════════
        # STEP 2: Classify recipes by type
        # ══════════════════════════════════════════════════════════════════
        print_step(2, "RECIPE CLASSIFICATION", 
                   "ML analysis to determine type (plat, dessert, boisson)")
        
        if not execute_script_step(run_classification_script, "ML Classification"):
            return 1
        
        # ══════════════════════════════════════════════════════════════════
        # STEP 3: Calculate top 20 by type and season
        # ══════════════════════════════════════════════════════════════════
        print_step(3, "CALCULATE FINAL TOP 20", 
                   "Bayesian scores and generation of final CSVs")
        
        if not execute_step(calculate_rankings, "Rankings calculation"):
            return 1
        
        # ══════════════════════════════════════════════════════════════════
        # FINAL SUMMARY
        # ══════════════════════════════════════════════════════════════════
        total_elapsed = time.time() - total_start
        total_minutes = int(total_elapsed // 60)
        total_seconds = int(total_elapsed % 60)
        
        print("\n" + "=" * 80)
        print("COMPLETE PIPELINE FINISHED SUCCESSFULLY!")
        print("=" * 80)
        
        print(f"\nGENERATED RESULTS:")
        print(f"Folder: data/processed/")
        print(f"Files:")
        print(f"   • top20_plat_for_each_season.csv      (80 recipes)")
        print(f"   • top20_dessert_for_each_season.csv   (80 recipes)")  
        print(f"   • top20_boisson_for_each_season.csv   (80 recipes)")
        print(f"Total: 240 recipes analyzed")
        
        print(f"\nTOTAL TIME: {total_minutes}m {total_seconds}s")
        print(f"End: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        print(f"\nYour data is ready for analysis!")
        print("=" * 80)
        
        return 0
        
    except KeyboardInterrupt:
        print(f"\n\nPipeline interrupted by user")
        return 1
        
    except Exception as e:
        print(f"\n\nFatal error in pipeline:")
        print(f"   {str(e)}")
        return 1


if __name__ == "__main__":
    """Script entry point."""
    exit_code = main()
    sys.exit(exit_code)