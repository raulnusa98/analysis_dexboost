import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.backends.backend_pdf import PdfPages
import json

FEATURES = ['MarketCap', 'TotalLiquidity', 'Amount', 'RugScore', 'TokenAge', 'TotalLPProviders', 'IsPump']
PALETTE = {"0": "#FF6B6B", "1": "#4ECDC4"}

plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("husl")

# Load parameters
with open("data/parameters.txt", "r") as f:
    params = json.load(f)
manual_limits = params.get("eda_limits", {})

def get_upper_limit(column, df):
    """
    Determines the upper limit for plotting based on parameters file or default to 95th percentile.
    """
    value = manual_limits.get(column)
    if value is not None:
        try:
            return float(value)
        except:
            pass
    return df[column].quantile(0.95)

def plot_distributions(df, column, bins=50):
    df_plot = df.copy()
    if column not in df_plot.columns or 'IsWorthIt' not in df_plot.columns:
        return None

    upper_limit = get_upper_limit(column, df_plot)
    df_plot = df_plot[df_plot[column] <= upper_limit]

    fig, ax = plt.subplots(figsize=(8, 4))
    sns.histplot(df_plot[df_plot['IsWorthIt'] == 1][column],
                 color=PALETTE["1"], kde=True, bins=bins, label='IsWorthIt=1', alpha=0.5)
    sns.histplot(df_plot[df_plot['IsWorthIt'] == 0][column],
                 color=PALETTE["0"], kde=True, bins=bins, label='IsWorthIt=0', alpha=0.5)

    mean1 = df_plot[df_plot['IsWorthIt'] == 1][column].mean()
    mean0 = df_plot[df_plot['IsWorthIt'] == 0][column].mean()
    ax.text(0.95, 0.95, f"Mean WorthIt=1: {mean1:.2f}\nMean WorthIt=0: {mean0:.2f}",
            transform=ax.transAxes, ha='right', va='top', fontsize=8)

    ax.set_title(f"Distribution of {column}")
    ax.set_xlabel(column)
    ax.set_ylabel("Frequency")
    ax.ticklabel_format(style='plain', axis='x')
    ax.legend()

    plt.tight_layout()
    plt.close(fig)

    return fig

def plot_liquidity_marketcap_ratio(df):
    """
    Plots the distribution of the MarketCap / TotalLiquidity ratio.
    """
    df = df.copy()
    df["MarketCap_to_Liquidity"] = df["MarketCap"] / (df["TotalLiquidity"] + 1)
    df = df[df["MarketCap_to_Liquidity"] < 50]  # Clip extreme outliers

    fig, ax = plt.subplots(figsize=(8, 4))
    sns.histplot(df[df['IsWorthIt'] == 1]["MarketCap_to_Liquidity"],
                 color=PALETTE["1"], kde=True, bins=50, label='IsWorthIt=1', alpha=0.5)
    sns.histplot(df[df['IsWorthIt'] == 0]["MarketCap_to_Liquidity"],
                 color=PALETTE["0"], kde=True, bins=50, label='IsWorthIt=0', alpha=0.5)

    ax.set_title("MarketCap / TotalLiquidity Ratio")
    ax.set_xlabel("Ratio")
    ax.set_ylabel("Frequency")
    ax.ticklabel_format(style='plain', axis='x')
    ax.legend()
    plt.tight_layout()
    plt.close(fig)
    return fig

def generate_eda_report(df_summary, output_path="data/output_data/eda_report.pdf"):
    with PdfPages(output_path) as pdf:
        for feature in FEATURES:
            fig = plot_distributions(df_summary, feature)
            if fig:
                pdf.savefig(fig)
                plt.close(fig)

        # Extra plot: MarketCap / TotalLiquidity ratio
        ratio_fig = plot_liquidity_marketcap_ratio(df_summary)
        pdf.savefig(ratio_fig)
        plt.close(ratio_fig)

    print(f"[✓] EDA report saved to: {output_path}")



