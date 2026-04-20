"""
ui.py
=====
Interfaz de línea de comandos (CLI).
Gestiona toda la interacción con el usuario: menús, prompts, lectura
de entradas y presentación de resultados en formato tabular.
"""

import os
import sys
from typing import List, Optional

from task_model import Task, VALID_PRIORITIES, VALID_STATUSES, PRIORITY_LABELS, STATUS_LABELS
from task_service import TaskService, TaskServiceError
from logger import get_logger

logger = get_logger()

# ── Colores ANSI ──────────────────────────────────────────────────────
_RESET = "\033[0m"
_BOLD  = "\033[1m"
_DIM   = "\033[2m"
_RED   = "\033[91m"
_GREEN = "\033[92m"
_YELLOW= "\033[93m"
_BLUE  = "\033[94m"
_CYAN  = "\033[96m"
_WHITE = "\033[97m"
_GRAY  = "\033[90m"


def _supports_color() -> bool:
    """Detecta si el terminal soporta colores ANSI."""
    return hasattr(sys.stdout, "isatty") and sys.stdout.isatty()


def _c(text: str, *codes: str) -> str:
    """Aplica códigos ANSI al texto si el terminal lo soporta."""
    if not _supports_color():
        return text
    return "".join(codes) + text + _RESET


def clear_screen() -> None:
    """Limpia la pantalla del terminal."""
    os.system("cls" if os.name == "nt" else "clear")


# ── Presentación ──────────────────────────────────────────────────────

BANNER = r"""
  ████████╗ █████╗ ███████╗██╗  ██╗    ███╗   ███╗ ██████╗ ██████╗ 
  ╚══██╔══╝██╔══██╗██╔════╝██║ ██╔╝    ████╗ ████║██╔════╝ ██╔══██╗
     ██║   ███████║███████╗█████╔╝     ██╔████╔██║██║  ███╗██████╔╝
     ██║   ██╔══██║╚════██║██╔═██╗     ██║╚██╔╝██║██║   ██║██╔══██╗
     ██║   ██║  ██║███████║██║  ██╗    ██║ ╚═╝ ██║╚██████╔╝██║  ██║
     ╚═╝   ╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝   ╚═╝     ╚═╝ ╚═════╝ ╚═╝  ╚═╝
"""

MENU_OPTIONS = {
    "1": "Crear tarea",
    "2": "Listar tareas",
    "3": "Buscar tareas",
    "4": "Actualizar tarea",
    "5": "Eliminar tarea",
    "0": "Salir",
}


def print_banner() -> None:
    clear_screen()
    print(_c(BANNER, _CYAN, _BOLD))
    print(_c("  Sistema Empresarial de Gestión de Tareas  v1.0", _GRAY))
    print(_c("  ─" * 36, _GRAY))
    print()


def print_menu() -> None:
    print(_c("\n╔══════════════════════════════╗", _BLUE))
    print(_c("║         MENÚ PRINCIPAL        ║", _BLUE, _BOLD))
    print(_c("╚══════════════════════════════╝", _BLUE))
    for key, label in MENU_OPTIONS.items():
        icon = "🔴" if key == "0" else "▸"
        print(f"  {_c(key, _YELLOW, _BOLD)}  {icon}  {label}")
    print()


def print_success(message: str) -> None:
    print(_c(f"\n  ✔  {message}", _GREEN, _BOLD))


def print_error(message: str) -> None:
    print(_c(f"\n  ✘  {message}", _RED, _BOLD))


def print_info(message: str) -> None:
    print(_c(f"\n  ℹ  {message}", _CYAN))


def print_separator() -> None:
    print(_c("  " + "─" * 70, _GRAY))


# ── Tabla de tareas ───────────────────────────────────────────────────

def _truncate(text: str, max_len: int) -> str:
    """Trunca el texto con puntos suspensivos si supera el límite."""
    return text if len(text) <= max_len else text[: max_len - 1] + "…"


def print_tasks_table(tasks: List[Task]) -> None:
    """
    Imprime las tareas en formato de tabla ASCII alineada.

    Args:
        tasks: Lista de instancias Task a mostrar.
    """
    if not tasks:
        print_info("No se encontraron tareas.")
        return

    # Anchos de columna fijos
    col_widths = {
        "id"         : 4,
        "title"      : 28,
        "priority"   : 14,
        "status"     : 16,
        "created_at" : 19,
    }

    def header_row() -> str:
        cells = [
            "ID".center(col_widths["id"]),
            "TÍTULO".ljust(col_widths["title"]),
            "PRIORIDAD".center(col_widths["priority"]),
            "ESTADO".center(col_widths["status"]),
            "CREADO".center(col_widths["created_at"]),
        ]
        return "  │  ".join(cells)

    sep = "  " + "─" * (sum(col_widths.values()) + 15)

    print()
    print(_c(sep, _GRAY))
    print(_c("  " + header_row(), _BOLD, _WHITE))
    print(_c(sep, _GRAY))

    for task in tasks:
        priority_label = PRIORITY_LABELS.get(task.priority, task.priority)
        status_label   = STATUS_LABELS.get(task.status, task.status)

        cells = [
            str(task.id).center(col_widths["id"]),
            _truncate(task.title, col_widths["title"]).ljust(col_widths["title"]),
            priority_label.center(col_widths["priority"]),
            status_label.center(col_widths["status"]),
            task.created_at[:19].center(col_widths["created_at"]),
        ]
        print("  " + "  │  ".join(cells))

    print(_c(sep, _GRAY))
    print(_c(f"  Total: {len(tasks)} tarea(s)\n", _GRAY))


