from pathlib import Path
import sys
import argparse

# ---------------------------------------------------------
# Ajuste de path para permitir ejecutar el script directamente
# ---------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_PATH = PROJECT_ROOT / "src"

if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

# ---------------------------------------------------------
# Imports del proyecto
# ---------------------------------------------------------
from wma_cross_alerts.utils.logger import get_logger
from wma_cross_alerts.data_sources.yahoo import fetch_daily_close
from wma_cross_alerts.indicators.wma import wma
from wma_cross_alerts.signals.golden_cross_wma import detect_cross_up


logger = get_logger("list_golden_crosses")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Listado historico de Golden Cross WMA 30/200"
    )
    parser.add_argument("--symbol", type=str, required=True, help="Ticker (ej: AAPL)")
    parser.add_argument(
        "--start",
        type=str,
        default="2000-01-01",
        help="Fecha inicio YYYY-MM-DD",
    )
    parser.add_argument(
        "--end",
        type=str,
        default=None,
        help="Fecha fin YYYY-MM-DD",
    )
    return parser.parse_args()


def run(
    symbol: str,
    start: str,
    end: str | None,
) -> None:
    logger.info(f"Descargando historico completo para {symbol}")

    close = fetch_daily_close(symbol, start=start, end=end)

    if close.empty:
        raise RuntimeError("No se han obtenido datos")

    logger.info("Calculando WMA 30 / WMA 200")
    wma30 = wma(close, 30)
    wma200 = wma(close, 200)

    logger.info("Detectando Golden Cross historicos")
    crosses = detect_cross_up(wma30, wma200)

    df = wma30.to_frame(name="WMA30")
    df["WMA200"] = wma200
    df["Close"] = close
    df["CROSS"] = crosses

    cross_events = df[df["CROSS"]]

    logger.info(f"Golden Cross detectados para {symbol}: {len(cross_events)}")

    if cross_events.empty:
        print("No se han detectado Golden Cross en el periodo indicado")
        return

    print("\nFecha        | Close     | WMA30     | WMA200")
    print("-" * 48)

    for date, row in cross_events.iterrows():
        print(
            f"{date.date()} | "
            f"{row['Close']:.2f} | "
            f"{row['WMA30']:.2f} | "
            f"{row['WMA200']:.2f}"
        )


def main() -> None:
    args = parse_args()

    run(
        symbol=args.symbol,
        start=args.start,
        end=args.end,
    )


if __name__ == "__main__":
    main()
