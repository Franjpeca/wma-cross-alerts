from pathlib import Path
import sys
import argparse

PROJECT_ROOT = Path(__file__).resolve().parents[3]
SRC_PATH = PROJECT_ROOT / "src"

if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from wma_cross_alerts.core.settings import load_config
from wma_cross_alerts.data_sources.yahoo import fetch_daily_close
from wma_cross_alerts.indicators.wma import wma
from wma_cross_alerts.signals.golden_cross_wma import all_cross_up
from wma_cross_alerts.utils.logger import get_logger

logger = get_logger("golden_cross_history")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Listar Golden Cross historicos (WMA) para testing"
    )
    parser.add_argument(
        "--symbol",
        type=str,
        required=True,
        help="Ticker a analizar (debe existir en config.yml)",
    )
    parser.add_argument(
        "--start",
        type=str,
        default="2000-01-01",
        help="Fecha inicio YYYY-MM-DD",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    config = load_config()

    signal_cfg = config["signals"]["golden_cross_wma"]
    short_period = signal_cfg["short_period"]
    long_period = signal_cfg["long_period"]

    symbol = args.symbol.upper()

    logger.info(f"Buscando Golden Cross historicos para {symbol}")

    close = fetch_daily_close(symbol, start=args.start)

    if close.empty or len(close) < long_period + 1:
        logger.error("Datos insuficientes")
        return

    wma_short = wma(close, short_period)
    wma_long = wma(close, long_period)

    crosses = all_cross_up(wma_short, wma_long)

    if crosses.empty:
        logger.info("No se detectaron Golden Cross historicos")
        return

    print("\nGolden Cross detectados:\n")

    for date, diff in crosses.items():
        print(f"- {date} | diff={diff:.4f}")

    print(f"\nTotal: {len(crosses)} cruces")


if __name__ == "__main__":
    main()
