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
├── app/                     # Entrypoints (CLI and Streamlit)
│   ├── main.py              # CLI runner / script orchestration
│   └── streamlit/           # Streamlit UI module
├── cooking_assistant/       # Core Python package (analysis, data, utils)
│   ├── analysis/            # Seasonal, reviews and scoring logic
│   ├── data/                # Downloader, loader, processor
│   ├── utils/               # Result helpers
│   └── config.py            # Central configuration & parameters
├── scripts/                 # One-off / reproducible pipeline scripts
├── data/                    # Data lake (raw → interim → processed)
├── docs/                    # Sphinx documentation source
├── tests/                   # (If present) Pytest test suite
├── Dockerfile               # Container build recipe
├── docker-compose.yml       # Orchestration (web service)
├── pyproject.toml           # Poetry dependencies & tool config
└── README.md                # Project overview
```

> Tip: Keep `data/processed` under version control only for small derived artifacts; large generated files should be ignored (adjust your `.gitignore`).


## Installation

### Prerequisites

- Python 3.12+
- Poetry (dependency & environment management)
- Optional: Docker & docker-compose (deployment)

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

### Quick Start

```bash
poetry install            # Install dependencies
poetry run pytest -q      # (Optional) Run tests
poetry run streamlit run app/streamlit/streamlit_app.py  # Launch UI
```

### Command Line Interface

Run the main orchestrator (example placeholder):
```bash
poetry run python app/main.py
```

### Data Pipeline Scripts

Raw → Interim → Processed transformation happens via explicit scripts:

```bash
# 1. Classification / tagging
poetry run python scripts/01_classifier_generator.py

# 2. Seasonal distribution analysis
poetry run python scripts/season_distribution.py

# 3. Rankings (seasonal top lists)
poetry run python scripts/top_recipe_rankings.py

# 4. Metrics enrichment (Bayesian score + effort)
poetry run python scripts/enrich_metrics.py
```

Generated enriched outputs (with `bayes_mean`, `effort_score`, seasonal top CSVs) are stored in `data/processed/`.

### Streamlit Web Interface

```bash
poetry run streamlit run app/streamlit/streamlit_app.py
```

### Building Documentation (Sphinx)

```bash
poetry run sphinx-build -b html docs docs/_build/html
# Or (if Makefile available)
make -C docs html
```

Open `docs/_build/html/index.html` in a browser.

## Configuration

The system configuration is centralized in `cooking_assistant/config.py`:

- **Data paths**: Raw, interim, and processed data directories
- **Bayesian parameters**: Scoring system configuration
- **Output settings**: Result formatting and export options

### Environment Variables

Create a `.env` (or use compose `environment:`) with:

```
STRICT_REAL_DATA=1        # Enforce using only real interaction-derived metrics (no synthetic fallbacks)
DATA_PATH=./data          # Root data directory (override if mounting differently in Docker)
```

`STRICT_REAL_DATA=1` ensures the UI hides or excludes any recipe metrics that could otherwise be approximated when insufficient real data exists.

### Bayesian Scoring (Overview)

We compute a stabilized recipe rating using a shrinkage approach:

```
weighted_mean = (valid_avg_rating * valid_reviews + season_avg * kb) / (valid_reviews + kb)
popularity_weight = (1 - exp(-valid_reviews / kpop)) ** gamma
bayes_mean = weighted_mean * popularity_weight
```

Where:
- `valid_avg_rating` = average of non-zero user ratings
- `valid_reviews` = count of valid rating events
- `season_avg` = seasonal category baseline average
- `kb` = shrinkage strength pulling sparse items toward seasonal mean
- `kpop`, `gamma` = parameters shaping how volume amplifies confidence

### Effort Score

`effort_score` approximates user effort based on ingredient count & instruction length (a heuristic). This allows dual-axis or quadrant visualizations contrasting recipe quality vs effort.

### Correlation & Quadrants

The UI categorizes recipes into quadrants using median splits on `bayes_mean` and `effort_score`. Correlation panels order features by absolute correlation with `bayes_mean` for interpretability.

## Docker Support

### Build Image

```bash
docker build -t cooking-assistant:latest .
```

### Run with Compose

```bash
docker-compose up --build
```

Visit: http://localhost:8501

### Environment & Data Mounting

The compose file mounts `./data` read-only into the container at `/app/data`. Override by editing `docker-compose.yml` or supplying a different volume. Add a local `.env` (or extend compose) for extra variables.

### Without Compose (plain Docker)

```bash
docker run -p 8501:8501 -e STRICT_REAL_DATA=1 -v $(pwd)/data:/app/data:ro cooking-assistant:latest
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
- `RAW_recipes_*.csv`: Recipe information
- `RAW_interactions_*.csv`: User-recipe interactions

Intermediate derivatives will appear in `data/interim/`, final scored outputs in `data/processed/`.

If initial source files are absent you can implement or adapt a downloader in `cooking_assistant/data/downloader.py`.

## License

MIT License (see `LICENSE`).

## Contributing

1. Fork & branch (`feat/<topic>`)
2. Keep changes small & tested
3. Run `pytest` + docs build before PR
4. Submit pull request describing rationale & impact

### Suggested Improvements
- Add more robust feature engineering (nutritional density, cost estimate)
- Extend effort model beyond basic heuristics
- Integrate user personalization layer (collaborative filtering)
- Parameter tuning via Bayesian optimization

---

### At a Glance
- Unified CSS for accessibility & consistent theming
- Ethical flag `STRICT_REAL_DATA` to ensure data authenticity
- Shrinkage Bayesian scoring to avoid overrating sparse recipes
- Sphinx docs for deeper explanation & reproducibility
- Dockerized deployment for platform neutrality

Feel free to open issues for questions or enhancement proposals.
