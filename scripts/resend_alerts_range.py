#!/usr/bin/env python3
import argparse
import subprocess
import sys
import logging
import os
from datetime import datetime, timedelta
from pathlib import Path

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("resend_range")

def parse_args():
    parser = argparse.ArgumentParser(description="Re-enviar alertas WMA para un rango de fechas.")
    parser.add_argument("--start", required=True, help="Fecha de inicio (YYYY-MM-DD)")
    parser.add_argument("--end", required=True, help="Fecha de fin (YYYY-MM-DD)")
    parser.add_argument("--market", help="Filtrar por mercado (opcional)")
    parser.add_argument("--dry-run", action="store_true", help="Modo prueba sin enviar emails")
    return parser.parse_args()

def date_range(start_date, end_date):
    current_date = start_date
    while current_date <= end_date:
        yield current_date
        current_date += timedelta(days=1)

def main():
    args = parse_args()
    
    try:
        start_date = datetime.strptime(args.start, "%Y-%m-%d").date()
        end_date = datetime.strptime(args.end, "%Y-%m-%d").date()
    except ValueError:
        logger.error("Formato de fecha invalido. Usar YYYY-MM-DD")
        sys.exit(1)

    if start_date > end_date:
        logger.error("Fecha inicio > fecha fin")
        sys.exit(1)

    # Localizar scripts/resend_alerts.py en el mismo directorio que este script
    script_path = Path(__file__).resolve().parent / "resend_alerts.py"
    if not script_path.exists():
        logger.error(f"No se encuentra el script: {script_path}")
        sys.exit(1)

    env = os.environ.copy()
    
    logger.info(f"Iniciando REENVIO por lotes: {start_date} -> {end_date}")
    if args.dry_run: logger.info("MODO DRY-RUN ACTIVADO")
    if args.market: logger.info(f"Mercado filtrado: {args.market}")

    success_count = 0
    fail_count = 0

    for single_date in date_range(start_date, end_date):
        date_str = single_date.strftime("%Y-%m-%d")
        logger.info(f"=== Procesando fecha: {date_str} ===")
        
        cmd = [sys.executable, str(script_path), "--date", date_str]
        
        if args.market:
            cmd.extend(["--market", args.market])
            
        if args.dry_run:
            cmd.append("--dry-run")
        
        try:
            result = subprocess.run(cmd, check=False, env=env)
            if result.returncode == 0:
                success_count += 1
            else:
                logger.error(f"❌ Fallo al procesar {date_str} (exit code {result.returncode})")
                fail_count += 1
        except Exception as e:
            logger.error(f"❌ Error inesperado en {date_str}: {e}")
            fail_count += 1
            
    logger.info("=" * 50)
    logger.info(f"Resumen de reenvio por lotes:")
    logger.info(f"Total dias: {success_count + fail_count}")
    logger.info(f"Exitosos:   {success_count}")
    logger.info(f"Fallidos:   {fail_count}")
    logger.info("=" * 50)

if __name__ == "__main__":
    main()
