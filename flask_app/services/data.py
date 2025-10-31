import os
import pandas as pd
from typing import Tuple
from ..config import DATA_URL, LOCAL_PATH, SEPARATOR, CO2_COL, COUNTRY_COL, YEAR_COL


def download_if_needed() -> str:
    os.makedirs("data", exist_ok=True)
    if not os.path.exists(LOCAL_PATH):
        df_remote = pd.read_csv(DATA_URL, sep=SEPARATOR)
        df_remote.to_csv(LOCAL_PATH, sep=SEPARATOR, index=False)
    return LOCAL_PATH


def load_data(drop_na: bool = True) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Return (clean_df, raw_df) where clean_df may have NA in CO2 removed.
    raw_df keeps original (after download)."""
    path = download_if_needed()
    raw = pd.read_csv(path, sep=SEPARATOR)
    clean = raw.dropna(subset=[CO2_COL]) if drop_na else raw.copy()
    return clean, raw


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
