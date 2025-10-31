<div align="center">

# Cooking Assistant
**Season-aware recipe ranking, classification & interactive exploration**

[Documentation (GitHub Pages)](https://lounishamroun.github.io/cooking-assistant/) · [Classifier Justification](analysis_parameter_justification/README_food_type_classifier_justification.md) · [Bayesian Parameter Justification](analysis_parameter_justification/bayesian_parameters_docs_justification.md)

</div>

## 1. Quick Evaluation (Teacher / Reviewer)
Fast path using pre-generated processed CSVs.

```bash
git clone https://github.com/lounishamroun/cooking-assistant.git
cd cooking-assistant
poetry install
poetry run streamlit run app/streamlit/streamlit_app.py
```
Open http://localhost:8501.

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

## 5. Regenerate Data Manually
```bash
poetry run python scripts/01_classifier_generator.py
poetry run python scripts/enrich_metrics.py
poetry run python scripts/top_recipe_rankings.py
```

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
poetry run sphinx-build -b html docs docs/_build/html
poetry run pytest -q
```
Coverage threshold: 90% (current > 90%).

## 9. Configuration
Edit `cooking_assistant/config.py` for paths & Bayesian parameters. Environment:
```
STRICT_REAL_DATA=1
```
Optional `LOG_FILE` for pipeline logging.

## 10. Contributing
Branch naming: `feat/`, `fix/`, `docs/`. Run tests + docs build before PR.

## 11. License
MIT (see `LICENSE`).

---
### Why Separate Justifications?
To keep the README lean while preserving deep analytical work. All reasoning remains versioned under `analysis_parameter_justification/` and surfaced via direct links & published Sphinx docs.

