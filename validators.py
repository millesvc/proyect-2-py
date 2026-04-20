"""
validators.py
=============
Capa de validación de datos de entrada.
Centraliza todas las reglas de negocio relacionadas con la integridad
de los datos antes de que lleguen a la capa de servicio o persistencia.
"""

from task_model import VALID_PRIORITIES, VALID_STATUSES


class ValidationError(Exception):
    """Excepción lanzada cuando una validación de negocio falla."""
    pass


def validate_title(title: str) -> str:
    """
    Valida y normaliza el título de una tarea.

    Args:
        title: Cadena de texto proporcionada por el usuario.

    Returns:
        Título normalizado (sin espacios extremos).

    Raises:
        ValidationError: Si el título está vacío o supera el límite.
    """
    if not isinstance(title, str):
        raise ValidationError("El título debe ser una cadena de texto.")

    title = title.strip()

    if not title:
        raise ValidationError("El título no puede estar vacío.")

    if len(title) > 120:
        raise ValidationError(
            f"El título no puede superar los 120 caracteres (actual: {len(title)})."
        )

    return title


def validate_description(description: str) -> str:
    """
    Valida y normaliza la descripción de una tarea.

    Args:
        description: Cadena de texto proporcionada por el usuario.

    Returns:
        Descripción normalizada.

    Raises:
        ValidationError: Si la descripción supera el límite de caracteres.
    """
    if not isinstance(description, str):
        raise ValidationError("La descripción debe ser una cadena de texto.")

    description = description.strip()

    if len(description) > 500:
        raise ValidationError(
            f"La descripción no puede superar los 500 caracteres (actual: {len(description)})."
        )

    return description


def validate_priority(priority: str) -> str:
    """
    Valida que la prioridad sea un valor permitido.

    Args:
        priority: Valor de prioridad ingresado por el usuario.

    Returns:
        Prioridad en minúsculas y normalizada.

    Raises:
        ValidationError: Si el valor no es válido.
    """
    if not isinstance(priority, str):
        raise ValidationError("La prioridad debe ser una cadena de texto.")

    priority = priority.strip().lower()

    if priority not in VALID_PRIORITIES:
        raise ValidationError(
            f"Prioridad inválida: '{priority}'. "
            f"Valores permitidos: {', '.join(VALID_PRIORITIES)}."
        )

    return priority


def validate_status(status: str) -> str:
    """
    Valida que el estado sea un valor permitido.

    Args:
        status: Valor de estado ingresado por el usuario.

    Returns:
        Estado en minúsculas y normalizado.

    Raises:
        ValidationError: Si el valor no es válido.
    """
    if not isinstance(status, str):
        raise ValidationError("El estado debe ser una cadena de texto.")

    status = status.strip().lower()

    if status not in VALID_STATUSES:
        raise ValidationError(
            f"Estado inválido: '{status}'. "
            f"Valores permitidos: {', '.join(VALID_STATUSES)}."
        )

    return status


def validate_task_id(task_id) -> int:
    """
    Valida que el ID de tarea sea un entero positivo.

    Args:
        task_id: Valor proporcionado (puede ser str o int).

    Returns:
        ID como entero.

    Raises:
        ValidationError: Si el valor no es un entero positivo.
    """
    try:
        task_id = int(task_id)
    except (ValueError, TypeError):
        raise ValidationError("El ID de tarea debe ser un número entero.")

    if task_id <= 0:
        raise ValidationError("El ID de tarea debe ser un número positivo.")

    return task_id
