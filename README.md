# Django version of CO2 Explorer

This adds a Django app replicating the Streamlit app (`app.py`) and pages (`pages/`).

## Quick start

1. Create venv and install deps:

```bash
pyenv virtualenv 3.11.8 django_app
pyenv local django_app
pip install -r requirements.txt
```

2. Run the Django app:

```bash
python manage.py migrate
python manage.py runserver 8502
```

Open http://127.0.0.1:8502

## Structure

- `co2_explorer/`: Django project settings and URL configuration
- `co2_app/`: Django application
  - `views.py`: View functions (dashboard, data exploration, time series)
  - `urls.py`: URL routing
  - `config.py`: Constants and dataset configuration
  - `data_service.py`: Data loading and aggregations with caching
  - `templates/`: Templates with Plotly charts via JSON
  - `static/`: Bootstrap helpers, confetti, simple snow CSS

## Notes

- CSV is downloaded to `data/CO2_per_capita.csv` if missing (same as Streamlit).
- Plotly-only rendering; no seaborn branch.
- Use query params to control the UI (e.g., `?start_year=1980&end_year=2010&top_n=15`).
- Django's built-in caching is used instead of Flask-Caching.
