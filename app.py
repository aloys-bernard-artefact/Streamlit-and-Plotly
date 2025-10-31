import os
import io
import pandas as pd
import seaborn as sns
import plotly.express as px
import streamlit as st
import matplotlib.pyplot as plt
from typing import Tuple
import requests  # TODO: remove if no other network calls remain

# Fun global effects
st.snow()

# Sidebar celebration and cats
def show_cat(sidebar: bool = True):
    """Display a cat image directly from a URL.
    Streamlit can render images from a URL without manual requests.
    """
    url = "https://upload.wikimedia.org/wikipedia/commons/thumb/7/74/A-Cat.jpg/960px-A-Cat.jpg?20101227100718"
    if sidebar:
        st.sidebar.image(url, caption="Cat", use_container_width=True)
    else:
        st.image(url, caption="Cat", use_container_width=True)

DATA_URL = "https://storage.googleapis.com/schoolofdata-datasets/Data-Analysis.Data-Visualization/CO2_per_capita.csv"
# Path en dur 
LOCAL_PATH = "data/CO2_per_capita.csv"
SEPARATOR = ";"
CO2_COL = "CO2 Per Capita (metric tons)"
COUNTRY_COL = "Country Name"
YEAR_COL = "Year"

st.set_page_config(page_title="CO2 Per Capita Explorer", layout="wide")

# ---------------------- Data Loading ---------------------- #
@st.cache_data(show_spinner=True)
def download_if_needed() -> str:
    os.makedirs("data", exist_ok=True)
    if not os.path.exists(LOCAL_PATH):
        df_remote = pd.read_csv(DATA_URL, sep=SEPARATOR)
        df_remote.to_csv(LOCAL_PATH, sep=SEPARATOR, index=False)
    return LOCAL_PATH