def print_task_detail(task: Task) -> None:
    """Muestra el detalle completo de una sola tarea."""
    priority_label = PRIORITY_LABELS.get(task.priority, task.priority)
    status_label   = STATUS_LABELS.get(task.status, task.status)

    print(_c("\n  ┌─────────────────────────────────────┐", _BLUE))
    print(_c(f"  │  Detalle de Tarea #{task.id:<20}│", _BLUE))
    print(_c("  └─────────────────────────────────────┘", _BLUE))
    print(f"  {'Título':<14}: {_c(task.title, _BOLD)}")
    print(f"  {'Prioridad':<14}: {priority_label}")
    print(f"  {'Estado':<14}: {status_label}")
    print(f"  {'Creado':<14}: {task.created_at}")
    if task.description:
        print(f"  {'Descripción':<14}: {task.description}")
    print()


# ── Prompts de entrada ────────────────────────────────────────────────

def prompt(text: str, default: str = "") -> str:
    """
    Solicita al usuario una entrada de texto.

    Args:
        text   : Texto del prompt.
        default: Valor por defecto mostrado entre corchetes.

    Returns:
        Cadena ingresada por el usuario (o el valor por defecto).
    """
    default_hint = f" [{default}]" if default else ""
    try:
        value = input(_c(f"  ◆ {text}{default_hint}: ", _YELLOW)).strip()
    except (KeyboardInterrupt, EOFError):
        print()
        raise

    return value if value else default


def prompt_choice(text: str, options: tuple, default: str = "") -> str:
    """
    Solicita al usuario elegir una opción de una lista.

    Args:
        text   : Texto del prompt.
        options: Tupla de opciones válidas.
        default: Opción por defecto.

    Returns:
        Opción elegida (normalizada a minúsculas).
    """
    opts_str = " / ".join(
        _c(o, _BOLD, _WHITE) if o == default else o
        for o in options
    )
    while True:
        value = prompt(f"{text} ({opts_str})", default).lower()
        if value in options:
            return value
        print_error(f"Opción inválida. Elige: {', '.join(options)}.")


def confirm(text: str) -> bool:
    """
    Solicita confirmación sí/no al usuario.

    Returns:
        True si el usuario confirma, False en caso contrario.
    """
    answer = prompt(f"{text} (s/n)", "n").lower()
    return answer in ("s", "si", "sí", "y", "yes")


# ── Flujos de cada funcionalidad ──────────────────────────────────────

