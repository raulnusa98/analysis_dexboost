# Dexboost Tokens Analysis

This project explores new tokens launched on the Solana-Raydium blockchain (a.k.a. shitcoins). The goal is to analyze their behavior right after launch — focusing on early metrics like market cap, liquidity, number of liquidity pool providers, token age (in minutes), etc.

The idea came from a separate project where I was parsing token prices every 10 seconds and trying to identify patterns that could help filter out scams or low-potential tokens.

In this repo, I build a clean pipeline and a full notebook to study whether certain tokens are "worth it" — based on a binary label I created called `IsWorthIt`. The main goal is:

> Train a basic model to see which features are most important to explain this label, and use that insight to filter tokens using a Python script and generate a PDF with the final results.

So, the typical flow is:
1. Run the notebook to explore data and validate that certain metrics (e.g. market cap or token age) are consistently useful.
2. Based on the SHAP results and distributions, set your manual filters inside `parameters.txt`.
3. Run `main.py` to apply those filters, generate a filtered token report, and export an optional EDA PDF.

## About the data

The dataset used in this project comes from another private repo, which collects token information from Raydium launches in real-time. The data is gathered after a token gets boosted using the Dexboost Telegram bot, which acts as the trigger to start tracking prices and metrics. 

⚠️ I don’t own the original scraping/collection script, so this repo doesn't include the full raw dataset.
However, the pipeline is fully compatible with any database that follows the same structure (i.e. tokens detected through Dexboost, with metrics like PriceHistory, MarketCap, etc.).⚠️

If you are collecting similar data with Dexboost's detection system, this repo should be helpful to analyze the data.

## Project structure

dexboost/
│
├── data/                        # Contains DB, filtered tokens and PDF reports
│   ├── output_data/             # Output folder for filtered_tokens.pdf & eda_report.pdf
│   ├── main_backup.db           # SQLite token data (not included in repo)
│   └── parameters.txt           # Main config (filters, plot limits, etc.)
│
├── env_scripts/                 # Modular code used by main.py
    ├── db_utils.py              # Connects to sqlite3 db and loads raw tables
    ├── eda.py                   # Generates EDA report
│   ├── pipeline.py              # Unifies preprocessing + summary + target
│   ├── plot_utils.py            # Price evolution charts and PDF generator with tokens passing the filters
│   ├── preprocessing.py         # Cleans data, explodes price data, correct dtypes, etc.
│   └── target_definition.py     # Little script to handle IsWorthIt conditions. Very easy to add or eliminate conditionals regarding what you would consider Worth It
│
├── notebooks/
│   └── modeling_analysis.ipynb  # Model training, tuning & exploration
│
│
├── main.py                      # Run this to launch full pipeline
├── .gitignore                   # Hides data, envs, logs, etc.
└── README.md                    # You’re here

## How it works

**1. Input**: The project reads from a SQLite database with token metrics and price history.

**2. Filtering**: Applies custom logic from parameters.txt to filter what we care about (e.g. liquidity, token age).

**3. PDF Output**: Generates 2 reports:

    filtered_tokens.pdf → shows only the tokens passing the filters and each chart has indicators whether a Take profit or Stop Loss was triggered.

    eda_report.pdf → shows feature distributions (MarketCap, RugScore, etc.).

**4. ML Classification**: Uses a tuned XGBoost model to predict IsWorthIt and explain the predictions with SHAP. This is inside the notebook and you can touch as many hyperparameters as you desire.

## Config: parameters.txt

You can customize some parameters here (looking forward to add more parameters to edit, such as TP, SL etc.)

`{
  "db_path": "data/main_backup.db",
  "max_seconds": 5000,
  "filters": {
    "TokenAge": "<=200",
    "TotalLiquidity": "<=500000",
    "MarketCap": ">=500000"
  },
  "eda_limits": {
    "TokenAge": 500,
    "TotalLiquidity": 200000,
    "MarketCap": 200000,
    "Amount": 2000,
    "RugScore": 15000,
    "TotalLPProviders": 20
  },
  "output_pdf": "data/output_data/filtered_tokens.pdf"
}
`

## Modeling summary

- Trained an basic XGBoost classifier (plus Random Forest for comparison)
- Focused on early features only: 'Marketcap', 'TokenAge', 'Liquidity', etc
- Validated performance using AUC + SHAP plots
- Hyperparameters optimized via 'RandomizedSearchCV'

## Output samples

- EDA plots of feature distributions, classified by colors whether the token is worth it or not.
- SHAP summary + waterfall charts (optional in notebook)
- Filtered Token table with final selections

## Author
Made with Python by Raúl
Reach out if you want to collab or adapt this to other chains/tokens!

