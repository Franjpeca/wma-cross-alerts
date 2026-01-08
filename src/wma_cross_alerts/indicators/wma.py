import numpy as np
import pandas as pd

from wma_cross_alerts.utils.logger import get_logger


logger = get_logger("wma_indicator")


def wma(series, period: int) -> pd.Series:
    if period <= 0:
        raise ValueError("El periodo de la WMA debe ser mayor que 0")

    if isinstance(series, pd.DataFrame):
        if series.shape[1] != 1:
            raise TypeError("Si series es DataFrame, debe tener exactamente 1 columna")
        series = series.squeeze("columns")

    if isinstance(series, np.ndarray):
        if series.ndim == 2 and 1 in series.shape:
            series = series.reshape(-1)
        elif series.ndim != 1:
            raise TypeError("Si series es ndarray, debe ser 1D o (n,1)/(1,n)")

    if not isinstance(series, pd.Series):
        series = pd.Series(series)

    logger.info(f"Calculando WMA(period={period})")

    weights = np.arange(1, period + 1, dtype=float)
    weight_sum = weights.sum()

    def _calc(prices: np.ndarray) -> float:
        return float(np.dot(prices, weights) / weight_sum)

    out = series.rolling(window=period, min_periods=period).apply(_calc, raw=True)
    out.name = f"WMA{period}"
    return out
