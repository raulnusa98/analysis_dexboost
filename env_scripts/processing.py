import pandas as pd
import json
from datetime import datetime

def parse_to_flat_format(df, max_seconds=3000, max_age_days=1):
    """
    Procesa el DataFrame, extrae y normaliza el historial de precios, calcula 
    TokenAge y AdjustedBoostAmount, y prepara los datos para análisis.
    
    Además, filtra filas según la columna CreatedAt, eliminando aquellas 
    con fecha anterior a (ahora - max_age_days).

    Args:
        df (pd.DataFrame): DataFrame original.
        max_seconds (float, optional): Límite máximo para 'TimeSinceBoostStart'. 
                                       Se descartan valores mayores a este límite.
        max_age_days (int, optional): Si se especifica, se eliminan las filas cuyo 
                                      CreatedAt sea anterior a la fecha actual menos 
                                      max_age_days.
    """
    df = df.copy()

    # Convertir StartLiquidity a USD
    df['StartLiquidityUSD'] = df['StartLiquidity'].apply(
        lambda x: json.loads(x.replace("'", '"')).get('usd', 0.0) if pd.notna(x) else 0
    )

    # Parsear y calcular TotalRiskScore
    def calculate_total_risk(risks):
        try:
            if pd.isna(risks) or not risks:
                return 0
            risks_data = json.loads(risks.replace("'", '"')) if isinstance(risks, str) else risks
            return sum(r.get('Score', 0) for r in risks_data)
        except json.JSONDecodeError:
            return 0

    df['TotalRiskScore'] = df['Risks'].apply(calculate_total_risk)

    # Convertir timestamps
    df['CreatedAt'] = pd.to_datetime(df['CreatedAt'], errors='coerce', utc=True)
    df['BoostTime'] = pd.to_datetime(df['Time'], errors='coerce', utc=True)

    # Filtrar filas según CreatedAt (si se especifica el parámetro)
    if max_age_days is not None:
        cutoff_date = pd.Timestamp.utcnow() - pd.Timedelta(days=max_age_days)
        df = df[df['CreatedAt'] >= cutoff_date]

    # Calcular TokenAge en minutos (redondeado a 3 decimales)
    df['TokenAge'] = ((df['BoostTime'] - df['CreatedAt']).dt.total_seconds().round(3)) / 60

    # Asignar BoostID según el orden de BoostTime por TokenMint
    df['BoostID'] = df.groupby('TokenMint')['BoostTime'].rank(method="dense", ascending=True).astype(int)

    # Calcular AdjustedBoostAmount (evitando NaN y negativos)
    df['AdjustedBoostAmount'] = df.groupby('TokenMint')['BoostAmount'].diff()
    mask = df['AdjustedBoostAmount'].isna() | (df['AdjustedBoostAmount'] < 0)
    df.loc[mask, 'AdjustedBoostAmount'] = df.loc[mask, 'BoostAmount']

    # Parsear PriceHistory
    df['PriceHistory'] = (
        df['PriceHistory']
        .astype(str)
        .str.replace(r'\\"', '"', regex=True)
        .str.strip('"')
        .apply(json.loads)
    )

    # Explode del historial de precios
    exploded = df.explode('PriceHistory')
    price_data = pd.json_normalize(exploded['PriceHistory'])
    exploded = exploded.reset_index(drop=True)
    price_data = price_data.reset_index(drop=True)
    flat_df = pd.concat([exploded, price_data], axis=1)

    # Convertir timestamps de precios
    flat_df['PriceTime'] = pd.to_datetime(flat_df['time'].astype(str).str[:19])

    # Convertir la columna Price a float
    flat_df['Price'] = pd.to_numeric(flat_df['price'], errors='coerce')

    # Calcular TimeSinceBoostStart usando BoostTime como referencia
    flat_df['TimeSinceBoostStart'] = (
        flat_df.groupby(['TokenMint', 'BoostTime'])['PriceTime']
        .transform(lambda x: (x - x.min()).dt.total_seconds().round(3))
    )

    # Eliminar filas donde TimeSinceBoostStart supera max_seconds
    if max_seconds is not None:
        flat_df = flat_df[flat_df['TimeSinceBoostStart'] <= max_seconds]

    # Renombrar columna 'time' a 'OriginalPriceTime'
    flat_df = flat_df.rename(columns={'time': 'OriginalPriceTime'})

    return flat_df


if __name__ == "__main__":
    pass


