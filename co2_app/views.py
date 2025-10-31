from django.shortcuts import render
from django.http import HttpResponse
import io
import pandas as pd
import plotly.express as px

from .config import CO2_COL, COUNTRY_COL, YEAR_COL, CAT_URL
from .data_service import (
    load_data,
    compute_nan_counts,
    aggregate_top_emitters,
)


def index(request):
    """Main dashboard view"""
    clean_df, raw_df = load_data(True)

    # Year bounds
    min_year, max_year = int(clean_df[YEAR_COL].min()), int(clean_df[YEAR_COL].max())

    # Controls via query params
    def _int(name: str, default: int, min_v: int, max_v: int) -> int:
        try:
            val = int(request.GET.get(name, default))
        except Exception:
            val = default
        return max(min_v, min(max_v, val))

    start_year = _int("start_year", max(min_year, 1950), min_year, max_year)
    end_year = _int("end_year", max_year, min_year, max_year)
    if start_year > end_year:
        start_year, end_year = end_year, start_year
    top_n = _int("top_n", 10, 1, 30)
    show_missing = request.GET.get("show_missing", "0") == "1"
    show_raw = request.GET.get("show_raw", "0") == "1"

    # Histogram (Plotly)
    fig_hist = px.histogram(clean_df, x=CO2_COL, nbins=60, title="Histogram of CO2 per Capita")
    hist_json = fig_hist.to_json()

    # Top emitters
    agg_df = aggregate_top_emitters(clean_df, start_year, end_year, top_n)
    table_html = agg_df.to_html(index=False, classes=["table", "table-sm", "table-striped"])
    fig_bar = None
    bar_json = None
    if not agg_df.empty:
        fig_bar = px.bar(
            agg_df,
            x=CO2_COL,
            y=COUNTRY_COL,
            orientation="h",
            title=f"Top {len(agg_df)} Average CO2 per Capita {start_year}-{end_year}",
            text=CO2_COL,
        )
        fig_bar.update_layout(yaxis={"categoryorder": "total ascending"})
        bar_json = fig_bar.to_json()

    # Missing table/chart
    nan_table_html = None
    nan_bar_json = None
    if show_missing:
        nan_counts = compute_nan_counts(raw_df)
        if not nan_counts.empty:
            nan_table_html = nan_counts.to_html(index=False, classes=["table", "table-sm", "table-striped"])        
            fig_nan = px.bar(
                nan_counts.head(25), x=COUNTRY_COL, y="Missing CO2", title="Top countries by missing CO2 rows"
            )
            nan_bar_json = fig_nan.to_json()

    # Raw head
    raw_head_html = raw_df.head(20).to_html(index=False, classes=["table", "table-sm", "table-striped"]) if show_raw else None

    # Schema/summary
    buffer = io.StringIO()
    clean_df.info(buf=buffer)
    info_text = buffer.getvalue()
    describe_html = clean_df.describe(include="all").to_html(classes=["table", "table-sm", "table-striped"])

    return render(request, "index.html", {
        "cat_url": CAT_URL,
        "min_year": min_year,
        "max_year": max_year,
        "start_year": start_year,
        "end_year": end_year,
        "top_n": top_n,
        "show_missing": show_missing,
        "show_raw": show_raw,
        "hist_json": hist_json,
        "bar_json": bar_json,
        "table_html": table_html,
        "nan_table_html": nan_table_html,
        "nan_bar_json": nan_bar_json,
        "raw_head_html": raw_head_html,
        "info_text": info_text,
        "describe_html": describe_html,
    })


def data_exploration(request):
    """Data exploration page with 3D Iris scatter plot"""
    df = px.data.iris()
    fig = px.scatter_3d(
        df,
        x="sepal_length",
        y="sepal_width",
        z="petal_length",
        color="species",
        color_discrete_map={"setosa": "red", "versicolor": "green", "virginica": "blue"},
        size="petal_width",
        title="Iris 3D Scatter",
    )
    fig_json = fig.to_json()
    return render(request, "pages/data_exploration.html", {
        "cat_url": CAT_URL,
        "fig_json": fig_json
    })


