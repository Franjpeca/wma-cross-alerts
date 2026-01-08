import matplotlib.pyplot as plt
from wma_cross_alerts.data_sources.yahoo import fetch_daily_close
from wma_cross_alerts.indicators.wma import wma
from wma_cross_alerts.signals.golden_cross_wma import detect_cross_up
import pandas as pd

def plot_golden_cross(symbol: str, start_date: str = "2000-01-01", end_date: str = None, window: int = 300) -> None:
    """
    Genera una gráfica de los cruces dorados (Golden Cross) para el símbolo especificado
    en el intervalo de fechas proporcionado. El rango de fechas por defecto es desde 2000-01-01.
    
    :param symbol: Símbolo del activo (por ejemplo, 'MSFT').
    :param start_date: Fecha de inicio del rango de datos (por defecto, "2000-01-01").
    :param end_date: Fecha de fin del rango de datos (por defecto, el último día disponible).
    :param window: Número de días a mostrar en la gráfica (por defecto, los últimos 300 días).
    """

    # Cargar datos de Yahoo Finance
    close = fetch_daily_close(symbol, start=start_date, end=end_date)

    # Calcular WMA30 y WMA200
    wma30 = wma(close, 30)
    wma200 = wma(close, 200)

    # Obtener los cruces dorados
    crosses = detect_cross_up(wma30, wma200)

    # Seleccionar un intervalo de tiempo para graficar (últimos 'window' días)
    df_window = close.tail(window)
    wma30_window = wma30.tail(window)
    wma200_window = wma200.tail(window)
    crosses_window = crosses.tail(window)

    # Filtrar las fechas donde hay un cruce (True en crosses_window)
    cross_dates = crosses_window[crosses_window].index

    # Crear la gráfica
    plt.figure(figsize=(14, 7))

    plt.plot(df_window.index, df_window, label="Close", alpha=0.4)
    plt.plot(wma30_window.index, wma30_window, label="WMA 30", linewidth=2)
    plt.plot(wma200_window.index, wma200_window, label="WMA 200", linewidth=2)

    # Marcar los cruces dorados en la gráfica
    plt.scatter(
        cross_dates,  # Solo las fechas con cruce
        wma30_window[cross_dates],  # Los valores de WMA30 en esas fechas
        color="green", 
        s=80, 
        label="Golden Cross", 
        zorder=5
    )

    plt.title(f"{symbol} - Golden Cross (WMA30 cruzando al alza WMA200)")
    plt.xlabel("Fecha")
    plt.ylabel("Precio")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()

    # Mostrar la gráfica
    plt.show()

    # Guardar la gráfica si es necesario
    # plt.savefig(f"golden_cross_{symbol}.png")


if __name__ == "__main__":
    # Cambia estos valores según el activo y las fechas
    symbol = "MSFT"  # o "AAPL", "GOOGL", etc.
    start_date = "2015-01-01"
    end_date = "2025-12-31"
    window = 300  # Últimos 300 días

    plot_golden_cross(symbol, start_date, end_date, window)
