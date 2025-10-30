# Cooking Assistant - Modular Architecture

## Overview

Project in two steps :
- Step 1 : Classification of all the dataset recipes by types (dish,dessert,beverages) 
  Step 2 : Top 20 of best recipes by type (plat, dessert, boisson) and by season.

## Project Architecture

```
cooking-assistant/
│
├── cooking_assistant/              # MAIN PACKAGE
│   ├── __init__.py
│   ├── config.py                   # Central configuration
│   │
│   ├── data/                       # Data management
│   │   ├── __init__.py
│   │   ├── downloader.py           # Download from Kaggle
│   │   ├── loader.py               # CSV loading
│   │   └── processor.py            # Merging and preprocessing
│   │
│   ├── classification/             # Recipe classification
│   │   └── __init__.py             # (To be implemented)
│   │
│   ├── analysis/                   # Analysis and ranking
│   │   ├── __init__.py
│   │   ├── seasonal.py             # Seasonal utilities
│   │   ├── scoring.py              # Bayesian score calculation
│   │   └── reviews.py              # Top reviews analysis
│   │
│   └── utils/                      # Utilities
│       ├── __init__.py
│       └── results.py              # Results management
│
├── app/                            # Applications
│   ├── main.py                     # Main pipeline entry point
│   └── streamlit/                  # Streamlit web interface
│       └── streamlit_app.py
│
├── scripts/                        # Automation scripts
│   ├── 01_classifier_generator.py  # Generates classified recipes
│   ├── top_recipe_rankings.py      # Calculate top rankings
│   ├── top_reviews_analyzer.py     # Analyze top reviews
│   └── season_distribution.py      # Season distribution analysis
│
├── analysis_parameter_justification/ # Parameter analysis
│   ├── bayesian_parameters_docs_justification.md
│   ├── generate_csv_to_analyse_for_parameter_justification.py
│   └── results_to_analyse/         # Analysis results
│
├── data/                           # Data directories
│   ├── raw/                        # Raw data (Kaggle)
│   ├── interim/                    # Intermediate data
│   │   └── recipes_classified.csv  # Recipes with 'type' column
│   └── processed/                  # Final processed data
│       ├── top20_plat_for_each_season.csv
│       ├── top20_dessert_for_each_season.csv
│       └── top20_boisson_for_each_season.csv
│
├── docs/                           # Documentation
├── reports/                        # Reports and visualizations
├── logs/                           # Log files
├── models/                         # ML models and artifacts
├── utils/                          # Legacy utilities
│
├── .gitignore.txt                  # Git ignore patterns
├── pyproject.toml                  # Poetry project configuration
├── poetry.lock                     # Poetry dependency lock file
├── docker-compose.yml              # Docker compose configuration
├── Dockerfile                      # Docker container configuration
├── README.md                       # Project documentation
└── ARCHITECTURE.md                 # This file
```
│
├── data/                           # Data directories
│   ├── raw/                        # Raw data (Kaggle)
│   ├── interim/                    # Intermediate data
│   │   └── recipes_classified.csv  # Recipes with 'type' column
│   └── processed/                  # Final processed data
│       ├── top20_plat_for_each_season.csv
│       ├── top20_dessert_for_each_season.csv
│       └── top20_boisson_for_each_season.csv
│
├── docs/                           # Documentation
├── reports/                        # Reports and visualizations
├── logs/                           # Log files
└── pyproject.toml                  # Poetry configuration
```

## Installation

### Prerequisites
- Python 3.8+
- Poetry (recommended) or pip

### With Poetry (Recommended)
```bash
# Install Poetry if not already installed
curl -sSL https://install.python-poetry.org | python3 -

# Install project dependencies
poetry install

# Activate virtual environment
poetry shell
```

### With pip
```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -e .
```

### Dependencies Management

The project uses Poetry for dependency management:
- `pyproject.toml`: Project configuration and dependencies
- `poetry.lock`: Locked versions for reproducible builds

Key dependencies include:
- pandas, numpy: Data manipulation
- scikit-learn: Machine learning
- matplotlib, seaborn: Visualization
- streamlit: Web interface
- kagglehub: Kaggle data download

## Usage

### 1. Download raw data

```python
from cooking_assistant.data import download_raw_data

# Download from Kaggle if not already done
download_raw_data()
```

### 2. Load and prepare data

```python
from cooking_assistant.data import load_data, prepare_merged_data

# Load recipes and interactions
recipes_df, interactions_df = load_data()

# Merge and add seasons
merged_df = prepare_merged_data(recipes_df, interactions_df)
```

### 3. Calculate top 20 by type and season

```python
from cooking_assistant.analysis import calculate_top_n_by_type
from cooking_assistant.config import BAYESIAN_PARAMS

