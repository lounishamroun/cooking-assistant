# Getting Started

Install dependencies (Poetry) and run the pipeline:

1. Install: `poetry install`
2. Generate data & metrics: `poetry run python app/main.py`
3. Launch demo UI: `poetry run streamlit run app/streamlit/streamlit_app.py`

Set `DEMO_MODE=1` to use bundled small CSV artifacts instead of full raw data.
