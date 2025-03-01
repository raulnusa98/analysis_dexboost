import os
import sqlite3
import pandas as pd
import logging
from typing import Optional

logging.basicConfig(level=logging.WARNING)  # Solo mostrar warnings y errores

def conectar_db(ruta_db: str) -> sqlite3.Connection:
    """
    Conecta a una base de datos SQLite.

    Args:
        ruta_db (str): Ruta al archivo de la base de datos.

    Returns:
        sqlite3.Connection: Conexión a la base de datos SQLite.
    """
    try:
        conn = sqlite3.connect(ruta_db)
        logging.info(f"Conexión exitosa a la base de datos: {ruta_db}")
        return conn
    except sqlite3.Error as e:
        logging.error(f"Error al conectar con la base de datos: {e}")
        raise

def cerrar_conexion(conn: Optional[sqlite3.Connection]) -> None:
    """
    Cierra la conexión a la base de datos SQLite.

    Args:
        conn (Optional[sqlite3.Connection]): Conexión a cerrar.
    """
    try:
        if conn:
            conn.close()
            logging.info("Conexión cerrada correctamente.")
    except sqlite3.Error as e:
        logging.error(f"Error al cerrar la conexión: {e}")
        raise

def cargar_tabla(conn: sqlite3.Connection, tabla: str) -> pd.DataFrame:
    """
    Carga una tabla de SQLite en un DataFrame de pandas.

    Args:
        conn (sqlite3.Connection): Conexión a la base de datos.
        tabla (str): Nombre de la tabla a cargar.

    Returns:
        pd.DataFrame: Datos de la tabla cargada en un DataFrame.
    """
    try:
        logging.info(f"Cargando tabla '{tabla}' desde la base de datos.")
        query = f"SELECT * FROM {tabla}"
        df = pd.read_sql(query, conn)
        logging.info(f"Tabla '{tabla}' cargada con éxito. {len(df)} filas encontradas.")
        return df
    except sqlite3.DatabaseError as e:
        logging.error(f"Error al cargar la tabla '{tabla}': {e}")
        raise

def guardar_tabla(conn: sqlite3.Connection, df: pd.DataFrame, tabla: str) -> None:
    """
    Guarda un DataFrame en una tabla de SQLite.

    Args:
        conn (sqlite3.Connection): Conexión a la base de datos SQLite.
        df (pd.DataFrame): DataFrame a guardar.
        tabla (str): Nombre de la tabla donde se guardará el DataFrame.
    """
    try:
        df.to_sql(tabla, conn, if_exists="replace", index=False)
        logging.info(f"Datos guardados exitosamente en la tabla '{tabla}' ({len(df)} filas).")
    except Exception as e:
        logging.error(f"Error al guardar la tabla '{tabla}': {e}")
        raise

def get_latest_db(folder_path: str) -> str:
    """
    Devuelve la ruta al archivo de base de datos más reciente en el directorio especificado.

    Args:
        folder_path (str): Ruta al directorio que contiene las bases de datos.

    Returns:
        str: Ruta al archivo de base de datos más reciente.
    """
    try:
        db_files = [os.path.join(folder_path, f) for f in os.listdir(folder_path) if f.endswith(".db")]
        if not db_files:
            raise FileNotFoundError("No se encontraron archivos .db en la carpeta especificada.")

        latest_file = max(db_files, key=os.path.getmtime)
        logging.info(f"Base de datos más reciente encontrada: {latest_file}")
        return latest_file
    except Exception as e:
        logging.error(f"Error al obtener la base de datos más reciente: {e}")
        raise

if __name__ == "__main__":
    pass

