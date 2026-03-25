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

    events = []

    # Siempre buscar recursivamente en toda la estructura
    # porque el usuario puede pedir un symbol sin saber el market o signal
    search_dir = BASE_EVENTS_DIR

    if signal:
        search_dir = search_dir / signal
    
    if market and signal:
        search_dir = search_dir / market
        
    if symbol and market and signal:
        search_dir = search_dir / symbol
    
    if not search_dir.exists():
         return []

    # Patrón de búsqueda: si tenemos symbol, buscamos ese archivo específico
    # Si no, buscamos todos
    pattern = "*.json"
    if symbol:
        pattern = f"*{symbol}*.json"

    for file in search_dir.rglob(pattern):
        try:
            with open(file, "r", encoding="utf-8") as f:
                data = json.load(f)
                
            # Filtrado estricto en memoria para asegurar coincidencias
            if signal and data.get("signal") != signal:
                continue
            if market and data.get("market") != market:
                continue
            if symbol and data.get("symbol") != symbol:
                continue
                
            events.append(data)
        except Exception as e:
            logger.error(f"Error leyendo evento {file}: {e}")

    return events
