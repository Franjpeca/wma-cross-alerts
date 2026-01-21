import pandas as pd

from wma_cross_alerts.utils.logger import get_logger


logger = get_logger("golden_cross_signal")


def detect_cross_up(
    wma_short: pd.Series,
    wma_long: pd.Series
) -> pd.Series:
    """
    Detecta cruces al alza (Golden Cross):
    - Ayer:  wma_short <= wma_long
    - Hoy:   wma_short >  wma_long

    Devuelve una Series booleana indexada por fecha.
    """

    if not isinstance(wma_short, pd.Series) or not isinstance(wma_long, pd.Series):
        raise TypeError("wma_short y wma_long deben ser pandas.Series")

    if not wma_short.index.equals(wma_long.index):
        raise ValueError("Las series deben tener el mismo indice temporal")

    logger.info("Detectando Golden Cross (WMA short vs long)")

    prev_condition = wma_short.shift(1) <= wma_long.shift(1)
    curr_condition = wma_short > wma_long

    cross_up = prev_condition & curr_condition

    return cross_up


def last_cross_up(
    wma_short: pd.Series,
    wma_long: pd.Series
) -> bool:
    """
    Devuelve True si el ultimo dia hay un Golden Cross confirmado.
    """

    cross_up = detect_cross_up(wma_short, wma_long)

    if cross_up.empty:
        return False

    return bool(cross_up.iloc[-1])


def all_cross_up(wma_short, wma_long):
    cross = (
        (wma_short.shift(1) <= wma_long.shift(1)) &
        (wma_short > wma_long)
    )

    diff = wma_short - wma_long
    return diff[cross]