# Calculate for main dishes
tops = calculate_top_n_by_type(
    merged_df=merged_df,
    recipes_df=recipes_df,
    recipe_type='plat',
    params=BAYESIAN_PARAMS['plat']
)

# Access spring top 20
spring_top20 = tops['Spring']
```

### 4. Analyze tops by number of reviews

```python
from cooking_assistant.analysis import analyze_top_reviews_by_type_season

# Analyze the 100 most reviewed recipes
results = analyze_top_reviews_by_type_season(
    merged_df=merged_df,
    recipes_df=recipes_df,
    top_n=100
)
```

## Configuration Files

### Project Configuration
- **`pyproject.toml`**: Poetry project configuration
  - Project metadata (name, version, description)
  - Dependencies specification
  - Build system configuration
  - Development dependencies

- **`poetry.lock`**: Dependency lock file
  - Exact versions of all dependencies
  - Ensures reproducible builds across environments
  - Should be committed to version control

### Development Configuration
- **`.gitignore.txt`**: Git ignore patterns
  - Excludes temporary files, logs, data files
  - Protects sensitive configuration
  - Prevents large data files from being committed

- **`docker-compose.yml`** & **`Dockerfile`**: Container configuration
  - Dockerized environment setup
  - Consistent deployment across platforms

## Configuration

All configuration is centralized in `cooking_assistant/config.py`:

- **Paths**: `RAW_DATA_DIR`, `PROCESSED_DATA_DIR`, `RESULTS_DIR`
- **Types**: `RECIPE_TYPES = ["plat", "dessert", "boisson"]`
- **Seasons**: `SEASONS = ["Spring", "Summer", "Fall", "Winter"]`
- **Bayesian parameters**: `BAYESIAN_PARAMS`

## Bayesian Parameters

Parameters are justified in `analysis_parameter_justification/bayesian_parameters_docs_justification.md`

| Type     | kb  | kpop | gamma | Description                    |
|----------|-----|------|-------|--------------------------------|
| Plat     | 65  | 47.0 | 1.2   | Quality/popularity balance     |
| Dessert  | 60  | 40.0 | 1.2   | More reviews in general        |
| Boisson  | 20  | 4.0  | 0.7   | Quality priority               |

## Main Pipeline

The complete pipeline is available via `app/main.py`:

```bash
# Run the complete pipeline
python app/main.py
```

This script executes:
1. Data download from Kaggle
2. Recipe classification by ML
3. Bayesian score calculation and top 20 generation

Final results are saved in `data/processed/`:
- `top20_plat_for_each_season.csv` (80 recipes: 20×4 seasons)
- `top20_dessert_for_each_season.csv` (80 recipes: 20×4 seasons)
- `top20_boisson_for_each_season.csv` (80 recipes: 20×4 seasons)

## Migration from old architecture

Old scripts in `scripts/` now use the `cooking_assistant` package:

**Before**:
```python
from scripts.config import PARAMS_PLATS
from scripts.data_loader_preparation import load_data
```

**After**:
```python
from cooking_assistant.config import BAYESIAN_PARAMS
from cooking_assistant.data import load_data

params_plats = BAYESIAN_PARAMS['plat']
```

## Testing

```bash
# Test data loading
python -m cooking_assistant.data.loader

# Test season calculation
python -m cooking_assistant.analysis.seasonal
```

## Main Scripts

### Script 1: Classification (01_classifier_generator.py)

**This script remains complex and requires future refactoring.**

Generates `recipes_classified.csv` with the `type` column.

### Script 2: Rankings calculation (top_recipe_rankings.py)

Uses the modular architecture to calculate rankings:

```python
from cooking_assistant.data import load_classified_recipes, load_interactions, prepare_merged_data
from cooking_assistant.analysis import calculate_top_n_by_type
from cooking_assistant.config import BAYESIAN_PARAMS, RECIPE_TYPES

def main():
    # Load data
    recipes = load_classified_recipes()
    interactions = load_interactions()
    merged = prepare_merged_data(recipes, interactions)
    
    # Calculate for each type
    for recipe_type in RECIPE_TYPES:
        tops = calculate_top_n_by_type(
            merged, recipes, recipe_type,
            BAYESIAN_PARAMS[recipe_type]
        )
        # Save results...

if __name__ == "__main__":
    main()
```

## Data Flow

```
RAW_recipes.csv + RAW_interactions.csv
            ↓
    01_classifier_generator.py
            ↓
    recipes_classified.csv (data/interim/)
            ↓
    top_recipe_rankings.py
            ↓
    top20_*.csv files (data/processed/)
```

## Contributors

- Lounis Hamroun
- Alexandre Donnat
- Omar Fekih
- Leo Ivars


