from flask import Blueprint, render_template, request, Response
import pandas as pd
import plotly.express as px

from ..config import (
    CAT_URL,
    DATA_URL,
    LOCAL_PATH,
    SEPARATOR,
    CO2_COL,
    COUNTRY_COL,
    YEAR_COL,
)
from ..services.data import load_data
from ..app import cache


bp = Blueprint("pages", __name__)

@bp.get("/pages/data-exploration")
def data_exploration():
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
    return render_template("pages/data_exploration.html", cat_url=CAT_URL, fig_json=fig_json)


@bp.get("/pages/time-series")
def time_series():
    @cache.memoize()  # type: ignore
    def _load(drop_na: bool):
        return load_data(drop_na)

    clean_df, _raw = _load(True)

    all_countries = sorted(clean_df[COUNTRY_COL].unique())
    selected_country = request.args.get("country", (all_countries[0] if all_countries else ""))

    min_year, max_year = int(clean_df[YEAR_COL].min()), int(clean_df[YEAR_COL].max())
    def _int(name: str, default: int, min_v: int, max_v: int) -> int:
        try:
            val = int(request.args.get(name, default))
        except Exception:
            val = default
        return max(min_v, min(max_v, val))

    start_year = _int("start_year", min_year, min_year, max_year)
    end_year = _int("end_year", max_year, min_year, max_year)
    if start_year > end_year:
        start_year, end_year = end_year, start_year
    rolling_window = _int("rolling", 1, 1, 25)
    use_log = request.args.get("log", "0") == "1"
    show_table = request.args.get("table", "1") == "1"

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

    return render_template(
        "pages/time_series.html",
        cat_url=CAT_URL,
        countries=all_countries,
        selected_country=selected_country,
        min_year=min_year,
        max_year=max_year,
        start_year=start_year,
        end_year=end_year,
        rolling_window=rolling_window,
        use_log=use_log,
        show_table=show_table,
        fig_json=fig_json,
        table_html=table_html,
    )


@bp.get("/pages/time-series/download")
def download_csv():
    @cache.memoize()  # type: ignore
    def _load(drop_na: bool):
        return load_data(drop_na)

    clean_df, _raw = _load(True)

    country = request.args.get("country", "")
    start_year = int(request.args.get("start_year", int(clean_df[YEAR_COL].min())))
    end_year = int(request.args.get("end_year", int(clean_df[YEAR_COL].max())))

    df = clean_df[(clean_df[COUNTRY_COL] == country) &
                  (clean_df[YEAR_COL] >= start_year) &
                  (clean_df[YEAR_COL] <= end_year)].copy()
    csv_bytes = df.to_csv(index=False).encode("utf-8")
    filename = f"co2_{country}_{start_year}_{end_year}.csv"
    return Response(csv_bytes, mimetype="text/csv", headers={"Content-Disposition": f"attachment; filename={filename}"})


