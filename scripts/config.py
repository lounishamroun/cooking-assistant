"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                           SYSTEM CONFIGURATION                               ║
╚══════════════════════════════════════════════════════════════════════════════╝

This file contains all configurable parameters for the recipe
recommendation system and the output paths of the different csv generated.
"""

import os

# ══════════════════════════════════════════════════════════════════════════════
# FILE PATHS
# ══════════════════════════════════════════════════════════════════════════════

# Path to the folder containing data (relative to structure folder)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(BASE_DIR, "data")

# Path to the results output folder
RESULTS_PATH = os.path.join(BASE_DIR, "resultats")

# Path to the parameter justification folder
JUSTIFICATION_PATH = os.path.join(BASE_DIR, "bayesian_parameters_justification")

# Create results and justification folders if they don't exist
os.makedirs(RESULTS_PATH, exist_ok=True)
os.makedirs(JUSTIFICATION_PATH, exist_ok=True)


# ══════════════════════════════════════════════════════════════════════════════
# BAYESIAN MODEL PARAMETERS
# ══════════════════════════════════════════════════════════════════════════════

# The set of parameters is justified in the folder dedicated to the justification of bayesian parameters

# Parameters for MAIN DISHES
PARAMS_PLATS = {
    'kb': 65,           # Number of "pseudo-reviews" for Bayesian regression
    'kpop': 45.0,       # Popularity threshold (reviews needed for 63% of max weight)
    'gamma': 1.2        # Popularity amplification factor
}

# Parameters for DESSERTS
PARAMS_DESSERTS = {
    'kb': 60,           # Higher = more conservative (pulls toward average)
    'kpop': 40.0,       # Desserts generally have more reviews
    'gamma': 1.2        # Moderate amplification
}

# Parameters for BEVERAGES
PARAMS_BOISSONS = {
    'kb': 20,           # Low = trust actual ratings more
    'kpop': 4.0,        # Beverages have fewer reviews
    'gamma': 0.7        # Low amplification (prioritizes quality)
}


# ══════════════════════════════════════════════════════════════════════════════
# CONSTANTS
# ══════════════════════════════════════════════════════════════════════════════

# Season order for display
SEASON_ORDER = ['Spring', 'Summer', 'Fall', 'Winter']

# Number of recipes to extract per season for ranking
TOP_N = 20
