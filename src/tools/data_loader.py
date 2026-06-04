# src/tools/data_loader.py
"""
Data loading and preprocessing utilities for data-confessions.
Loads and merges Chicago crime and weather data (2018-2023).
"""

import pandas as pd
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent.parent / "data" / "raw"


def load_crime_data() -> pd.DataFrame:
    """
    Load and preprocess Chicago crime data.
    - Parses dates
    - Extracts date-only column for merging
    """
    df = pd.read_csv(DATA_DIR / "crime.csv")
    df["date"] = pd.to_datetime(df["date"])
    df["date_only"] = df["date"].dt.date
    return df


def load_weather_data() -> pd.DataFrame:
    """
    Load and preprocess Chicago weather data.
    - Renames columns to clean names
    - Parses dates
    """
    df = pd.read_csv(DATA_DIR / "weather.csv")
    df = df.rename(columns={
        "time": "date",
        "precipitation_sum (mm)": "precipitation_mm",
        "temperature_2m_max (°C)": "temp_max_c",
        "temperature_2m_min (°C)": "temp_min_c",
        "rain_sum (mm)": "rain_mm",
    })
    df["date"] = pd.to_datetime(df["date"], format="%m/%d/%y")
    df["date_only"] = df["date"].dt.date
    return df


def load_merged_data() -> pd.DataFrame:
    """
    Merge crime and weather data on date.
    Returns daily crime counts joined with weather variables.
    """
    crime = load_crime_data()
    weather = load_weather_data()

    # Aggregate crime to daily counts
    daily_crime = (
        crime.groupby("date_only")
        .agg(
            crime_count=("primary_type", "count"),
            arrests=("arrest", "sum"),
        )
        .reset_index()
    )

    # Merge on date
    merged = daily_crime.merge(weather, on="date_only", how="inner")
    merged = merged.sort_values("date_only").reset_index(drop=True)

    return merged


if __name__ == "__main__":
    df = load_merged_data()
    print(f"Merged dataset: {df.shape}")
    print(df.columns.tolist())
    print(df.head())
    print(f"\nDate range: {df['date_only'].min()} to {df['date_only'].max()}")
    print(f"Avg daily crimes: {df['crime_count'].mean():.1f}")
    print(f"Rainy days: {(df['precipitation_mm'] > 0).sum()}")