def define_is_worth_it(row):
    """
    Determines if a token is worth investing in based on the specified conditions.
    The function checks various conditions related to the token's price history,
    rug pull status, and price variations.

    Returns:
        int: 1 if the token is considered worth it, 0 otherwise.
    """
    if (
        (row['FirstTrigger'] == 'TP' and row['HasRugPull'] == 0) or
        (row['FirstTrigger'] == 'TP' and row['HasRugPull'] == 1 and row['RugPullSeconds'] > row['SecondsTrigger'] + 30) or
        (row['MaxPriceVar'] >= 30 and row['MaxPriceSeconds'] < row['MinPriceSeconds']) or
        (row['MaxPriceVar'] >= 30 and row['MinPriceVar'] < -20 and row['MinPriceSeconds'] < row['MaxPriceSeconds'])
    ):
        return 1
    return 0
