import os
import sqlite3
import pandas as pd
import logging
from typing import Optional

logging.basicConfig(level=logging.WARNING)  # Only show warnings and errors

def connect_db(db_path: str) -> sqlite3.Connection:
    """
    Connects to a SQLite database.

    Args:
        db_path (str): Path to the database file.

    Returns:
        sqlite3.Connection: Connection to SQLite database.
    """
    try:
        conn = sqlite3.connect(db_path)
        logging.info(f"Successfully connected to database: {db_path}")
        return conn
    except sqlite3.Error as e:
        logging.error(f"Error connecting to database: {e}")
        raise

def close_connection(conn: Optional[sqlite3.Connection]) -> None:
    """
    Closes the SQLite database connection.

    Args:
        conn (Optional[sqlite3.Connection]): Connection to close.
    """
    try:
        if conn:
            conn.close()
            logging.info("Connection closed successfully.")
    except sqlite3.Error as e:
        logging.error(f"Error closing connection: {e}")
        raise

def load_table(conn: sqlite3.Connection, table: str) -> pd.DataFrame:
    """
    Loads a SQLite table into a pandas DataFrame.

    Args:
        conn (sqlite3.Connection): Database connection.
        table (str): Name of table to load.

    Returns:
        pd.DataFrame: Table data loaded into DataFrame.
    """
    try:
        logging.info(f"Loading table '{table}' from database.")
        query = f"SELECT * FROM {table}"
        df = pd.read_sql(query, conn)
        logging.info(f"Table '{table}' loaded successfully. {len(df)} rows found.")
        return df
    except sqlite3.DatabaseError as e:
        logging.error(f"Error loading table '{table}': {e}")
        raise

def save_table(conn: sqlite3.Connection, df: pd.DataFrame, table: str) -> None:
    """
    Saves a DataFrame to a SQLite table.

    Args:
        conn (sqlite3.Connection): SQLite database connection.
        df (pd.DataFrame): DataFrame to save.
        table (str): Name of table where DataFrame will be saved.
    """
    try:
        df.to_sql(table, conn, if_exists="replace", index=False)
        logging.info(f"Data successfully saved to table '{table}' ({len(df)} rows).")
    except Exception as e:
        logging.error(f"Error saving table '{table}': {e}")
        raise

def get_latest_db(folder_path: str) -> str:
    """
    Returns the path to the most recent database file in the specified directory.

    Args:
        folder_path (str): Path to directory containing databases.

    Returns:
        str: Path to most recent database file.
    """
    try:
        db_files = [os.path.join(folder_path, f) for f in os.listdir(folder_path) if f.endswith(".db")]
        if not db_files:
            raise FileNotFoundError("No .db files found in specified folder.")

        latest_file = max(db_files, key=os.path.getmtime)
        logging.info(f"Most recent database found: {latest_file}")
        return latest_file
    except Exception as e:
        logging.error(f"Error getting most recent database: {e}")
        raise

def query_table(conn: sqlite3.Connection, query: str) -> pd.DataFrame:
    """
    Executes a SQL query and returns the result as a DataFrame.

    Args:
        conn (sqlite3.Connection): Database connection.
        query (str): SQL query to execute.

    Returns:
        pd.DataFrame: Query result as DataFrame.
    """
    try:
        logging.info(f"Executing custom query:\n{query}")
        df = pd.read_sql_query(query, conn)
        logging.info(f"Query returned {len(df)} rows.")
        return df
    except Exception as e:
        logging.error(f"Error executing query: {e}")
        raise
