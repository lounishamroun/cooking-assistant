# Cooking Assistant

A Python-based cooking recommendation system that analyzes recipe data and provides personalized suggestions based on seasonal trends and user preferences.

## Features

- **Recipe Classification**: Automatic categorization of recipes into drinks, desserts, and main dishes
- **Seasonal Analysis**: Seasonal trend detection for recipe recommendations
- **Bayesian Scoring**: Advanced scoring system for recipe ranking
- **Interactive Interface**: Streamlit web application for user interaction
- **Data Processing**: Comprehensive data loading and processing pipeline

## Project Structure

```
cooking-assistant/
├── cooking_assistant/           # Main package
│   ├── analysis/               # Analysis modules
│   │   ├── reviews.py         # Review analysis
│   │   ├── scoring.py         # Bayesian scoring system
│   │   └── seasonal.py        # Seasonal trend analysis
│   ├── data/                  # Data handling
│   │   ├── downloader.py      # Data downloading utilities
│   │   ├── loader.py          # Data loading functions
│   │   └── processor.py       # Data processing pipeline
│   ├── utils/                 # Utility functions
│   │   └── results.py         # Result processing
│   └── config.py              # Configuration constants
├── app/                       # Application layer
│   ├── main.py               # Main application entry
│   └── streamlit/            # Streamlit web interface
├── scripts/                   # Analysis scripts
├── analysis_parameter_justification/  # Parameter analysis
├── data/                      # Data storage
│   ├── raw/                  # Raw data files
│   ├── interim/              # Intermediate processed data
│   └── processed/            # Final processed data
└── docs/                     # Documentation
```

## Installation

### Prerequisites

- Python 3.8+
- Poetry (for dependency management)

### Setup

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd cooking-assistant
   ```

2. Install dependencies using Poetry:
   ```bash
   poetry install
   ```

3. Activate the virtual environment:
   ```bash
   poetry shell
   ```

## Usage

### Command Line Interface

Run the main application:
```bash
poetry run python app/main.py
```

### Streamlit Web Interface

Launch the web interface:
```bash
poetry run streamlit run app/streamlit/streamlit_app.py
```

### Data Processing

Process raw recipe data:
```bash
poetry run python scripts/01_classifier_generator.py
```

Analyze seasonal trends:
```bash
poetry run python scripts/season_distribution.py
```

Generate top recipe rankings:
```bash
poetry run python scripts/top_recipe_rankings.py
```

## Configuration

The system configuration is centralized in `cooking_assistant/config.py`:

- **Data paths**: Raw, interim, and processed data directories
- **Bayesian parameters**: Scoring system configuration
- **Output settings**: Result formatting and export options

## Docker Support

Build and run using Docker:
```bash
docker-compose up --build
```

## Development

### Running Tests

```bash
poetry run pytest
```

### Code Quality

The project follows Python best practices with:
- Type hints where applicable
- Comprehensive documentation
- Modular design for maintainability

## Data Requirements

The system expects the following data files in `data/raw/`:
- `PP_recipes_*.csv`: Recipe information
- `PP_users_*.csv`: User data
- `interactions_*.csv`: User-recipe interactions

## License

[Add your license information here]

## Contributing

[Add contribution guidelines here]
