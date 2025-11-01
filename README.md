<div align="center">

# Cooking Assistant
**Season-aware recipe ranking, classification & interactive exploration**

[Documentation (GitHub Pages)](https://lounishamroun.github.io/cooking-assistant/) · [API Reference](https://lounishamroun.github.io/cooking-assistant/reference.html) · [Classifier Justification](analysis_parameter_justification/README_food_type_classifier_justification.md) · [Bayesian Parameter Justification](analysis_parameter_justification/bayesian_parameters_docs_justification.md)

**Live Demo (Streamlit Cloud):** https://cooking-assistant.streamlit.app/

</div>

### TL;DR
Classify recipes (4-phase structural + lexical arbitration), compute seasonal Bayesian rankings (quality shrinkage × popularity saturation), explore results in a Streamlit dashboard with canonical `*_latest.csv` artifacts for reproducible evaluation.

### Global Architecture (Snapshot)
```
 cooking-assistant/
 ├── cooking_assistant/            # Core package (config, data, analysis, utils)
 │   ├── data/                     # Download, load, preprocess raw → interim
 │   ├── analysis/                 # Seasonal + Bayesian scoring + reviews
 │   └── utils/                    # Results & shared helpers
 ├── app/                          # Orchestrator + Streamlit UI
 ├── scripts/                      # Reproducible pipeline steps (classification, rankings, metrics)
 ├── data/                         # raw / interim / processed artifacts
 ├── analysis_parameter_justification/  # Parameter & methodology justification assets
 ├── docs/                         # Sphinx (MyST) documentation site
 ├── tests/                        # Unit & integration tests (90%+ coverage)
 └── Dockerfile / docker-compose.yml
```
Data flow: `RAW_recipes.csv + RAW_interactions.csv → classifier (recipes_classified.csv) → enrichment (recipes_classified_enriched.csv) → ranking (top20_<type>_for_each_season.csv) → Streamlit UI`.

### Primary Data Sources
| File | Role |
|------|------|
| `RAW_recipes.csv` | Base recipe metadata & nutrition for classification features |
| `RAW_interactions.csv` | User ratings & reviews powering popularity and seasonal review counts |
| `recipes_classified.csv` | Output of multi-phase classifier (includes type + confidence) used by ranking |

### Glossary (Key Symbols)
| Term | Meaning |
|------|---------|
| `kb` | Shrinkage strength toward seasonal baseline |
| `kpop` | Review count scale controlling saturation speed |
| `gamma` | Curvature exponent amplifying popularity separation |
| `season_avg` | Mean rating for (type, season) used as prior |
| `valid_avg_rating` | Average rating excluding 0 (non-votes) |
| `nb_valid_ratings` | Count of ratings > 0 for a recipe in season |
| `nb_season_reviews` | Total reviews (incl. 0 ratings) for engagement measure |
| `Pop_Weight` | Saturated popularity multiplier `(1 - exp(-reviews/kpop))^gamma` |
| `Final` | Product of shrunk quality `Q` and popularity weight |

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

## 8. Evaluation Cheat Sheet (Scan in < 1 min)
| Aspect | Summary |
|--------|---------|
| Objective | Seasonal ranking & classification with transparent, reproducible pipeline |
| Classification | 4 phases: structural indices → prototype similarity → lexicon logits → arbitration (rule-based) |
| Ranking Formula | `Q = (kb*season_avg + nb_valid_ratings*valid_avg_rating)/(kb+nb_valid_ratings)`; `Pop_Weight = (1 - exp(-reviews/kpop))^gamma`; `Final = Q * Pop_Weight` |
| Shrinkage Rationale | Prevent early volatility; few ratings regress to seasonal baseline |
| Popularity Curve | Saturating exponential avoids runaway advantage for very large review counts |
| Data Quality | Exclude rating==0 from valid averages; canonical `*_latest.csv` artifacts for stable UI |
| Removed Feature | Correlation matrix dropped (low actionable value vs added cognitive load) |
| Confidence | Derived from blended structural + lexical logits with penalties on disagreement |
| Naming Consistency | UI uses Main Dish / Dessert / Beverage; raw data kept as `plat/dessert/boisson` |
| Robustness | Fallback to system interpreter if Poetry env missing; seasonal baseline guards sparse periods |
| Limitations | Manual prototypes & lexicons; no time decay in ranking; rule-based arbitration |
| Future Work | Learn embeddings, sentiment-adjusted popularity, dynamic season segmentation, calibrated confidence |

## 9. Documentation & Tests
```bash
# Build docs locally
poetry run sphinx-build -b html docs docs/_build/html

# Run tests (unit + integration)
poetry run pytest -q
```
If the GitHub Pages site looks empty right after a push, wait ~1–2 minutes (deployment job) then hard refresh (Ctrl+Shift+R). Ensure the link points to the repository root: `https://<user>.github.io/cooking-assistant/`.
Coverage threshold: 90% (current > 90%).

## 10. Configuration
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

## 11. Contributing
Branch naming: `feat/`, `fix/`, `docs/`. Run tests + docs build before PR.

## 12. License
MIT (see `LICENSE`).

---
### Why Separate Justifications?
To keep the README lean while preserving deep analytical work. All reasoning remains versioned under `analysis_parameter_justification/` and surfaced via direct links & published Sphinx docs.