def time_series(request):
    """Time series page for country-specific CO2 data"""
    clean_df, _raw = load_data(True)

    all_countries = sorted(clean_df[COUNTRY_COL].unique())
    selected_country = request.GET.get("country", (all_countries[0] if all_countries else ""))

    min_year, max_year = int(clean_df[YEAR_COL].min()), int(clean_df[YEAR_COL].max())
    def _int(name: str, default: int, min_v: int, max_v: int) -> int:
        try:
            val = int(request.GET.get(name, default))
        except Exception:
            val = default
        return max(min_v, min(max_v, val))

    start_year = _int("start_year", min_year, min_year, max_year)
    end_year = _int("end_year", max_year, min_year, max_year)
    if start_year > end_year:
        start_year, end_year = end_year, start_year
    rolling_window = _int("rolling", 1, 1, 25)
    use_log = request.GET.get("log", "0") == "1"
    show_table = request.GET.get("table", "1") == "1"

    country_df = clean_df[(clean_df[COUNTRY_COL] == selected_country) &
                          (clean_df[YEAR_COL] >= start_year) &
                          (clean_df[YEAR_COL] <= end_year)].copy()
    country_df.sort_values(by=YEAR_COL, inplace=True)

    if rolling_window > 1 and not country_df.empty:
        country_df[f"Rolling {rolling_window}y"] = (
            country_df[CO2_COL].rolling(window=rolling_window, min_periods=1).mean()
        )

    fig_json = None
    if not country_df.empty:
        fig = px.line(
            country_df,
            x=YEAR_COL,
            y=CO2_COL,
            title=f"CO2 Per Capita - {selected_country} ({start_year}-{end_year})",
            markers=True,
        )
        if rolling_window > 1:
            fig.add_scatter(
                x=country_df[YEAR_COL],
                y=country_df[f"Rolling {rolling_window}y"],
                mode="lines",
                name=f"Rolling {rolling_window}y mean",
                line=dict(width=3),
            )
        if use_log:
            fig.update_yaxes(type="log")
        fig.update_layout(yaxis_title="CO2 per Capita (metric tons)")
        fig_json = fig.to_json()

    table_html = country_df.reset_index(drop=True).to_html(index=False, classes=["table", "table-sm", "table-striped"]) if (show_table and not country_df.empty) else None

    return render(request, "pages/time_series.html", {
        "cat_url": CAT_URL,
        "countries": all_countries,
        "selected_country": selected_country,
        "min_year": min_year,
        "max_year": max_year,
        "start_year": start_year,
        "end_year": end_year,
        "rolling_window": rolling_window,
        "use_log": use_log,
        "show_table": show_table,
        "fig_json": fig_json,
        "table_html": table_html,
    })


def download_csv(request):
    """Download CSV data for selected country and year range"""
    clean_df, _raw = load_data(True)
    
    def _int_safe(name: str, default: int) -> int:
        try:
            return int(request.GET.get(name, default))
        except (ValueError, TypeError):
            return default

    country = request.GET.get("country", "")
    start_year = _int_safe("start_year", int(clean_df[YEAR_COL].min()))
    end_year = _int_safe("end_year", int(clean_df[YEAR_COL].max()))

    df = clean_df[(clean_df[COUNTRY_COL] == country) &
                  (clean_df[YEAR_COL] >= start_year) &
                  (clean_df[YEAR_COL] <= end_year)].copy()
    csv_bytes = df.to_csv(index=False).encode("utf-8")
    filename = f"co2_{country}_{start_year}_{end_year}.csv"
    
    response = HttpResponse(csv_bytes, content_type="text/csv")
    response["Content-Disposition"] = f"attachment; filename={filename}"
    return response

