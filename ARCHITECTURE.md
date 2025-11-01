# Cooking Assistant - Global Architecture

## Overview

Intelligent culinary assistance system that classifies and recommends recipes by type and season:
- **Step 1**: Automatic recipe classification (dish, dessert, beverage)
- **Step 2**: Recommendation of top 20 best recipes by type and season

## Project Architecture

```
cooking-assistant/
│
├── cooking_assistant/              # MAIN PACKAGE
│   ├── __init__.py
│   ├── config.py                   # Centralized configuration
│   │
│   ├── data/                       # Data management
│   │   ├── __init__.py
│   │   ├── downloader.py           # Download from Kaggle
│   │   ├── loader.py               # CSV loading
│   │   └── processor.py            # Merging and preprocessing
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
│   ├── main.py                     # Main entry point
│   └── streamlit/                  # Streamlit web interface
│       ├── streamlit_app.py
│       ├── components.py
│       └── styles.css
│
├── scripts/                        # Automation scripts
│   ├── 01_classifier_generator.py  # Generate classified recipes
│   ├── top_recipe_rankings.py      # Calculate rankings
│   ├── top_reviews_analyzer.py     # Analyze top reviews
│   └── season_distribution.py      # Seasonal distribution analysis
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
├── analysis_parameter_justification/ # Parameter analysis
│   ├── bayesian_parameters_docs_justification.md
│   ├── generate_csv_to_analyse_for_parameter_justification.py
│   └── results_to_analyse/         # Analysis results
│
├── docs/                           # Documentation
├── reports/                        # Reports and visualizations
├── logs/                           # Log files
├── models/                         # ML models and artifacts
├── tests/                          # Unit tests
├── utils/                          # Legacy utilities
│
├── pyproject.toml                  # Poetry configuration
├── requirements.txt                # Pip dependencies
├── docker-compose.yml              # Docker Compose configuration
├── Dockerfile                      # Docker container configuration
├── README.md                       # Project documentation
└── ARCHITECTURE.md                 # This file
```

## Data Flow

```
Raw Data (Kaggle)
    recipes.csv + interactions.csv
            ↓
    01_classifier_generator.py
            ↓
    recipes_classified.csv (data/interim/)
            ↓
    top_recipe_rankings.py
            ↓
    top20_*.csv (data/processed/)
            ↓
    Streamlit Interface
```

## Main Components

### 1. `cooking_assistant` Package
- **`data/`**: Data downloading, loading and preparation
- **`analysis/`**: Bayesian scoring algorithms and seasonal analysis
- **`utils/`**: Common utilities and results management
- **`config.py`**: Centralized configuration (parameters, paths, constants)

### 2. Applications (`app/`)
- **`main.py`**: Main execution pipeline
- **`streamlit/`**: Interactive web interface for recommendations

### 3. Automation Scripts (`scripts/`)
- Automatic recipe classification by ML
- Bayesian score-based rankings calculation
- Statistical analysis and seasonal distribution

### 4. Data Management (`data/`)
- **`raw/`**: Original data from Kaggle
- **`interim/`**: Data enriched with classifications
- **`processed/`**: Final results (top 20 by type/season)

## Key Technologies

- **Python 3.8+**: Main language
- **Poetry**: Dependency management
- **Pandas/NumPy**: Data manipulation
- **Scikit-learn**: Machine learning for classification
- **Streamlit**: Interactive web interface
- **Docker**: Containerization
- **Pytest**: Unit testing


