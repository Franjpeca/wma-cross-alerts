from datetime import datetime, timezone, timedelta
from pathlib import Path
import sys
import argparse

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_PATH = PROJECT_ROOT / "src"

if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from wma_cross_alerts.utils.logger import get_logger
from wma_cross_alerts.core.settings import load_config
from wma_cross_alerts.core.universe import get_universe

from wma_cross_alerts.data_sources.yahoo import fetch_daily_close
from wma_cross_alerts.indicators.wma import wma
from wma_cross_alerts.signals.golden_cross_wma import last_cross_up
from wma_cross_alerts.persistence.storage import save_event
from wma_cross_alerts.persistence.state import already_registered
from wma_cross_alerts.reporting.plotter import plot_golden_cross
from wma_cross_alerts.notifiers.email import (
    send_cross_alert_email,
    send_error_report_email,
)

logger = get_logger("main")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="WMA Golden Cross Alert System")
    parser.add_argument(
        "--date",
        type=str,
        default=None,
        help="Fecha de ejecucion YYYY-MM-DD (cierre evaluado)",
    )
    return parser.parse_args()


def resolve_execution_dates(date_arg: str | None) -> tuple[str, str]:
    if date_arg is None:
        exec_date = datetime.now(timezone.utc).date()
    else:
        exec_date = datetime.strptime(date_arg, "%Y-%m-%d").date()

    end_date = (exec_date + timedelta(days=1)).strftime("%Y-%m-%d")
    exec_date_str = exec_date.strftime("%Y-%m-%d")

    return exec_date_str, end_date


def resolve_symbols(market: dict) -> list[str]:
    market_name = market["name"]
    mode = market.get("mode", "list")

    if mode == "all":
        logger.info(f"Resolviendo universo COMPLETO para mercado {market_name}")
        return get_universe(market_name)

    symbols = market.get("symbols", [])
    logger.info(f"Usando lista explicita de simbolos para {market_name}: {symbols}")
    return symbols


def main() -> None:
    args = parse_args()
    exec_date, end_date = resolve_execution_dates(args.date)

    logger.info("=" * 70)
    logger.info("INICIO DE EJECUCION DEL SISTEMA")
    logger.info(f"FECHA DE EJECUCION (CIERRE EVALUADO): {exec_date}")
    logger.info("=" * 70)

    config = load_config()

    blacklist = set(config.get("blacklist", {}).get("symbols", []))
    if blacklist:
        logger.info(f"Blacklist activa ({len(blacklist)}): {sorted(blacklist)}")

    signal_name = "golden_cross_wma"
    signal_cfg = config["signals"][signal_name]

    short_period = signal_cfg["short_period"]
    long_period = signal_cfg["long_period"]

    start_date = "2000-01-01"

    golden_crosses: list[dict] = []
    invalid_symbols: list[tuple] = []
    processing_errors: list[tuple] = []

    for market in config["markets"]:
        market_name = market["name"]
        symbols = resolve_symbols(market)

        for symbol in symbols:
            if symbol in blacklist:
                logger.info(f"⏭️  Simbolo ignorado por blacklist: {symbol}")
                continue

            logger.info("-" * 70)
            logger.info(f"MERCADO: {market_name} | EMPRESA: {symbol}")
            logger.info("-" * 70)

            try:
                close = fetch_daily_close(
                    symbol,
                    start=start_date,
                    end=end_date,
                )

                if close.empty or len(close) < long_period + 1:
                    logger.warning(f"Datos insuficientes para {symbol}")
                    invalid_symbols.append((symbol, market_name, "Datos insuficientes"))
                    continue

                wma_short = wma(close, short_period)
                wma_long = wma(close, long_period)

                is_cross = last_cross_up(wma_short, wma_long)
                event_date = close.index[-1].strftime("%Y-%m-%d")

                if event_date != exec_date:
                    logger.info(
                        f"Ultimo cierre disponible ({event_date}) no coincide con fecha objetivo ({exec_date})"
                    )
                    continue

                if not is_cross:
                    logger.info(f"No hay Golden Cross en el cierre {event_date} para {symbol}")
                    continue

                if already_registered(symbol, signal_name, event_date):
                    logger.info(f"Golden Cross ya registrado para {symbol} en {event_date}")
                    continue

                diff = float(wma_short.iloc[-1] - wma_long.iloc[-1])

                event = {
                    "symbol": symbol,
                    "market": market_name,
                    "signal": signal_name,
                    "date": event_date,
                    "wma_short": float(wma_short.iloc[-1]),
                    "wma_long": float(wma_long.iloc[-1]),
                    "difference": diff,
                    "period_short": short_period,
                    "period_long": long_period,
                }

                logger.info("----- [!] -----")
                logger.info(
                    f"GOLDEN CROSS DETECTADO -> {symbol} {event_date} (diff={diff:.4f})"
                )
                logger.info("----- [!] -----")

                save_event(event)

                chart_path = plot_golden_cross(
                    symbol=symbol,
                    market=market_name,
                    signal_name=signal_name,
                    event_date=event_date,
                    short_period=short_period,
                    long_period=long_period,
                    window_sessions=config["chart"]["window_sessions"],
                )

                golden_crosses.append({
                    "symbol": symbol,
                    "market": market_name,
                    "date": event_date,
                    "difference": diff,
                    "wma_short": float(wma_short.iloc[-1]),
                    "wma_long": float(wma_long.iloc[-1]),
                    "chart_path": chart_path,
                })

            except Exception as e:
                logger.error(f"Error procesando {symbol}: {str(e)}", exc_info=True)
                processing_errors.append((symbol, market_name, str(e)))

    logger.info("=" * 70)
    logger.info("FIN DE EJECUCION DEL SISTEMA")
    logger.info("=" * 70)

    if golden_crosses:
        send_cross_alert_email(
            exec_date=exec_date,
            golden_crosses=golden_crosses,
            invalid_symbols=invalid_symbols,
            processing_errors=processing_errors,
        )
    else:
        logger.info("No se detectaron Golden Cross en esta ejecucion")

    if processing_errors or invalid_symbols:
        send_error_report_email(
            exec_date=exec_date,
            processing_errors=processing_errors,
            invalid_symbols=invalid_symbols,
        )


if __name__ == "__main__":
    main()
