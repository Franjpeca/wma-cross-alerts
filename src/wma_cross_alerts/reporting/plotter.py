from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from wma_cross_alerts.utils.logger import get_logger
from wma_cross_alerts.data_sources.yahoo import fetch_daily_close
from wma_cross_alerts.indicators.wma import wma
from wma_cross_alerts.signals.golden_cross_wma import last_cross_up

logger = get_logger("plotter")


def plot_golden_cross(
    *,
    symbol: str,
    market: str,
    signal_name: str,
    event_date: str,
    short_period: int,
    long_period: int,
    window_sessions: int = 300,
    start_buffer: int = 10,
) -> Path:
    """
    Genera y guarda una grafica del Golden Cross para una fecha concreta.

    La grafica se guarda en:
    data/charts/<signal>/<market>/<symbol>/<date>_<symbol>_<signal>.png
    """

    logger.info(
        f"Generando grafica {signal_name} para {symbol} ({market}) en {event_date}"
    )

    # Descargar historico suficiente hasta la fecha del evento
    close = fetch_daily_close(
        symbol=symbol,
        end=event_date,
    )

    if close.empty or len(close) < long_period + start_buffer:
        raise ValueError("Datos insuficientes para generar la grafica")

    # Ventana visual
    close = close.tail(window_sessions)

    wma_short = wma(close, short_period)
    wma_long = wma(close, long_period)

    # Ruta de salida
    charts_dir = (
        Path("data")
        / "charts"
        / signal_name
        / market
        / symbol
    )
    charts_dir.mkdir(parents=True, exist_ok=True)

    filename = f"{event_date}_{symbol}_{signal_name}.png"
    output_path = charts_dir / filename

    # --- Plot ---
    plt.figure(figsize=(12, 6))

    plt.plot(close.index, close, label="Close", alpha=0.4)
    plt.plot(wma_short.index, wma_short, label=f"WMA {short_period}", linewidth=2)
    plt.plot(wma_long.index, wma_long, label=f"WMA {long_period}", linewidth=2)

    # Marcar el cruce exactamente en la fecha del evento
    event_ts = pd.to_datetime(event_date)

    if event_ts in close.index:
        plt.scatter(
            event_ts,
            close.loc[event_ts],
            color="green",
            s=100,
            zorder=5,
            label="Golden Cross",
        )

    plt.title(f"{symbol} – Golden Cross WMA ({event_date})")
    plt.xlabel("Fecha")
    plt.ylabel("Precio")
    plt.legend()
    plt.grid(True)

    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()

    logger.info(f"Grafica guardada en {output_path}")
    
    return output_path
