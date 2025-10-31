"""Time Series CO2 Per Capita Page

Allows user to select a single country and visualize the evolution of CO2 per capita
emissions over time. Controls: country select, year range, optional rolling mean,
log scale toggle, and CSV download of the filtered data.
No caching or shared utils per user request.
"""
import os
import pandas as pd
import plotly.express as px
import streamlit as st

st.snow()

def show_cat(sidebar: bool = True):
    url = "https://upload.wikimedia.org/wikipedia/commons/thumb/7/74/A-Cat.jpg/960px-A-Cat.jpg?20101227100718"
    if sidebar:
        st.sidebar.image(url, caption="Cat", use_container_width=True)
    else:
        st.image(url, caption="Cat", use_container_width=True)

DATA_URL = "https://storage.googleapis.com/schoolofdata-datasets/Data-Analysis.Data-Visualization/CO2_per_capita.csv"
LOCAL_PATH = "data/CO2_per_capita.csv"
SEPARATOR = ";"
CO2_COL = "CO2 Per Capita (metric tons)"
COUNTRY_COL = "Country Name"
YEAR_COL = "Year"

st.sidebar.title("Extras 🎉")
if st.sidebar.button("Celebrate! 🎈"):
    st.balloons()
show_cat(sidebar=True)

st.title("📈 CO2 Per Capita Time Series")
show_cat(sidebar=False)
st.write("Select a country to explore its per-capita CO2 emission trajectory across years.")

# ---------------------- Data Load (no cache) ---------------------- #
os.makedirs("data", exist_ok=True)
if not os.path.exists(LOCAL_PATH):
    # Direct read from URL then save locally to keep same dataset between pages
    df_remote = pd.read_csv(DATA_URL, sep=SEPARATOR)
    df_remote.to_csv(LOCAL_PATH, sep=SEPARATOR, index=False)

df = pd.read_csv(LOCAL_PATH, sep=SEPARATOR)

# Clean NA rows for target column (keep for completeness if user wants) but we remove NaN for plotting
clean_df = df.dropna(subset=[CO2_COL])

# ---------------------- Controls ---------------------- #
all_countries = sorted(clean_df[COUNTRY_COL].unique())
selected_country = st.selectbox("Country", all_countries, index=0)

min_year, max_year = int(clean_df[YEAR_COL].min()), int(clean_df[YEAR_COL].max())
year_range = st.slider(
    "Year range", min_year, max_year, (min_year, max_year), step=1
)

rolling_window = st.number_input(
    "Rolling mean window (years)", min_value=1, max_value=25, value=1, step=1,
    help="Set to >1 to smooth the line with a rolling mean."
)

use_log = st.checkbox(
    "Log scale (y-axis)", value=False,
    help="Apply logarithmic scale to CO2 per capita axis"
)
show_table = st.checkbox("Show data table", value=True)

# ---------------------- Filter & Transform ---------------------- #
start_year, end_year = year_range
country_df = clean_df[(clean_df[COUNTRY_COL] == selected_country) &
                      (clean_df[YEAR_COL] >= start_year) &
                      (clean_df[YEAR_COL] <= end_year)].copy()

country_df.sort_values(by=YEAR_COL, inplace=True)

if rolling_window > 1 and not country_df.empty:
    country_df[f"Rolling {rolling_window}y"] = (
        country_df[CO2_COL].rolling(window=rolling_window, min_periods=1).mean()
    )

# ---------------------- Plot ---------------------- #
if country_df.empty:
    st.warning("No data available for the selected filters.")
else:
    y_col = CO2_COL
    fig = px.line(
        country_df,
        x=YEAR_COL,
        y=y_col,
        title=f"CO2 Per Capita - {selected_country} ({start_year}-{end_year})",
        markers=True,
    )
    if rolling_window > 1:
        fig.add_scatter(
            x=country_df[YEAR_COL],
            y=country_df[f"Rolling {rolling_window}y"],
            mode="lines",
            name=f"Rolling {rolling_window}y mean",
            line=dict(width=3)
        )
    if use_log:
        fig.update_yaxes(type="log")
    fig.update_layout(yaxis_title="CO2 per Capita (metric tons)")
    st.plotly_chart(fig, use_container_width=True)

# ---------------------- Table & Download ---------------------- #
if show_table and not country_df.empty:
    st.subheader("Filtered Data")
    st.dataframe(country_df.reset_index(drop=True))

    csv_bytes = country_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="Download CSV",
        data=csv_bytes,
        file_name=f"co2_{selected_country}_{start_year}_{end_year}.csv",
        mime="text/csv"
    )

# ---------------------- Footer ---------------------- #
st.markdown("---")
st.caption("Time series built without caching or code refactor per user instruction.")
