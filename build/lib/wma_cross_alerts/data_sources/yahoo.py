from datetime import datetime
from typing import Optional

import pandas as pd
import yfinance as yf

from wma_cross_alerts.utils.logger import get_logger


logger = get_logger("yahoo_data_source")


def fetch_daily_close(
    symbol: str,
    start: str = "2000-01-01",
    end: Optional[str] = None,
) -> pd.Series:
    logger.info(f"Descargando datos diarios para {symbol}")

    if end is None:
        end = datetime.utcnow().strftime("%Y-%m-%d")

    try:
        df = yf.download(
            tickers=[symbol],
            start=start,
            end=end,
            interval="1d",
            progress=False,
            auto_adjust=False,
            multi_level_index=False,
        )
    except TypeError:
        df = yf.download(
            tickers=[symbol],
            start=start,
            end=end,
            interval="1d",
            progress=False,
            auto_adjust=False,
        )

    if df is None or df.empty:
        logger.warning(f"No se han recibido datos para {symbol}")
        return pd.Series(dtype="float64", name="Close")

    if isinstance(df.columns, pd.MultiIndex):
        if "Close" not in df.columns.get_level_values(0):
            raise ValueError("Columna Close no encontrada")
        close = df.xs("Close", axis=1, level=0)
    else:
        if "Close" not in df.columns:
            raise ValueError("Columna Close no encontrada")
        close = df["Close"]

    if isinstance(close, pd.DataFrame):
        close = close.squeeze("columns")

    close = close.dropna()
    close.name = "Close"

    logger.info(
        f"Datos descargados para {symbol}: {len(close)} filas desde {close.index.min().date()} hasta {close.index.max().date()}"
    )

    return close
