# Flask version of CO2 Explorer

This adds a Flask app replicating the Streamlit app (`app.py`) and pages (`pages/`).

## Quick start

1. Create venv and install deps:

```bash
pyenv virtualenv 3.11.8 flask_app
pyenv local flask_app
pip install -r requirements.txt
```

2. Run the Flask app:

```bash
export FLASK_APP=flask_app.app:create_app
export FLASK_RUN_PORT=8502
export FLASK_DEBUG=1
flask run
```

Open http://127.0.0.1:8502

## Structure

- `flask_app/app.py`: app factory, cache, blueprints
- `flask_app/config.py`: constants, dataset config
- `flask_app/services/data.py`: data loading and aggregations
- `flask_app/blueprints/main.py`: index route (dashboard)
- `flask_app/blueprints/pages.py`: extra pages (data exploration, time series)
- `flask_app/templates/…`: templates with Plotly charts via JSON
- `flask_app/static/…`: Bootstrap helpers, confetti, simple snow CSS

## Notes

- CSV is downloaded to `data/CO2_per_capita.csv` if missing (same as Streamlit).
- Plotly-only rendering; no seaborn branch.
- Use query params to control the UI (e.g., `?start_year=1980&end_year=2010&top_n=15`).