@st.cache_data(show_spinner=True)
def load_data(drop_na: bool = True) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Return (clean_df, raw_df) where clean_df may have NA in CO2 removed.
    raw_df keeps original (after download)."""
    path = download_if_needed()
    raw = pd.read_csv(path, sep=SEPARATOR)
    clean = raw.dropna(subset=[CO2_COL]) if drop_na else raw.copy()
    return clean, raw

# ---------------------- Helper Computations ---------------------- #
@st.cache_data(show_spinner=False)
def compute_nan_counts(raw_df: pd.DataFrame) -> pd.DataFrame:
    nan_df = raw_df[[COUNTRY_COL]].copy()
    nan_df["Missing CO2"] = raw_df[[CO2_COL]].isna()
    nan_df = (
        nan_df.groupby(COUNTRY_COL)
        .sum(numeric_only=True)
        .sort_values(by="Missing CO2", ascending=False)
    )
    nan_df = nan_df[nan_df["Missing CO2"] > 0].reset_index()
    return nan_df

@st.cache_data(show_spinner=False)
def aggregate_top_emitters(df: pd.DataFrame, start_year: int, end_year: int, top_n: int) -> pd.DataFrame:
    mask = (df[YEAR_COL] >= start_year) & (df[YEAR_COL] <= end_year)
    filtered = df.loc[mask, [COUNTRY_COL, YEAR_COL, CO2_COL]].copy()
    if filtered.empty:
        return pd.DataFrame(columns=[COUNTRY_COL, CO2_COL])
    grouped = (
        filtered
        .groupby(COUNTRY_COL)[CO2_COL]
        .mean()
        .sort_values(ascending=False)
        .head(top_n)
        .reset_index()
    )
    return grouped

# ---------------------- UI Sidebar ---------------------- #
st.sidebar.title("Controls 🛠️")
if st.sidebar.button("Celebrate! 🎈"):
    st.balloons()
show_cat(sidebar=True)
clean_df, raw_df = load_data(drop_na=True)

min_year, max_year = int(clean_df[YEAR_COL].min()), int(clean_df[YEAR_COL].max())
def_years = (max(min_year, 1950), max_year)

year_range = st.sidebar.slider(
    "Select year range", min_year, max_year, def_years, step=1
)

top_n = st.sidebar.number_input("Top N emitters", min_value=1, max_value=30, value=10, step=1)

show_plotly = st.sidebar.toggle("Use Plotly (otherwise seaborn)", value=True)
show_missing = st.sidebar.checkbox("Show missing CO2 per country", value=False)
show_raw = st.sidebar.checkbox("Show raw dataset head", value=False)

st.sidebar.markdown("---")
st.sidebar.caption("Data cached locally. Reload the app to force re-download.")

# ---------------------- Main Title ---------------------- #
st.title("🌍 CO2 Per Capita Explorer")
show_cat(sidebar=False)
st.write(
    "Interactive exploration of per-capita CO2 emissions. Use the sidebar to set the year range and number of top emitting countries to display."
)

# ---------------------- Dataset Overview ---------------------- #
with st.expander("Dataset overview / schema"):
    buffer = io.StringIO()
    clean_df.info(buf=buffer)
    st.text(buffer.getvalue())
    st.markdown("**Summary statistics**")
    st.dataframe(clean_df.describe(include="all"))

if show_raw:
    st.subheader("Raw Data (first 20 rows)")
    st.dataframe(raw_df.head(20))

# ---------------------- Missing Values (Optional) ---------------------- #
if show_missing:
    st.subheader("Countries with missing CO2 entries")
    nan_counts = compute_nan_counts(raw_df)
    if nan_counts.empty:
        st.info("No missing CO2 values in dataset.")
    else:
        st.dataframe(nan_counts)
        if show_plotly:
            fig_nan = px.bar(
                nan_counts.head(25),
                x=COUNTRY_COL,
                y="Missing CO2",
                title="Top countries by missing CO2 rows",
            )
            st.plotly_chart(fig_nan, use_container_width=True)
        else:
            fig, ax = plt.subplots(figsize=(10, 4))
            sns.barplot(data=nan_counts.head(25), x=COUNTRY_COL, y="Missing CO2", ax=ax)
            ax.set_title("Top countries by missing CO2 rows")
            ax.set_xlabel("")
            ax.set_ylabel("Count of missing rows")
            ax.tick_params(axis='x', rotation=70)
            st.pyplot(fig)

# ---------------------- Distribution ---------------------- #
st.subheader("Distribution of CO2 Per Capita")
if show_plotly:
    fig_hist = px.histogram(clean_df, x=CO2_COL, nbins=60, title="Histogram of CO2 per Capita")
    st.plotly_chart(fig_hist, use_container_width=True)
else:
    fig, ax = plt.subplots(figsize=(8, 4))
    sns.histplot(clean_df, x=CO2_COL, ax=ax, bins=60)
    ax.set_title("Histogram of CO2 per Capita")
    st.pyplot(fig)

# ---------------------- Top Emitters ---------------------- #
st.subheader("Top Emitters (Average CO2 per Capita)")
start_year, end_year = year_range
agg_df = aggregate_top_emitters(clean_df, start_year, end_year, top_n)

if agg_df.empty:
    st.warning("No data in the selected year range.")
else:
    st.dataframe(agg_df, use_container_width=True, hide_index=True)
    if show_plotly:
        fig_bar = px.bar(
            agg_df,
            x=CO2_COL,
            y=COUNTRY_COL,
            orientation='h',
            title=f"Top {len(agg_df)} Average CO2 per Capita {start_year}-{end_year}",
            text=CO2_COL,
        )
        fig_bar.update_layout(yaxis={'categoryorder': 'total ascending'})
        st.plotly_chart(fig_bar, use_container_width=True)
    else:
        fig, ax = plt.subplots(figsize=(8, 0.5 * len(agg_df) + 1))
        sns.barplot(data=agg_df, x=CO2_COL, y=COUNTRY_COL, ax=ax)
        ax.set_title(f"Top {len(agg_df)} Average CO2 per Capita {start_year}-{end_year}")
        st.pyplot(fig)

# ---------------------- Footer ---------------------- #
st.markdown("---")
st.caption(
    "Built from exploratory notebook: filtered by year, grouped by country, averaged and displayed as top N bar chart."
)
