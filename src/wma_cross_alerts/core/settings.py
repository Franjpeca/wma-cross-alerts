from pathlib import Path
import yaml

from wma_cross_alerts.utils.logger import get_logger


logger = get_logger("settings")


CONFIG_PATH = Path("config") / "config.yaml"


def load_config() -> dict:
    if not CONFIG_PATH.exists():
        logger.error(f"No se encuentra el fichero de configuración: {CONFIG_PATH}")
        raise FileNotFoundError(CONFIG_PATH)

    logger.info("Cargando configuración")

    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    _validate_config(config)

    logger.info("Configuración cargada correctamente")
    return config


def _validate_config(config: dict) -> None:
    required_keys = ["markets", "signals", "chart", "notifications"]

    for key in required_keys:
        if key not in config:
            raise ValueError(f"Falta la clave obligatoria en config.yaml: {key}")

    if "golden_cross_wma" not in config["signals"]:
        raise ValueError("No está definida la señal golden_cross_wma")

    logger.info("Configuración validada")
