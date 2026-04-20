"""
logger.py
=========
Configuración centralizada del sistema de logging.
Escribe simultáneamente en consola (WARNING+) y en archivo .log (INFO+),
garantizando trazabilidad completa de todas las operaciones del sistema.
"""

import logging
import os
from datetime import datetime


# Ruta del archivo de log
LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
LOG_FILE = os.path.join(LOG_DIR, f"task_manager_{datetime.now().strftime('%Y%m')}.log")

# Nombre logger principal de la aplicación
LOGGER_NAME = "task_manager"


def setup_logger() -> logging.Logger:
    """
    Inicializa y configura el logger de la aplicación.

    - FileHandler  : Registra INFO y superior en archivo mensual.
    - StreamHandler: Muestra WARNING y superior en consola.

    Returns:
        Logger configurado y listo para usar.
    """
    # Crear directorio de logs si no existe
    os.makedirs(LOG_DIR, exist_ok=True)

    logger = logging.getLogger(LOGGER_NAME)

    # Evitar duplicación de handlers si se llama varias veces
    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG)

    # ── Formato 
    file_formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(module)s:%(lineno)d | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    console_formatter = logging.Formatter(
        fmt="%(levelname)s: %(message)s"
    )

    # ── Handler de archivo 
    file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(file_formatter)

    # ── Handler de consola
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.WARNING)
    console_handler.setFormatter(console_formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


def get_logger() -> logging.Logger:
    """
    Devuelve el logger principal de la aplicación.
    Si no está inicializado, lo configura automáticamente.

    Returns:
        Logger de la aplicación.
    """
    logger = logging.getLogger(LOGGER_NAME)
    if not logger.handlers:
        return setup_logger()
    return logger