class UIController:
    """
    Controlador de la interfaz de usuario.
    Vincula el servicio de tareas con los flujos de interacción CLI.
    """

    def __init__(self, service: Optional[TaskService] = None):
        self._service = service or TaskService()

    # ── 1. Crear tarea ─────────────────────────────────────────────────

    def flow_create_task(self) -> None:
        print(_c("\n  ── Nueva Tarea ──", _CYAN, _BOLD))
        try:
            title = prompt("Título")
            if not title:
                print_error("El título es obligatorio.")
                return

            description = prompt("Descripción (opcional)")
            priority    = prompt_choice("Prioridad", VALID_PRIORITIES, default="media")
            status      = prompt_choice("Estado", VALID_STATUSES, default="pendiente")

            task = self._service.create_task(
                title=title,
                description=description,
                priority=priority,
                status=status,
            )
            print_success(f"Tarea creada exitosamente con ID={task.id}.")
            logger.info("UI: Tarea creada | ID=%d", task.id)

        except TaskServiceError as exc:
            print_error(str(exc))
            logger.warning("UI: Error al crear tarea — %s", exc)

    # ── 2. Listar tareas ───────────────────────────────────────────────

    def flow_list_tasks(self) -> None:
        print(_c("\n  ── Listado de Tareas ──", _CYAN, _BOLD))
        try:
            apply_filter = confirm("¿Aplicar filtros?")
            status_filter = priority_filter = None

            if apply_filter:
                filter_by = prompt_choice(
                    "Filtrar por",
                    ("estado", "prioridad", "ambos", "ninguno"),
                    default="ninguno",
                )
                if filter_by in ("estado", "ambos"):
                    status_filter = prompt_choice("Estado", VALID_STATUSES, default="pendiente")
                if filter_by in ("prioridad", "ambos"):
                    priority_filter = prompt_choice("Prioridad", VALID_PRIORITIES, default="media")

            tasks = self._service.list_tasks(
                status_filter=status_filter,
                priority_filter=priority_filter,
            )
            print_tasks_table(tasks)

        except TaskServiceError as exc:
            print_error(str(exc))
            logger.warning("UI: Error al listar tareas — %s", exc)

    # ── 3. Buscar tareas ───────────────────────────────────────────────

    def flow_search_tasks(self) -> None:
        print(_c("\n  ── Buscar Tareas ──", _CYAN, _BOLD))
        try:
            keyword = prompt("Palabra clave")
            if not keyword:
                print_error("Ingresa un término de búsqueda.")
                return

            tasks = self._service.search_tasks(keyword)
            print_info(f"Resultados para '{keyword}':")
            print_tasks_table(tasks)

        except TaskServiceError as exc:
            print_error(str(exc))
            logger.warning("UI: Error en búsqueda — %s", exc)

    # ── 4. Actualizar tarea ────────────────────────────────────────────

    def flow_update_task(self) -> None:
        print(_c("\n  ── Actualizar Tarea ──", _CYAN, _BOLD))
        try:
            task_id = prompt("ID de la tarea a actualizar")
            if not task_id:
                print_error("Debes ingresar un ID.")
                return

            # Mostrar tarea actual
            try:
                current = self._service.get_task(task_id)
            except TaskServiceError as exc:
                print_error(str(exc))
                return

            print_task_detail(current)

            print_info("Deja en blanco los campos que no deseas cambiar.")

            fields: dict = {}

            new_title = prompt("Nuevo título", current.title)
            if new_title != current.title:
                fields["title"] = new_title

            new_desc = prompt("Nueva descripción", current.description)
            if new_desc != current.description:
                fields["description"] = new_desc

            new_priority = prompt_choice("Prioridad", VALID_PRIORITIES, default=current.priority)
            if new_priority != current.priority:
                fields["priority"] = new_priority

            new_status = prompt_choice("Estado", VALID_STATUSES, default=current.status)
            if new_status != current.status:
                fields["status"] = new_status

            if not fields:
                print_info("No se realizaron cambios.")
                return

            updated = self._service.update_task(task_id, **fields)
            print_success(f"Tarea ID={updated.id} actualizada correctamente.")
            logger.info("UI: Tarea ID=%s actualizada | campos=%s", task_id, list(fields.keys()))

        except TaskServiceError as exc:
            print_error(str(exc))
            logger.warning("UI: Error al actualizar tarea — %s", exc)

    # ── 5. Eliminar tarea ──────────────────────────────────────────────

    def flow_delete_task(self) -> None:
        print(_c("\n  ── Eliminar Tarea ──", _CYAN, _BOLD))
        try:
            task_id = prompt("ID de la tarea a eliminar")
            if not task_id:
                print_error("Debes ingresar un ID.")
                return

            # Mostrar tarea antes de eliminar
            try:
                task = self._service.get_task(task_id)
            except TaskServiceError as exc:
                print_error(str(exc))
                return

            print_task_detail(task)

            if not confirm(f"¿Confirmas eliminar la tarea '{task.title}'?"):
                print_info("Operación cancelada.")
                return

            self._service.delete_task(task_id)
            print_success(f"Tarea ID={task_id} eliminada exitosamente.")
            logger.info("UI: Tarea ID=%s eliminada.", task_id)

        except TaskServiceError as exc:
            print_error(str(exc))
            logger.warning("UI: Error al eliminar tarea — %s", exc)

    # ── Bucle principal ────────────────────────────────────────────────

    def run(self) -> None:
        """Inicia el bucle interactivo del menú principal."""
        print_banner()

        FLOW_MAP = {
            "1": self.flow_create_task,
            "2": self.flow_list_tasks,
            "3": self.flow_search_tasks,
            "4": self.flow_update_task,
            "5": self.flow_delete_task,
        }

        while True:
            print_menu()
            try:
                choice = input(_c("  ❯ Selecciona una opción: ", _BOLD, _WHITE)).strip()
            except (KeyboardInterrupt, EOFError):
                choice = "0"

            if choice == "0":
                print(_c("\n  👋  Sesión finalizada. ¡Hasta pronto!\n", _CYAN, _BOLD))
                logger.info("UI: Sesión finalizada por el usuario.")
                sys.exit(0)

            if choice in FLOW_MAP:
                try:
                    FLOW_MAP[choice]()
                except (KeyboardInterrupt, EOFError):
                    print_info("Operación cancelada.")
                input(_c("\n  Presiona ENTER para continuar…", _GRAY))
                print_banner()
            else:
                print_error("Opción no válida. Elige una del menú.")
