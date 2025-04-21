import os
import pandas as pd
import sqlite3
from datetime import datetime, timedelta

from env_scripts.db_utils import get_latest_db, connect_db, close_connection, load_table
from env_scripts.preprocessing import initial_processing, parse_price_history
from env_scripts.plot_utils import plot_and_save_tokens
from env_scripts.eda import generate_eda_report
from env_scripts.target_definition import define_is_worth_it

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
PARAMS_PATH = os.path.join(ROOT_DIR, 'data', 'parameters.txt')

def copy_db_to_memory(database_path):
    """
    Copies a SQLite database from disk to memory for faster processing.

    Args:
        database_path (str): Path to the SQLite database file.

    Returns:
        sqlite3.Connection: In-memory database connection.
    """
    disk_conn = sqlite3.connect(database_path)
    mem_conn = sqlite3.connect(":memory:")
    disk_conn.backup(mem_conn)
    disk_conn.close()
    return mem_conn

def load_and_filter_data(conn, days_back=None):
    """
    Loads data from the database and filters it by date if specified.

    Args:
        conn (sqlite3.Connection): Active database connection.
        days_back (int or None): Number of days to look back from today.

    Returns:
        pd.DataFrame: Filtered raw data.
    """
    df_raw = load_table(conn, 'analysisLiquidityPool')
    if 'DetectedAt' not in df_raw.columns:
        raise KeyError("Missing required column: 'DetectedAt'")
    df_raw['DetectedAt'] = pd.to_datetime(df_raw['DetectedAt'], utc=True)
    df_raw['DetectedAt'] = df_raw['DetectedAt'].dt.tz_localize(None)

    if days_back is not None:
        cutoff_time = datetime.utcnow() - timedelta(days=days_back)
        df_raw = df_raw[df_raw['DetectedAt'] >= cutoff_time]
        print(f"Filtered to last {days_back} days: {len(df_raw)} rows")
    else:
        print("Analyzing all available data")
    return df_raw

def process_price_data(df_raw):
    """
    Cleans and parses raw data to extract price history and prepare it for analysis.

    Args:
        df_raw (pd.DataFrame): Raw input data from the database.

    Returns:
        tuple: Cleaned dataframe, and dataframe exploded with price history.
    """
    df_clean = initial_processing(df_raw)
    df_prices = parse_price_history(df_clean)
    return df_clean, df_prices

def summarize_token_behavior(df_prices):
    """
    Aggregates price and token metrics per TokenMint to build a summary DataFrame.

    Args:
        df_prices (pd.DataFrame): Parsed token price history.

    Returns:
        pd.DataFrame: Summary of token behavior including IsWorthIt target.
    """
    df_summary = (
        df_prices.groupby("TokenMint")
        .agg({
            "TokenName": "first",
            "DetectedAt": "first",
            "MarketCap": "first",
            "TotalLiquidity": "first",
            "Amount": "first",
            "RugScore": "first",
            "TokenAge": "first",
            "PriceVariation_%": ["max", "min"],
            "TimeSinceBoostStart": ["idxmax", "idxmin"],
            "Trigger": "first"
        }).reset_index()
    )
    df_summary.columns = ['TokenMint', 'TokenName', 'DetectedAt', 'MarketCap', 'TotalLiquidity', 'Amount',
                          'RugScore', 'TokenAge', 'MaxPriceVar', 'MinPriceVar', 'MaxPriceIdx', 'MinPriceIdx', 'FirstTrigger']

    df_summary['MaxPriceSeconds'] = df_prices.loc[df_summary['MaxPriceIdx'], 'TimeSinceBoostStart'].values
    df_summary['MinPriceSeconds'] = df_prices.loc[df_summary['MinPriceIdx'], 'TimeSinceBoostStart'].values
    df_summary['SecondsTrigger'] = df_prices.loc[df_prices.groupby("TokenMint")['Trigger'].idxmax(), 'TimeSinceBoostStart'].values
    df_summary['HasRugPull'] = 0
    df_summary['RugPullSeconds'] = 9999
    df_summary['IsWorthIt'] = df_summary.apply(define_is_worth_it, axis=1)
    return df_summary

def apply_filters(df, filters):
    """
    Applies filtering conditions (e.g., from parameters.txt) to a DataFrame.

    Args:
        df (pd.DataFrame): Data to be filtered.
        filters (dict): Dictionary of column -> condition (e.g., {"TokenAge": "< 10"}).

    Returns:
        pd.DataFrame: Filtered DataFrame.
    """
    for col, condition in filters.items():
        if col in df.columns:
            try:
                df = df.query(f"{col} {condition}")
            except Exception as e:
                print(f"[!] Error applying filter {col} {condition}: {e}")
        else:
            print(f"[!] Warning: Column '{col}' not found. Skipping filter.")
    return df

def generate_reports(df_summary, df_prices, config):
    """
    Generates the EDA report and filtered token price charts as PDFs.

    Args:
        df_summary (pd.DataFrame): Token-level summary including IsWorthIt.
        df_prices (pd.DataFrame): Detailed price history.
        config (dict): Parameters from config file.
    """
    eda_path = os.path.join(ROOT_DIR, "data/output_data", "eda_report.pdf")
    os.makedirs(os.path.join(ROOT_DIR, "data/output_data"), exist_ok=True)
    generate_eda_report(df_summary, eda_path)

    filters = config.get("filters", {})
    summary_filtered = apply_filters(df_summary.copy(), filters)

    if summary_filtered.empty:
        print("[!] No tokens passed the filters.")
        return

    tokens_to_plot = summary_filtered["TokenMint"].unique()
    df_plot = df_prices[df_prices["TokenMint"].isin(tokens_to_plot)]

    output_pdf = config.get("output_pdf", "data/output_data/filtered_tokens.pdf")
    plot_and_save_tokens(df_plot, output_pdf, image_path="icons/jate.png",
                         max_seconds=config.get("max_seconds", None))

    print(f"\n✅ Generated reports:\n - EDA: {eda_path}\n - Filtered tokens: {output_pdf}")

def run_pipeline():
    """
    Main function to execute the Dexboost analysis pipeline.
    Loads config, connects to database, processes data, generates reports.
    """
    print(">>> Starting Dexboost Pipeline\n")
    try:
        with open(PARAMS_PATH, 'r') as f:
            config = eval(f.read())
        print(f"Loaded parameters from {PARAMS_PATH}")
    except Exception as e:
        print(f"[X] Failed to load parameters: {e}")
        return

    db_path = config.get("db_path", get_latest_db("data"))
    max_seconds = config.get("max_seconds", None)
    days_back = config.get("days_back", None)

    conn = copy_db_to_memory(db_path)
    print(f"Connected to database: {db_path}")

    try:
        df_raw = load_and_filter_data(conn, days_back)
        df_clean, df_prices = process_price_data(df_raw)

        if df_prices.empty:
            print("[!] No valid price history found.")
            return

        df_summary = summarize_token_behavior(df_prices)
        print("Calculated IsWorthIt")

        generate_reports(df_summary, df_prices, config)

    except Exception as e:
        print(f"[X] Pipeline error: {e}")
    finally:
        close_connection(conn)
        print(">>> Pipeline finished.")
