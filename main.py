"""
main.py
=======
Punto de entrada del Sistema de Gestión de Tareas.

Responsabilidades:
- Inicializar el logger antes de cualquier otra operación.
- Verificar la versión mínima de Python requerida.
- Instanciar los componentes de la aplicación.
- Lanzar el bucle interactivo de la interfaz CLI.
- Capturar errores críticos no manejados.

Uso:
    python main.py
"""

import sys
import os

# ── Verificación de versión Python ────────────────────────────────────
if sys.version_info < (3, 8):
    print("ERROR: Se requiere Python 3.8 o superior.")
    sys.exit(1)

# ── Asegurar que el directorio del script esté en sys.path ───────────
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from logger import setup_logger, get_logger
from ui import UIController


def main() -> None:
    """Función principal de arranque de la aplicación."""

    # Inicializar el logger lo antes posible
    setup_logger()
    logger = get_logger()
    logger.info("=" * 60)
    logger.info("Iniciando Sistema de Gestión de Tareas")
    logger.info("Python %s | PID %d", sys.version.split()[0], os.getpid())
    logger.info("=" * 60)

    try:
        controller = UIController()
        controller.run()

    except KeyboardInterrupt:
        print("\n\n  Aplicación interrumpida por el usuario.")
        logger.info("Aplicación interrumpida por KeyboardInterrupt.")
        sys.exit(0)

    except Exception as exc:  # pylint: disable=broad-except
        logger.critical("Error crítico no controlado: %s", exc, exc_info=True)
        print(f"\n  ERROR CRÍTICO: {exc}")
        print("  Revisa el archivo de log para más detalles.")
        sys.exit(1)


if __name__ == "__main__":
    main()
