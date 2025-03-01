import matplotlib.pyplot as plt
from scipy.signal import find_peaks
from matplotlib.backends.backend_pdf import PdfPages
import matplotlib.image as mpimg
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
import pandas as pd

def calculate_event_data(df, distance, tp_threshold, sl_threshold):
    """
    A partir de un DataFrame ya filtrado y ordenado, calcula:
      - Los picos y valles.
      - El precio inicial.
      - Los valores de TP y SL.
      - El evento (TP, SL o No trigger) y su momento/precio.
      - El efecto porcentual sobre el precio inicial.
    
    Retorna un diccionario con estos datos.
    """
    # Asegurarse de que el DataFrame esté ordenado por 'TimeSinceBoostStart'
    df = df.sort_values(by='TimeSinceBoostStart')
    time_diff = df['TimeSinceBoostStart']
    prices = df['Price']

    peaks, _ = find_peaks(prices, distance=distance)
    troughs, _ = find_peaks(-prices, distance=distance)

    initial_price = prices.iloc[0]
    tp_value = initial_price * tp_threshold
    sl_value = initial_price * sl_threshold

    tp_event = df[df['Price'] >= tp_value]
    sl_event = df[df['Price'] <= sl_value]

    tp_time = tp_price = None
    sl_time = sl_price = None

    if not tp_event.empty:
        tp_time = tp_event.iloc[0]['TimeSinceBoostStart']
        tp_price = tp_event.iloc[0]['Price']
    if not sl_event.empty:
        sl_time = sl_event.iloc[0]['TimeSinceBoostStart']
        sl_price = sl_event.iloc[0]['Price']

    if tp_time is not None and sl_time is not None:
        if tp_time <= sl_time:
            event = 'TP'
            event_time = tp_time
            event_price = tp_price
        else:
            event = 'SL'
            event_time = sl_time
            event_price = sl_price
    elif tp_time is not None:
        event = 'TP'
        event_time = tp_time
        event_price = tp_price
    elif sl_time is not None:
        event = 'SL'
        event_time = sl_time
        event_price = sl_price
    else:
        event = 'No trigger'
        event_time = time_diff.iloc[-1]
        event_price = prices.iloc[-1]
    
    effect = ((event_price - initial_price) / initial_price) * 100

    return {
       'time_diff': time_diff,
       'prices': prices,
       'peaks': peaks,
       'troughs': troughs,
       'initial_price': initial_price,
       'tp_value': tp_value,
       'sl_value': sl_value,
       'event': event,
       'event_time': event_time,
       'event_price': event_price,
       'effect': effect
    }

def plot_price_evolution(time_diff, prices, peaks, troughs, initial_price,
                         event, event_time, event_price, effect,
                         title, annotation_factors, event_marker_style='image',
                         image_path="icons/jate.png"):
    """
    Grafica la evolución de precio incluyendo:
      - La línea de precios.
      - Picos (máximos) y valles (mínimos) con sus anotaciones.
      - El marcador del evento (TP/SL) que se mostrará con imagen o con scatter.
    
    Parámetros:
      - annotation_factors: tupla con el factor para ajustar la posición del texto para máximos y mínimos.
        (por ejemplo, (1.1, 0.9) en el PDF o (1.05, 0.95) en el plot interactivo).
      - event_marker_style: 'image' para usar la imagen o cualquier otro valor para usar un scatter.
    
    Retorna la figura generada.
    """
    plt.figure(figsize=(12, 6))
    plt.plot(time_diff, prices, label='Price', color='black')
    plt.scatter(time_diff.iloc[peaks], prices.iloc[peaks], color='red', label='Max', zorder=5)
    plt.scatter(time_diff.iloc[troughs], prices.iloc[troughs], color='blue', label='Min', zorder=5)
    plt.axhline(y=initial_price, color='green', linestyle='--', label=f"1st price ({initial_price:.6f})")

    # Anotaciones para máximos y mínimos
    for peak in peaks:
        peak_variation = ((prices.iloc[peak] - initial_price) / initial_price) * 100
        plt.text(time_diff.iloc[peak], prices.iloc[peak] * annotation_factors[0],
                 f"{peak_variation:.1f}%\n{int(time_diff.iloc[peak])}s",
                 color='red', fontsize=8, ha='center')
    for trough in troughs:
        trough_variation = ((prices.iloc[trough] - initial_price) / initial_price) * 100
        plt.text(time_diff.iloc[trough], prices.iloc[trough] * annotation_factors[1],
                 f"{trough_variation:.1f}%\n{int(time_diff.iloc[trough])}s",
                 color='blue', fontsize=8, ha='center')

    # Marcador para el evento TP/SL
    if event_marker_style == 'image':
        try:
            img = mpimg.imread(image_path)
        except Exception as e:
            print(f"Error loading image '{image_path}':", e)
            img = None
        if img is not None:
            im = OffsetImage(img, zoom=0.15)
            ab = AnnotationBbox(im, (event_time, event_price), frameon=False)
            ax = plt.gca()
            ax.add_artist(ab)
        # Dummy scatter para que aparezca el label en la leyenda
        plt.scatter([], [], color='none', label=f"{event}: {effect:.1f}%")
    else:
        marker_color = 'magenta' if event == 'TP' else ('cyan' if event == 'SL' else 'gray')
        plt.scatter(event_time, event_price, color=marker_color, label=f'Evento: {event}', zorder=6, s=100, marker='D')
        plt.text(event_time, event_price, f"{event}\n{int(event_time)}s\n{effect:.1f}%", color=marker_color, fontsize=8, ha='center')

    plt.title(title)
    plt.xlabel("Seconds since first transaccion")
    plt.ylabel("Price")
    plt.legend()
    plt.grid(True)
    return plt.gcf()

