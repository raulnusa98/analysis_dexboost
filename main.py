import os
import pandas as pd
import sqlite3
from datetime import datetime, timedelta
from env_scripts.db_utils import conectar_db, cargar_tabla, cerrar_conexion
from env_scripts.processing import parse_to_flat_format
from env_scripts.plot_utils import plot_and_save_peaks


BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # Directorio base
os.chdir(BASE_DIR)  # Asegurar que trabajamos en la ruta correcta

def copy_db_to_memory(database_path):
    """
    Crea una copia en memoria de la base de datos SQLite sin problemas de transacción.
    """
    disk_conn = sqlite3.connect(database_path)
    mem_conn = sqlite3.connect(":memory:")
    
    # Copiar datos correctamente
    disk_conn.backup(mem_conn)  
    disk_conn.close()
    
    return mem_conn

def main():
    print(">>> Initializing main.py execution...")
    filters_path = os.path.join(BASE_DIR, 'data', 'filters.txt')

    # Cargar configuración desde filters.txt
    try:
        with open(filters_path, 'r') as f:
            config = eval(f.read())
        print(f">>> Loaded configuration: {config}")
    except Exception as e:
        print(f"Error loading configuration from {filters_path}: {e}")
        return

    database_path = "C:\\Programing\\Dexboost\\Dexboost-hunter\\src\\data\\main.db"
    output_pdf = config.get("output_pdf")
    filters = config.get("filters")
    distance = config.get("distance", 10)

    print("Connecting to database and creating in-memory backup...")
    conn = copy_db_to_memory(database_path)

    try:
        print("Loading analysis table from database...")
        df = cargar_tabla(conn, 'analysisLiquidityPool')
        print(f"Amount of rows loaded: {len(df)}")

        # Convertir Time a datetime y filtrar últimos 7 días
        df['Time'] = pd.to_datetime(df['Time'])
        seven_days_ago = pd.to_datetime(datetime.now() - timedelta(days=7)).tz_localize("UTC")
        df = df[df['Time'] >= seven_days_ago]

        # Procesar datos PRIMERO
        print("Processing data...")
        processed_df = parse_to_flat_format(df)
        print(f"Data processed successfully. Rows: {len(processed_df)}")

        # Aplicar filtros sobre processed_df
        print("Applying filters...")
        for col, condition in filters.items():
            if col in processed_df.columns:
                try:
                    processed_df = processed_df.query(f"{col} {condition}")
                except Exception as e:
                    print(f"Error applying filter {col} {condition}: {e}")
            else:
                print(f"Warning: Column '{col}' not found in dataset, skipping filter.")
        
        print(f"Data filtered. Rows remaining: {len(processed_df)}")

        # Generar gráficos y guardarlos en PDF
        print("Generating graphics from tokens that passed filters...")
        plot_and_save_peaks(processed_df, output_pdf, distance, max_boost_id=1)
        print(f"Process completed! Check {output_pdf}")

    except Exception as e:
        print(f"Error during execution: {e}")

    finally:
        cerrar_conexion(conn)

if __name__ == "__main__":
    main()

