"""
task_service.py
===============
Capa de lógica de negocio (Service Layer).
Orquesta la interacción entre los validadores, el modelo de datos y
la capa de acceso a datos. Es el único punto de entrada para toda
operación que modifica el estado del sistema.
"""

from typing import List, Optional

from db_manager import DatabaseManager, DatabaseError
from task_model import Task
from validators import (
    ValidationError,
    validate_title,
    validate_description,
    validate_priority,
    validate_status,
    validate_task_id,
)
from logger import get_logger

logger = get_logger()


class TaskServiceError(Exception):
    """Excepción de alto nivel lanzada por la capa de servicio."""
    pass


class TaskService:
    """
    Servicio principal de gestión de tareas.

    Centraliza todas las operaciones CRUD aplicando validaciones
    antes de delegar en el DatabaseManager.
    """

    def __init__(self, db_manager: Optional[DatabaseManager] = None):
        """
        Args:
            db_manager: Instancia de DatabaseManager inyectada.
                        Si es None, se crea una con la ruta por defecto.
        """
        self._db = db_manager or DatabaseManager()

    # ------------------------------------------------------------------
    # Crear
    # ------------------------------------------------------------------

    def create_task(
        self,
        title: str,
        description: str = "",
        priority: str = "media",
        status: str = "pendiente",
    ) -> Task:
        """
        Valida los datos y crea una nueva tarea.

        Args:
            title      : Título de la tarea (obligatorio).
            description: Descripción opcional.
            priority   : 'alta', 'media' o 'baja'.
            status     : 'pendiente', 'en progreso' o 'completada'.

        Returns:
            Instancia Task con el ID asignado.

        Raises:
            TaskServiceError: Si la validación o la persistencia fallan.
        """
        try:
            title = validate_title(title)
            description = validate_description(description)
            priority = validate_priority(priority)
            status = validate_status(status)
        except ValidationError as exc:
            raise TaskServiceError(str(exc)) from exc

        task = Task(
            title=title,
            description=description,
            priority=priority,
            status=status,
        )

        try:
            with self._db as db:
                task.id = db.insert_task(
                    title=task.title,
                    description=task.description,
                    priority=task.priority,
                    status=task.status,
                    created_at=task.created_at,
                )
        except DatabaseError as exc:
            raise TaskServiceError(f"No se pudo guardar la tarea: {exc}") from exc

        logger.info("Tarea creada exitosamente | ID=%d | título='%s'", task.id, task.title)
        return task

    # ------------------------------------------------------------------
    # Listar
    # ------------------------------------------------------------------

    def list_tasks(
        self,
        status_filter: Optional[str] = None,
        priority_filter: Optional[str] = None,
    ) -> List[Task]:
        """
        Devuelve la lista de tareas, con filtros opcionales.

        Args:
            status_filter  : Filtra por estado ('pendiente', etc.).
            priority_filter: Filtra por prioridad ('alta', etc.).

        Returns:
            Lista de instancias Task.
        """
        try:
            if status_filter:
                status_filter = validate_status(status_filter)
            if priority_filter:
                priority_filter = validate_priority(priority_filter)
        except ValidationError as exc:
            raise TaskServiceError(str(exc)) from exc

        try:
            with self._db as db:
                rows = db.fetch_all(
                    status_filter=status_filter,
                    priority_filter=priority_filter,
                )
            return [Task.from_row(row) for row in rows]
        except DatabaseError as exc:
            raise TaskServiceError(f"Error al recuperar tareas: {exc}") from exc

    # ------------------------------------------------------------------
    # Buscar
    # ------------------------------------------------------------------

    def search_tasks(self, keyword: str) -> List[Task]:
        """
        Busca tareas por palabra clave en título o descripción.

        Args:
            keyword: Término de búsqueda.

        Returns:
            Lista de tareas que coinciden.
        """
        keyword = keyword.strip()
        if not keyword:
            raise TaskServiceError("El término de búsqueda no puede estar vacío.")

        try:
            with self._db as db:
                rows = db.search_tasks(keyword)
            return [Task.from_row(row) for row in rows]
        except DatabaseError as exc:
            raise TaskServiceError(f"Error en la búsqueda: {exc}") from exc

    # ------------------------------------------------------------------
    # Obtener por ID
    # ------------------------------------------------------------------

    def get_task(self, task_id) -> Task:
        """
        Recupera una tarea por su ID.

        Args:
            task_id: ID de la tarea.

        Returns:
            Instancia Task.

        Raises:
            TaskServiceError: Si el ID no existe o es inválido.
        """
        try:
            task_id = validate_task_id(task_id)
        except ValidationError as exc:
            raise TaskServiceError(str(exc)) from exc

        try:
            with self._db as db:
                row = db.fetch_by_id(task_id)
        except DatabaseError as exc:
            raise TaskServiceError(f"Error al obtener la tarea: {exc}") from exc

        if row is None:
            raise TaskServiceError(f"No existe ninguna tarea con ID={task_id}.")

        return Task.from_row(row)

    # ------------------------------------------------------------------
    # Actualizar
    # ------------------------------------------------------------------

    def update_task(self, task_id, **fields) -> Task:
        """
        Actualiza campos de una tarea existente.

        Args:
            task_id: ID de la tarea a modificar.
            **fields: Campos a actualizar (title, description, priority, status).

        Returns:
            Tarea actualizada.

        Raises:
            TaskServiceError: Si la validación o la actualización fallan.
        """
        try:
            task_id = validate_task_id(task_id)
        except ValidationError as exc:
            raise TaskServiceError(str(exc)) from exc

        validated_fields: dict = {}

        validators_map = {
            "title": validate_title,
            "description": validate_description,
            "priority": validate_priority,
            "status": validate_status,
        }

        try:
            for field_name, value in fields.items():
                if field_name in validators_map:
                    validated_fields[field_name] = validators_map[field_name](value)
                else:
                    raise TaskServiceError(f"Campo no permitido: '{field_name}'.")
        except ValidationError as exc:
            raise TaskServiceError(str(exc)) from exc

        if not validated_fields:
            raise TaskServiceError("No se proporcionaron campos para actualizar.")

        try:
            with self._db as db:
                updated = db.update_task(task_id, **validated_fields)
                if not updated:
                    raise TaskServiceError(f"No existe ninguna tarea con ID={task_id}.")
                row = db.fetch_by_id(task_id)
        except DatabaseError as exc:
            raise TaskServiceError(f"Error al actualizar la tarea: {exc}") from exc

        return Task.from_row(row)

    # ------------------------------------------------------------------
    # Eliminar
    # ------------------------------------------------------------------

    def delete_task(self, task_id) -> bool:
        """
        Elimina una tarea por su ID.

        Args:
            task_id: ID de la tarea a eliminar.

        Returns:
            True si se eliminó correctamente.

        Raises:
            TaskServiceError: Si el ID es inválido o la tarea no existe.
        """
        try:
            task_id = validate_task_id(task_id)
        except ValidationError as exc:
            raise TaskServiceError(str(exc)) from exc

        try:
            with self._db as db:
                deleted = db.delete_task(task_id)
        except DatabaseError as exc:
            raise TaskServiceError(f"Error al eliminar la tarea: {exc}") from exc

        if not deleted:
            raise TaskServiceError(f"No existe ninguna tarea con ID={task_id}.")

        return True
