from __future__ import annotations

from datetime import datetime, timezone, timedelta
from pathlib import Path
import json
import os
import re
from typing import Any

import requests

from wma_cross_alerts.utils.logger import get_logger

logger = get_logger("universe")

try:
    from dotenv import load_dotenv

    load_dotenv()
except Exception:
    pass


CACHE_DIR = Path("data") / "universes"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

DEFAULT_TTL_DAYS = int(os.getenv("UNIVERSE_TTL_DAYS", "0"))
HTTP_TIMEOUT_SECS = float(os.getenv("UNIVERSE_HTTP_TIMEOUT", "20"))
USER_AGENT = os.getenv("UNIVERSE_USER_AGENT", "wma-cross-alerts/1.0")

YFIUA_BASE = "https://yfiua.github.io/index-constituents"
YFIUA_URLS = {
    "sp500": f"{YFIUA_BASE}/constituents-sp500.json",
    "nasdaq100": f"{YFIUA_BASE}/constituents-nasdaq100.json",
}

EXPECTED_COUNTS = {
    "sp500": (450, 520),
    "nasdaq100": (90, 110),
}

_SYMBOL_RE = re.compile(r"^[A-Z0-9][A-Z0-9-]{0,15}$")


def get_universe(market: str, *, force_refresh: bool = False) -> list[str]:
    market = (market or "").strip().lower()
    cache_path = _cache_path(market)
    cached = _read_cache(cache_path)

    if not force_refresh and cached is not None and _is_fresh(cached):
        return list(cached["symbols"])

    try:
        symbols, source = _fetch_universe(market)
        payload = {
            "market": market,
            "source": source,
            "fetched_at_utc": datetime.now(timezone.utc).isoformat(),
            "count": len(symbols),
            "symbols": symbols,
        }
        _write_cache(cache_path, payload)
        return symbols
    except Exception as e:
        if cached is not None:
            logger.warning(
                f"Fallo refrescando universo para {market}; usando cache (source={cached.get('source')}). Error: {e}"
            )
            return list(cached["symbols"])
        raise


def _fetch_universe(market: str) -> tuple[list[str], str]:
    if market not in YFIUA_URLS:
        raise ValueError(f"Mercado no soportado en universe.py: {market}")

    symbols = _fetch_from_yfiua_json(market)
    symbols = _normalize_symbols(symbols)

    _validate_symbols(market, symbols)
    return symbols, "yfiua/index-constituents"


def _fetch_from_yfiua_json(market: str) -> list[str]:
    url = YFIUA_URLS[market]
    headers = {"User-Agent": USER_AGENT, "Accept": "application/json"}
    resp = requests.get(url, headers=headers, timeout=HTTP_TIMEOUT_SECS)
    resp.raise_for_status()

    data: Any = resp.json()
    if not isinstance(data, list):
        raise ValueError(f"Formato inesperado en JSON de universo ({market})")

    out: list[str] = []
    for row in data:
        if isinstance(row, dict):
            sym = row.get("Symbol") or row.get("symbol") or row.get("ticker") or row.get("Ticker")
            if sym:
                out.append(str(sym))
    if not out:
        raise ValueError(f"No se extrajeron simbolos del JSON ({market})")
    return out


def _normalize_symbols(symbols: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for s in symbols:
        sym = _normalize_symbol(s)
        if not sym:
            continue
        if sym not in seen:
            seen.add(sym)
            out.append(sym)
    return out


def _normalize_symbol(s: str) -> str:
    s = (s or "").strip().upper()
    if not s:
        return ""
    s = re.sub(r"\s+", "", s)
    s = s.replace(".", "-")
    return s


def _validate_symbols(market: str, symbols: list[str]) -> None:
    if not symbols:
        raise ValueError("Universo vacio")

    lo, hi = EXPECTED_COUNTS.get(market, (1, 10_000))
    n = len(symbols)
    if not (lo <= n <= hi):
        raise ValueError(f"Recuento inesperado para {market}: {n} (esperado {lo}-{hi})")

    bad = [s for s in symbols if _SYMBOL_RE.match(s) is None]
    if bad:
        raise ValueError(f"Simbolos invalidos detectados en {market} (ej: {bad[:10]})")


def _cache_path(market: str) -> Path:
    return CACHE_DIR / f"{market}.json"


def _read_cache(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            return {
                "market": path.stem,
                "source": "legacy",
                "fetched_at_utc": "1970-01-01T00:00:00+00:00",
                "count": len(data),
                "symbols": data,
            }
        if isinstance(data, dict) and isinstance(data.get("symbols"), list):
            return data
    except Exception:
        return None
    return None


def _write_cache(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    tmp.replace(path)
    logger.info(f"Universo cacheado: {path} (source={payload.get('source')}, count={payload.get('count')})")


def _is_fresh(cached: dict[str, Any]) -> bool:
    ttl_days = DEFAULT_TTL_DAYS
    if ttl_days <= 0:
        return False

    ts = cached.get("fetched_at_utc")
    if not isinstance(ts, str) or not ts:
        return False

    try:
        dt = datetime.fromisoformat(ts)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        age = datetime.now(timezone.utc) - dt.astimezone(timezone.utc)
        return age <= timedelta(days=ttl_days)
    except Exception:
        return False
