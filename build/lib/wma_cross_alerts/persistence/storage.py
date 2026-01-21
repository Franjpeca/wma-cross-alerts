import json
from pathlib import Path
from typing import Dict, List

from wma_cross_alerts.utils.logger import get_logger


logger = get_logger("event_storage")

BASE_EVENTS_DIR = Path("data") / "events"
BASE_EVENTS_DIR.mkdir(parents=True, exist_ok=True)


def save_event(event: Dict) -> Path:
    """
    Guarda un evento en formato JSON en:
    data/events/<signal>/<market>/<symbol>/<fecha>_<symbol>_<signal>.json
    """

    signal = event["signal"]
    market = event["market"]
    symbol = event["symbol"]

    filename = f"{event['date']}_{symbol}_{signal}.json"

    event_dir = (
        BASE_EVENTS_DIR
        / signal
        / market
        / symbol
    )
    event_dir.mkdir(parents=True, exist_ok=True)

    path = event_dir / filename

    with open(path, "w", encoding="utf-8") as f:
        json.dump(event, f, indent=2, ensure_ascii=False)

    logger.info(f"Evento guardado: {path}")
    return path


def load_events(
    *,
    signal: str | None = None,
    market: str | None = None,
    symbol: str | None = None,
) -> List[Dict]:
    """
    Carga eventos filtrando opcionalmente por signal, market y/o symbol.
    """

    base_dir = BASE_EVENTS_DIR

    if signal:
        base_dir = base_dir / signal
    if market:
        base_dir = base_dir / market
    if symbol:
        base_dir = base_dir / symbol

    if not base_dir.exists():
        return []

    events = []

    for file in base_dir.rglob("*.json"):
        try:
            with open(file, "r", encoding="utf-8") as f:
                events.append(json.load(f))
        except Exception as e:
            logger.error(f"Error leyendo evento {file}: {e}")

    return events
