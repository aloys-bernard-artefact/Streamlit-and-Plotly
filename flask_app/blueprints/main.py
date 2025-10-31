from flask import Blueprint, render_template, request
import io
import pandas as pd
import plotly.express as px

from ..config import CO2_COL, COUNTRY_COL, YEAR_COL, CAT_URL
from ..services.data import (
    load_data,
    compute_nan_counts,
    aggregate_top_emitters,
)
from ..app import cache


bp = Blueprint("main", __name__)

@bp.route("/")
def index():
    # Load data (cached by Flask-Caching memoize wrappers)
    @cache.memoize()  # type: ignore
    def _load(drop_na: bool):
        return load_data(drop_na)

    clean_df, raw_df = _load(True)

    # Year bounds
    min_year, max_year = int(clean_df[YEAR_COL].min()), int(clean_df[YEAR_COL].max())

    # Controls via query params
    def _int(name: str, default: int, min_v: int, max_v: int) -> int:
        try:
            val = int(request.args.get(name, default))
        except Exception:
            val = default
        return max(min_v, min(max_v, val))

    start_year = _int("start_year", max(min_year, 1950), min_year, max_year)
    end_year = _int("end_year", max_year, min_year, max_year)
    if start_year > end_year:
        start_year, end_year = end_year, start_year
    top_n = _int("top_n", 10, 1, 30)
    show_missing = request.args.get("show_missing", "0") == "1"
    show_raw = request.args.get("show_raw", "0") == "1"

    # Histogram (Plotly)
    fig_hist = px.histogram(clean_df, x=CO2_COL, nbins=60, title="Histogram of CO2 per Capita")
    hist_json = fig_hist.to_json()

    # Top emitters
    @cache.memoize()  # type: ignore
    def _agg(s: int, e: int, n: int):
        return aggregate_top_emitters(clean_df, s, e, n)

    agg_df = _agg(start_year, end_year, top_n)
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
        @cache.memoize()  # type: ignore
        def _nan():
            return compute_nan_counts(raw_df)

        nan_counts = _nan()
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

    return render_template(
        "index.html",
        cat_url=CAT_URL,
        min_year=min_year,
        max_year=max_year,
        start_year=start_year,
        end_year=end_year,
        top_n=top_n,
        show_missing=show_missing,
        show_raw=show_raw,
        hist_json=hist_json,
        bar_json=bar_json,
        table_html=table_html,
        nan_table_html=nan_table_html,
        nan_bar_json=nan_bar_json,
        raw_head_html=raw_head_html,
        info_text=info_text,
        describe_html=describe_html,
    )


