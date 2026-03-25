import argparse
import subprocess
import sys
import logging
import os
from datetime import datetime, timedelta
from pathlib import Path
from dotenv import load_dotenv

# Configurar logging basico para este script auxiliar
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("run_wma_range")

def parse_args():
    parser = argparse.ArgumentParser(description="Ejecutar WMA Cross Alerts para un rango de fechas.")
    parser.add_argument("--start", required=True, help="Fecha de inicio (YYYY-MM-DD)")
    parser.add_argument("--end", required=True, help="Fecha de fin (YYYY-MM-DD)")
    return parser.parse_args()

def date_range(start_date, end_date):
    """Generador de fechas desde start_date hasta end_date (inclusive)."""
    current_date = start_date
    while current_date <= end_date:
        yield current_date
        current_date += timedelta(days=1)

def main():
    # Cargar variables de entorno (necesario si no se ejecuta desde el script .sh)
    load_dotenv()
    
    args = parse_args()
    
    try:
        start_date = datetime.strptime(args.start, "%Y-%m-%d").date()
        end_date = datetime.strptime(args.end, "%Y-%m-%d").date()
    except ValueError:
        logger.error("Formato de fecha invalido. Usar YYYY-MM-DD")
        sys.exit(1)

    if start_date > end_date:
        logger.error("La fecha de inicio debe ser anterior o igual a la fecha de fin.")
        sys.exit(1)

    # Preparar el entorno para el subproceso con el PYTHONPATH correcto
    # Esto es crucial para que encuentre el paquete wma_cross_alerts en src/
    env = os.environ.copy()
    project_root = Path(__file__).resolve().parents[1]
    src_path = project_root / "src"
    
    if "PYTHONPATH" in env:
        env["PYTHONPATH"] = str(src_path) + os.pathsep + env["PYTHONPATH"]
    else:
        env["PYTHONPATH"] = str(src_path)

    logger.info(f"Iniciando ejecucion por lotes desde {start_date} hasta {end_date}")
    logger.debug(f"PYTHONPATH configurado: {env['PYTHONPATH']}")
    
    success_count = 0
    fail_count = 0

    for single_date in date_range(start_date, end_date):
        date_str = single_date.strftime("%Y-%m-%d")
        logger.info(f"=== Procesando fecha: {date_str} ===")
        
        # Construir el comando para invocar al modulo principal
        cmd = [sys.executable, "-m", "wma_cross_alerts.main", "--date", date_str]
        
        try:
            # Ejecutar el subproceso con el entorno modificado
            subprocess.run(cmd, check=True, env=env)
            logger.info(f"✅ Ejecucion exitosa para {date_str}")
            success_count += 1
        except subprocess.CalledProcessError:
            logger.error(f"❌ Fallo la ejecucion para {date_str}")
            fail_count += 1
        except Exception as e:
            logger.error(f"❌ Error inesperado para {date_str}: {e}")
            fail_count += 1

    logger.info("=" * 50)
    logger.info(f"Resumen de ejecucion por lotes:")
    logger.info(f"Total dias: {success_count + fail_count}")
    logger.info(f"Exitosos:   {success_count}")
    logger.info(f"Fallidos:   {fail_count}")
    logger.info("=" * 50)

if __name__ == "__main__":
    main()