def plot_with_peaks_by_token_mint(token_df, token_mint, boost_id, distance, tp_threshold=1.05, sl_threshold=0.95):
    """
    Genera y muestra un gráfico de evolución de precio para un token y BoostID específicos.
    Se usan factores de anotación (1.05 y 0.95) y se marca el evento TP/SL con un scatter.
    """
    filtered_df = token_df[(token_df['TokenMint'] == token_mint) & (token_df['BoostID'] == boost_id)]
    if filtered_df.empty:
        print(f"Data not found for TokenMint: {token_mint} and BoostID: {boost_id}")
        return

    data = calculate_event_data(filtered_df, distance, tp_threshold, sl_threshold)
    title = f"Price evolution chart - TokenMint: {token_mint}, BoostID: {boost_id}"
    fig = plot_price_evolution(
        data['time_diff'], data['prices'], data['peaks'], data['troughs'], data['initial_price'],
        data['event'], data['event_time'], data['event_price'], data['effect'],
        title=title,
        annotation_factors=(1.025, 0.975),
        event_marker_style='scatter'
    )
    plt.show()

def plot_and_save_peaks(token_df, output_pdf, distance=25, max_boost_id=1, tp_threshold=1.5, sl_threshold=0.65):
    """
    Genera gráficos de evolución de precio (con máximos, mínimos y detección TP/SL) para cada token
    (hasta el BoostID máximo) y los guarda en un PDF. Además, añade al final:
      - Una tabla con la simulación del trade (cada trade con capital fijo 200€).
      - Una página final con un resumen de indicadores.
    
    En estos gráficos se usan factores de anotación (1.1 y 0.9) y se marca el evento TP/SL con una imagen.
    """
    filtered_tokens = token_df[token_df['BoostID'] <= max_boost_id]
    simulation_results = []

    with PdfPages(output_pdf) as pdf:
        # Generación de gráficos por TokenMint y BoostID
        for token_mint in filtered_tokens['TokenMint'].unique():
            token_data = filtered_tokens[filtered_tokens['TokenMint'] == token_mint]
            for boost_id in token_data['BoostID'].unique():
                filtered_df = token_data[token_data['BoostID'] == boost_id]
                if filtered_df.empty:
                    print(f"Data not found for TokenMint: {token_mint} and BoostID: {boost_id}")
                    continue

                data = calculate_event_data(filtered_df, distance, tp_threshold, sl_threshold)
                title = f"Price evolution chart - TokenMint: {token_mint}, BoostID: {boost_id}"
                fig = plot_price_evolution(
                    data['time_diff'], data['prices'], data['peaks'], data['troughs'], data['initial_price'],
                    data['event'], data['event_time'], data['event_price'], data['effect'],
                    title=title,
                    annotation_factors=(1.05, 0.95),
                    event_marker_style='image',
                    image_path="icons/jate.png"
                )
                pdf.savefig(fig)
                plt.close(fig)
                
                simulation_results.append({
                    'TokenMint': token_mint,
                    'Initial Price': data['initial_price'],
                    'Event': data['event'],
                    'Final Price': data['event_price'],
                    'TimeSinceBoost': data['event_time'],
                    'Effect (%)': data['effect']
                })
        
        # --- Tabla de simulación con dinero real (solo al final) ---
        simulation_sorted = sorted(simulation_results, key=lambda x: x['TimeSinceBoost'])
        initial_trade = 200.0  # Capital fijo por trade
        simulation_table = []
        total_profit = 0.0  # Acumulado de beneficio/pérdida

        for r in simulation_sorted:
            final_trade = initial_trade * (1 + r['Effect (%)'] / 100)
            profit = final_trade - initial_trade
            total_profit += profit
            simulation_table.append([
                r['TokenMint'],                    # Mostrar completo
                r['Event'],
                f"{r['Effect (%)']:.2f}%",
                f"{initial_trade:.2f}€",
                f"{final_trade:.2f}€",
                f"{profit:.2f}€"
            ])

        columns = ["TokenMint", "Event", "Effect (%)", "Initial Capital", "Final Capital", "Profit"]

        # Crear una sola página para la tabla de simulación
        fig, ax = plt.subplots(figsize=(11.69, 8.27))
        ax.axis('tight')
        ax.axis('off')
        plt.subplots_adjust(left=0.03, right=0.97, top=0.95, bottom=0.03)

        df_table = pd.DataFrame(simulation_table, columns=columns)
        table = ax.table(cellText=df_table.values, colLabels=df_table.columns, loc='center')
        table.auto_set_font_size(False)
        table.set_fontsize(6)
        table.scale(1, 0.9)
        plt.title("Simulación de trading", fontsize=10)
        pdf.savefig(fig)
        plt.close(fig)
        
        # --- Página final: Resumen de métricas ---
        total_trades = len(simulation_results)
        overall_percentage = (total_profit / (initial_trade * total_trades)) * 100 if total_trades > 0 else 0
        count_tp = sum(1 for r in simulation_results if r['Event'] == 'TP')
        count_sl = sum(1 for r in simulation_results if r['Event'] == 'SL')
        count_no_positive = sum(1 for r in simulation_results if r['Event'] == 'No trigger' and r['Effect (%)'] > 0)
        count_no_negative = sum(1 for r in simulation_results if r['Event'] == 'No trigger' and r['Effect (%)'] < 0)
        win_rate = (sum(1 for r in simulation_results if r['Effect (%)'] > 0) / total_trades) * 100 if total_trades > 0 else 0
        avg_effect = (sum(r['Effect (%)'] for r in simulation_results) / total_trades) if total_trades > 0 else 0
        unique_tokens = set(r['TokenMint'] for r in simulation_results)
        rugpull_tokens = set(r['TokenMint'] for r in simulation_results if r['Effect (%)'] <= -50)
        rugpull_percentage = (len(rugpull_tokens) / len(unique_tokens)) * 100 if unique_tokens else 0

        summary_data = [
            ["TP", count_tp],
            ["SL", count_sl],
            ["No trigger positive", count_no_positive],
            ["No trigger negative", count_no_negative],
            ["Total trades", total_trades],
            ["Win rate", f"{win_rate:.1f}%"],
            ["Avg Effect", f"{avg_effect:.2f}%"],
            ["Rugpull %", f"{rugpull_percentage:.1f}%"],
            ["Total Profit", f"{total_profit:.2f}€"],
            ["Overall %", f"{overall_percentage:.1f}%"]
        ]
        
        fig, ax = plt.subplots(figsize=(11.69, 8.27))
        ax.axis('tight')
        ax.axis('off')
        summary_table = ax.table(cellText=summary_data, colLabels=["Métrica", "Valor"], loc='center')
        summary_table.auto_set_font_size(False)
        summary_table.set_fontsize(10)
        summary_table.scale(1, 1.5)
        plt.title("Resumen", fontsize=12)
        pdf.savefig(fig)
        plt.close(fig)
    
    print(f"PDF saved at {output_pdf}")

if __name__ == "__main__":
    # Código de prueba o ejemplo si es necesario
    pass

