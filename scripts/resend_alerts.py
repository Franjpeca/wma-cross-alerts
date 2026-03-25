#!/usr/bin/env python3
"""
resend_alerts.py
----------------
Consulta los cruces Golden Cross WMA guardados para una fecha concreta
y re-envía el correo de alertas.

Uso:
  # Solo consultar (sin enviar email):
  python scripts/resend_alerts.py --date 2026-02-13 --dry-run

  # Consultar y re-enviar email:
  python scripts/resend_alerts.py --date 2026-02-13
"""

from datetime import datetime
from pathlib import Path
import sys
import argparse

# Añadir src al path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = PROJECT_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from wma_cross_alerts.utils.logger import get_logger
from wma_cross_alerts.persistence.storage import load_events
from wma_cross_alerts.notifiers.email import send_cross_alert_email

logger = get_logger("resend_alerts")

SIGNAL_NAME = "golden_cross_wma"
CHARTS_DIR = PROJECT_ROOT / "data" / "charts" / SIGNAL_NAME


def find_chart(market: str, symbol: str, date: str) -> str | None:
    """Busca el archivo de chart generado para un cruce, si existe."""
    chart_path = CHARTS_DIR / market / symbol / f"{date}_{symbol}_{SIGNAL_NAME}.png"
    return str(chart_path) if chart_path.exists() else None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Re-enviar email de alertas Golden Cross para una fecha"
    )
    parser.add_argument(
        "--date",
        type=str,
        required=True,
        help="Fecha a consultar en formato YYYY-MM-DD",
    )
    parser.add_argument(
        "--market",
        type=str,
        default=None,
        help="Filtrar por mercado (sp500, nasdaq100, nyse, dowjones). Opcional.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Solo mostrar los cruces encontrados sin enviar email",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    # Validar formato de fecha
    try:
        datetime.strptime(args.date, "%Y-%m-%d")
    except ValueError:
        print(f"Error: fecha '{args.date}' no tiene el formato YYYY-MM-DD")
        sys.exit(1)

    logger.info("=" * 60)
    logger.info(f"CONSULTA DE CRUCES PARA FECHA: {args.date}")
    if args.market:
        logger.info(f"Filtrando por mercado: {args.market}")
    if args.dry_run:
        logger.info("MODO DRY-RUN: no se enviará email")
    logger.info("=" * 60)

    # Cargar todos los eventos del signal (filtrando por market si se indicó)
    events = load_events(
        signal=SIGNAL_NAME,
        market=args.market,
    )

    # Filtrar por la fecha pedida
    day_events = [e for e in events if e.get("date") == args.date]

    if not day_events:
        logger.info(f"No se encontraron cruces registrados para {args.date}")
        print(f"\n⚠️  No hay cruces guardados para {args.date}")
        return

    logger.info(f"Cruces encontrados: {len(day_events)}")

    # Construir la lista de cruces con la ruta del chart si existe
    crosses = []
    for e in day_events:
        chart_path = find_chart(e["market"], e["symbol"], e["date"])
        crosses.append({
            "symbol": e["symbol"],
            "market": e["market"],
            "date": e["date"],
            "difference": e.get("difference", 0.0),
            "wma_short": e.get("wma_short", 0.0),
            "wma_long": e.get("wma_long", 0.0),
            "chart_path": chart_path,
        })

    # Mostrar resumen en consola siempre
    print(f"\n{'='*60}")
    print(f"  Golden Crosses registrados para {args.date}")
    print(f"{'='*60}")
    for i, c in enumerate(crosses, 1):
        chart_status = "✅ chart" if c["chart_path"] else "❌ sin chart"
        print(f"  {i:>3}. {c['symbol']:<10} ({c['market']:<10}) diff={c['difference']:.4f}  {chart_status}")
    print(f"{'='*60}")
    print(f"  Total: {len(crosses)} cruces")
    print(f"{'='*60}\n")

    if args.dry_run:
        logger.info("Dry-run completado. Sin envío de email.")
        return

    # Re-enviar email
    logger.info("Enviando email de re-notificación...")
    send_cross_alert_email(
        exec_date=args.date,
        golden_crosses=crosses,
        invalid_symbols=[],
        processing_errors=[],
        mode="resend",
    )
    logger.info("Email de re-notificación enviado correctamente.")


if __name__ == "__main__":
    main()
