import os
import pandas as pd
from typing import Tuple
from django.core.cache import cache
from .config import DATA_URL, LOCAL_PATH, SEPARATOR, CO2_COL, COUNTRY_COL, YEAR_COL
import urllib.request


def download_if_needed() -> str:
    os.makedirs("data", exist_ok=True)
    if not os.path.exists(LOCAL_PATH):
        # Add headers to avoid 403 Forbidden
        req = urllib.request.Request(
            DATA_URL,
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        )
        with urllib.request.urlopen(req) as response:
            content = response.read()
        
        # Save the content
        with open(LOCAL_PATH, 'wb') as f:
            f.write(content)
    return LOCAL_PATH


def load_data(drop_na: bool = True) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Return (clean_df, raw_df) where clean_df may have NA in CO2 removed.
    raw_df keeps original (after download)."""
    cache_key = f"load_data_{drop_na}"
    cached = cache.get(cache_key)
    if cached:
        return cached
    
    path = download_if_needed()
    raw = pd.read_csv(path, sep=SEPARATOR)
    clean = raw.dropna(subset=[CO2_COL]) if drop_na else raw.copy()
    result = (clean, raw)
    cache.set(cache_key, result, 600)
    return result


def compute_nan_counts(raw_df: pd.DataFrame) -> pd.DataFrame:
    # Note: Cache key simplified - in production, consider using DataFrame hash
    cache_key = "compute_nan_counts"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached
    
    nan_df = raw_df[[COUNTRY_COL]].copy()
    nan_df["Missing CO2"] = raw_df[[CO2_COL]].isna()
    nan_df = (
        nan_df.groupby(COUNTRY_COL)
        .sum(numeric_only=True)
        .sort_values(by="Missing CO2", ascending=False)
    )
    nan_df = nan_df[nan_df["Missing CO2"] > 0].reset_index()
    cache.set(cache_key, nan_df, 600)
    return nan_df


def aggregate_top_emitters(df: pd.DataFrame, start_year: int, end_year: int, top_n: int) -> pd.DataFrame:
    cache_key = f"aggregate_top_emitters_{start_year}_{end_year}_{top_n}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached
    
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
    cache.set(cache_key, grouped, 600)
    return grouped
