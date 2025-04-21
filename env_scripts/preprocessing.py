import numpy as np
import pandas as pd
import json
import re

def initial_processing(df):
    """
    Preprocesseess the DataFrame by converting 'DetectedAt' to datetime, dropping unnecessary columns, and converting data types.
    TokenAge is converted from milliseconds to minutes.
    """

    df = df.copy()
    df['DetectedAt'] = pd.to_datetime(df['DetectedAt'], utc=True, errors='coerce')
    df = df.drop(columns=['id', 'Markets', 'Risks'])
    df['TokenAge'] = df['TokenAge'] / 60000
    column_dtypes = {
        'TokenAge': 'int32', 'Amount': 'int16', 'PubKey': 'string', 'IsLP': 'bool',
        'IsPump': 'bool', 'TokenName': 'string', 'TokenMint': 'string',
        'MarketCap': 'int64', 'TotalLiquidity': 'int32', 'TotalLPProviders': 'int16',
        'RugScore': 'int32'
    }
    df = df.astype(column_dtypes)
    df.reset_index(drop=True, inplace=True)
    return df

def parse_price_history(df, tp=35, sl=-40):
    df = df.copy()

    # Convert DetectedAt
    df['DetectedAt'] = pd.to_datetime(df['DetectedAt'], utc=True, errors='coerce')

    # Clean PriceHistory
    df['PriceHistory'] = df['PriceHistory'].astype(str).str.replace(r'\\"', '"', regex=True).str.strip('"')
    df = df[df['PriceHistory'].notna() & (df['PriceHistory'] != 'nan') & (df['PriceHistory'] != '')]

    # Convert to list of dicts
    df['PriceHistory'] = df['PriceHistory'].apply(lambda x: json.loads(x) if isinstance(x, str) else None)
    df = df[df['PriceHistory'].apply(lambda x: isinstance(x, list) and len(x) > 0)]

    # Get StartPrice
    df['StartPrice'] = [float(x[0].get('price') or x[0].get('Price') or np.nan) for x in df['PriceHistory']]

    # Explode
    df_exploded = df.explode('PriceHistory', ignore_index=True)
    price_data = pd.json_normalize(df_exploded['PriceHistory'])
    price_data.rename(columns={'time': 'PriceTime', 'Time': 'PriceTime', 'price': 'price', 'Price': 'price'}, inplace=True)

    # Time parsing
    price_data['PriceTime'] = pd.to_datetime(price_data['PriceTime'], utc=True, errors='coerce')
    price_data['price'] = pd.to_numeric(price_data['price'], errors='coerce')

    df_exploded = df_exploded.drop(columns=['PriceHistory']).reset_index(drop=True)
    df_exploded = pd.concat([df_exploded, price_data], axis=1)

    df_exploded = df_exploded[df_exploded['PriceTime'].notna()]

    # Filter by time logic
    first_price_time = df_exploded.groupby('TokenMint')['PriceTime'].transform('min')
    mask_valid = first_price_time <= (df_exploded['DetectedAt'] + pd.Timedelta(minutes=1))
    df_exploded = df_exploded[mask_valid]

    df_exploded = df_exploded[df_exploded['DetectedAt'].notna()]

    # Compute derived metrics
    df_exploded['TimeSinceBoostStart'] = (
        (df_exploded['PriceTime'] - df_exploded['DetectedAt'])
        .dt.total_seconds()
        .clip(lower=0)
        .astype('int32')
    )

    df_exploded['PriceVariation_%'] = (
        (df_exploded['price'] - df_exploded['StartPrice']) / df_exploded['StartPrice'] * 100
    ).round(2)

    conditions = [
        df_exploded['PriceVariation_%'] >= tp,
        df_exploded['PriceVariation_%'] <= sl
    ]
    choices = ['TP', 'SL']
    df_exploded['Trigger'] = np.select(conditions, choices, default='No event')

    dtypes = {'price': 'float32', 'TimeSinceBoostStart': 'int32', 'Trigger': 'str'}
    df_exploded = df_exploded.astype(dtypes).reset_index(drop=True)

    return df_exploded






