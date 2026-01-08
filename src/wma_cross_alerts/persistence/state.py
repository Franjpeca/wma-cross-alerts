from typing import Dict, Optional

from wma_cross_alerts.persistence.storage import load_events
from wma_cross_alerts.utils.logger import get_logger


logger = get_logger("event_state")


def already_registered(
    symbol: str,
    signal: str,
    date: str
) -> bool:
    """
    Comprueba si un evento ya fue registrado anteriormente.
    """

    events = load_events(symbol=symbol)

    for event in events:
        if (
            event.get("symbol") == symbol
            and event.get("signal") == signal
            and event.get("date") == date
        ):
            logger.info(
                f"Evento ya registrado: {symbol} {signal} {date}"
            )
            return True

    return False
