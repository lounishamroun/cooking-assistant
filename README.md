<div align="center">

# Cooking Assistant
**Season-aware recipe ranking, classification & interactive exploration**

[Documentation (GitHub Pages)](https://lounishamroun.github.io/cooking-assistant/) · [API Reference](https://lounishamroun.github.io/cooking-assistant/reference.html) · [Classifier Justification](analysis_parameter_justification/README_food_type_classifier_justification.md) · [Bayesian Parameter Justification](analysis_parameter_justification/bayesian_parameters_docs_justification.md)

**Live Demo (Streamlit Cloud):** https://cooking-assistant.streamlit.app/

</div>

## 1. Quickstart (Evaluation)
Fastest path using pre-generated processed CSVs (no need to regenerate heavy data). Artifacts consumed by the demo are the canonical `*_latest.csv` files; timestamped ones preserve history.

```bash
git clone https://github.com/lounishamroun/cooking-assistant.git
cd cooking-assistant
poetry install
poetry run streamlit run app/streamlit/streamlit_app.py
```
Open http://localhost:8501.

Integration status: pipeline + justification scripts produce stable `*_latest.csv` artifacts (season distribution & top_100) automatically; Streamlit falls back gracefully if enrichment missing.

## 2. Full Reproduction (Pipeline)
Runs the end-to-end pipeline (download → classify → rank). Requires Kaggle access if downloader uses API.
```bash
poetry run python app/main.py
```
Outputs saved in `data/processed/`.

## 3. Core Components
| Component | Purpose |
|-----------|---------|
| `app/main.py` | Complete pipeline orchestrator |
| `app/streamlit/` | Interactive UI (ranking, quadrants, exploration) |
| `cooking_assistant/analysis/` | Seasonal aggregation, scoring, correlations |
| `cooking_assistant/data/` | Download, load, process raw → interim → processed |
| `scripts/` | Individual reproducible steps (classification, rankings, metrics) |
| `analysis_parameter_justification/` | Formal justifications (classifier + Bayesian params) |

## 4. Deployment Options
### Local (Poetry)
```bash
poetry install
poetry run streamlit run app/streamlit/streamlit_app.py
```

### Docker
```bash
docker build -t cooking-assistant:latest .
docker run -p 8501:8501 -e STRICT_REAL_DATA=1 cooking-assistant:latest
```
Compose (mount read-only data volume):
```bash
docker-compose up --build
```

### Streamlit Cloud (Recommended for Demo)
Set the entrypoint to `app/streamlit/streamlit_app.py` and ensure `data/processed/` contains pre-generated CSVs.

## 5. Regenerate Data Manually (Ordered From Scratch)
If you want to reproduce everything without using the orchestrator (`app/main.py`), run the individual scripts in this order. Step 1 requires Kaggle credentials configured (see docs) if raw data is absent.

```bash
# 1. Download raw datasets (if not already present in data/raw/)
poetry run python -m cooking_assistant.data.downloader

# 2. Classify recipes (produces data/interim/recipes_classified.csv)
poetry run python scripts/01_classifier_generator.py

# 3. Enrich metrics (adds derived popularity / effort features, if used by ranking or UI)
poetry run python scripts/enrich_metrics.py

# 4. Generate seasonal Bayesian top 20 rankings (writes 3 CSVs in data/processed/)
poetry run python scripts/top_recipe_rankings.py

# 5. (Optional) Parameter justification artifacts (season distribution + top 100 reviews)
poetry run python analysis_parameter_justification/generate_csv_to_analyse_for_parameter_justification.py

# 6. Launch the Streamlit UI
poetry run streamlit run app/streamlit/streamlit_app.py
```

Or run everything (steps 1–4) with a single command:

```bash
poetry run python app/main.py
```

### Generated Key Artifacts
| File | Purpose | Creator |
|------|---------|---------|
| `data/interim/recipes_classified.csv` | Each recipe + predicted type + confidence | Classifier script |
| `data/processed/top20_<type>_for_each_season.csv` | Top 20 per season for each type (ranking) | Rankings script |
| `analysis_parameter_justification/results_to_analyse/season_type_distribution_latest.csv` | Share of reviews per season per type | Justification script |
| `analysis_parameter_justification/results_to_analyse/top_100_reviews_by_type_season_latest.csv` | Top 100 review counts per type-season | Justification script |

Latest vs timestamped: the justification script produces timestamped historical snapshots and also writes stable `*_latest.csv` aliases so the Streamlit app can load them reliably.

## 6. Bayesian Scoring (Formula Summary)
Weighted quality + popularity shrinkage:
```
Q = (valid_avg_rating * valid_reviews + season_avg * kb) / (valid_reviews + kb)
Pop_Weight = (1 - exp(-nb_season_reviews / kpop)) ** gamma
Final = Q * Pop_Weight
```
Detailed rationale: see [Bayesian Parameter Justification](analysis_parameter_justification/bayesian_parameters_docs_justification.md).

## 7. Classifier (Structural + NLP)
Dual-phase (nutritional prototypes + lexical signals) with arbitration layer. Full methodology: [Classifier Justification](analysis_parameter_justification/README_food_type_classifier_justification.md).

## 8. Documentation & Tests
```bash
# Build docs locally
poetry run sphinx-build -b html docs docs/_build/html

# Run tests (unit + integration)
poetry run pytest -q
```
If the GitHub Pages site looks empty right after a push, wait ~1–2 minutes (deployment job) then hard refresh (Ctrl+Shift+R). Ensure the link points to the repository root: `https://<user>.github.io/cooking-assistant/`.
Coverage threshold: 90% (current > 90%).

## 9. Configuration
Edit `cooking_assistant/config.py` for paths & Bayesian parameters.

Environment examples:
```
STRICT_REAL_DATA=1        # disable synthetic popularity fallbacks
DEMO_MODE=1               # limit heavy loading in Streamlit (optional if implemented)
LOG_FILE=app.log          # send pipeline logs to file
```
Change Bayesian parameters (`kb`, `kpop`, `gamma`) per recipe type in `BAYESIAN_PARAMS` to experiment.

### Environment Setup & Troubleshooting


```bash
# Ensure Poetry itself is installed
curl -sSL https://install.python-poetry.org | python3 -

# Install dependencies (creates the virtualenv if absent)
poetry install

# Confirm environment (shows path)
poetry env info

# Run any script using the managed environment
poetry run python scripts/01_classifier_generator.py
```

If `app/main.py` falls back to the system interpreter (message: `[env] .venv not found; falling back ...`), it means the virtualenv wasn’t created yet—run `poetry install` first. Do NOT manually create `.venv`; let Poetry manage it for consistency.

To use an in-project `.venv` (optional):
```bash
poetry config virtualenvs.in-project true
poetry install
```
This places the environment under `./.venv/` so path-based tooling (like some IDEs) picks it up automatically.

## 10. Contributing
Branch naming: `feat/`, `fix/`, `docs/`. Run tests + docs build before PR.

## 11. License
MIT (see `LICENSE`).

---
### Why Separate Justifications?
To keep the README lean while preserving deep analytical work. All reasoning remains versioned under `analysis_parameter_justification/` and surfaced via direct links & published Sphinx docs.

