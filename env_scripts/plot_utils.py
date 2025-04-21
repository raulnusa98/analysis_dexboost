import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import matplotlib.image as mpimg
from matplotlib.offsetbox import OffsetImage, AnnotationBbox

def plot_token_price_evolution(token_df, title, annotation_factors=(1.05, 0.95),
                               event_marker_style='scatter', image_path=None,
                               max_seconds=None):
    """
    Plots the price evolution for a token using pre-processed data.

    Parameters:
      token_df: DataFrame for a single token.
      title: Title of the plot.
      annotation_factors: Tuple to adjust annotation position.
      event_marker_style: 'scatter' (default).
      image_path: Deprecated.
      max_seconds: Max seconds to display on X-axis (truncate longer data).
    """
    token_df = token_df.sort_values(by='TimeSinceBoostStart')

    if max_seconds is not None:
        token_df = token_df[token_df['TimeSinceBoostStart'] <= max_seconds]

    time_diff = token_df['TimeSinceBoostStart']
    prices = token_df['price']
    initial_price = prices.iloc[0]

    # Event detection (TP/SL)
    event_candidates = token_df[token_df['Trigger'] != 'No event']
    event_data = event_candidates.iloc[0] if not event_candidates.empty else token_df.iloc[-1]
    event_time = event_data['TimeSinceBoostStart']
    event_price = event_data['price']
    event_trigger = event_data['Trigger']
    effect = event_data['PriceVariation_%']

    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(time_diff, prices, label='Price', color='black')
    ax.axhline(y=initial_price, color='green', linestyle='--',
               label=f"Initial Price ({initial_price:.6f})")

    # Max & Min local points
    try:
        max_idx = token_df['price'].idxmax()
        min_idx = token_df['price'].idxmin()
        max_time = token_df.loc[max_idx, 'TimeSinceBoostStart']
        max_price = token_df.loc[max_idx, 'price']
        min_time = token_df.loc[min_idx, 'TimeSinceBoostStart']
        min_price = token_df.loc[min_idx, 'price']

        ax.scatter(max_time, max_price, color='blue', s=80, marker='^', label='Local Max')
        ax.scatter(min_time, min_price, color='red', s=80, marker='v', label='Local Min')
        ax.annotate(f'Max: {max_price:.2f}', (max_time, max_price), textcoords="offset points", xytext=(0,10), ha='center')
        ax.annotate(f'Min: {min_price:.2f}', (min_time, min_price), textcoords="offset points", xytext=(0,-15), ha='center')
    except Exception as e:
        print(f"[!] Error marking max/min: {e}")

    # TP/SL marker as dot
    marker_color = 'magenta' if event_trigger == 'TP' else ('cyan' if event_trigger == 'SL' else 'gray')
    ax.scatter(event_time, event_price, color=marker_color, s=100, marker='o',
               label=f'{event_trigger}: {effect:.1f}%')

    # Labels and layout
    ax.set_title(title)
    ax.set_xlabel("Seconds since boost start")
    ax.set_ylabel("Price")
    ax.grid(True)
    ax.legend()

    if max_seconds:
        ax.set_xlim(0, max_seconds)

    return fig


def plot_and_save_tokens(token_df, output_pdf, event_marker_style='image',
                         image_path="icons/jate.png", max_seconds=None):
    """
    Generates and saves charts per token into a single PDF.

    Parameters:
      token_df: DataFrame with processed price data.
      output_pdf: Path to save the resulting PDF.
      event_marker_style: 'image' or 'scatter'.
      image_path: Path to image if using image marker.
      max_seconds: X-axis maximum time in seconds.
    """
    with PdfPages(output_pdf) as pdf:
        for token_mint in token_df['TokenMint'].unique():
            token_data = token_df[token_df['TokenMint'] == token_mint]
            title = f"Price Evolution - TokenMint: {token_mint}"
            fig = plot_token_price_evolution(token_data, title,
                                             event_marker_style=event_marker_style,
                                             image_path=image_path,
                                             max_seconds=max_seconds)
            pdf.savefig(fig)
            plt.close(fig)

    print(f"[✓] PDF saved at: {output_pdf}")
