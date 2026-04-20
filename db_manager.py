"""
db_manager.py
=============
Capa de acceso a datos (DAL).
Encapsula todas las operaciones SQL contra la base de datos SQLite,
exponiendo una interfaz limpia y tipada para la capa de servicio.
"""

import sqlite3
import os
from typing import List, Optional, Tuple

from logger import get_logger

logger = get_logger()

# Ruta de la base de datos (junto al directorio de ejecución)
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tasks.db")

# DDL de la tabla principal
_CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS tasks (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    title       TEXT    NOT NULL,
    description TEXT    DEFAULT '',
    priority    TEXT    NOT NULL DEFAULT 'media',
    status      TEXT    NOT NULL DEFAULT 'pendiente',
    created_at  TEXT    NOT NULL
);
"""


class DatabaseError(Exception):
    """Excepción lanzada ante cualquier fallo de la capa de datos."""
    pass


class DatabaseManager:
    """
    Gestiona el ciclo de vida de la conexión SQLite y las operaciones CRUD
    sobre la tabla `tasks`.

    Uso recomendado como context manager:

        with DatabaseManager() as db:
            rows = db.fetch_all()
    """

    def __init__(self, db_path: str = DB_PATH):
        self._db_path = db_path
        self._conn: Optional[sqlite3.Connection] = None

    # ------------------------------------------------------------------
    # Context manager
    # ------------------------------------------------------------------

    def __enter__(self) -> "DatabaseManager":
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        if exc_type:
            self._conn.rollback()
            logger.error("Rollback por excepción: %s – %s", exc_type.__name__, exc_val)
        else:
            self._conn.commit()
        self.close()
        return False  # Propaga la excepción

    # ------------------------------------------------------------------
    # Conexión
    # ------------------------------------------------------------------

    def connect(self) -> None:
        """Abre la conexión y garantiza que el esquema existe."""
        try:
            self._conn = sqlite3.connect(self._db_path)
            self._conn.row_factory = sqlite3.Row  # Acceso por nombre de columna
            self._conn.execute("PRAGMA foreign_keys = ON;")
            self._conn.execute("PRAGMA journal_mode = WAL;")
            self._initialize_schema()
            logger.debug("Conexión abierta: %s", self._db_path)
        except sqlite3.Error as exc:
            raise DatabaseError(f"No se pudo conectar a la base de datos: {exc}") from exc

    def close(self) -> None:
        """Cierra la conexión si está abierta."""
        if self._conn:
            self._conn.close()
            self._conn = None
            logger.debug("Conexión cerrada.")

    def _initialize_schema(self) -> None:
        """Crea las tablas si no existen."""
        self._conn.executescript(_CREATE_TABLE_SQL)
        self._conn.commit()

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------

    def insert_task(
        self,
        title: str,
        description: str,
        priority: str,
        status: str,
        created_at: str,
    ) -> int:
        """
        Inserta una nueva tarea y devuelve su ID generado.

        Returns:
            ID de la tarea recién creada.

        Raises:
            DatabaseError: Si la inserción falla.
        """
        sql = """
            INSERT INTO tasks (title, description, priority, status, created_at)
            VALUES (?, ?, ?, ?, ?)
        """
        try:
            cursor = self._conn.execute(sql, (title, description, priority, status, created_at))
            self._conn.commit()
            task_id = cursor.lastrowid
            logger.info("Tarea insertada con ID=%d | título='%s'", task_id, title)
            return task_id
        except sqlite3.Error as exc:
            raise DatabaseError(f"Error al insertar tarea: {exc}") from exc

    def fetch_all(
        self,
        status_filter: Optional[str] = None,
        priority_filter: Optional[str] = None,
    ) -> List[Tuple]:
        """
        Recupera todas las tareas, con filtros opcionales.

        Args:
            status_filter  : Filtra por estado exacto.
            priority_filter: Filtra por prioridad exacta.

        Returns:
            Lista de tuplas (id, title, description, priority, status, created_at).
        """
        sql = "SELECT id, title, description, priority, status, created_at FROM tasks WHERE 1=1"
        params: list = []

        if status_filter:
            sql += " AND status = ?"
            params.append(status_filter)

        if priority_filter:
            sql += " AND priority = ?"
            params.append(priority_filter)

        sql += " ORDER BY id ASC"

        try:
            cursor = self._conn.execute(sql, params)
            return [tuple(row) for row in cursor.fetchall()]
        except sqlite3.Error as exc:
            raise DatabaseError(f"Error al listar tareas: {exc}") from exc

    def fetch_by_id(self, task_id: int) -> Optional[Tuple]:
        """
        Recupera una tarea por su ID.

        Returns:
            Tupla con los datos de la tarea, o None si no existe.
        """
        sql = "SELECT id, title, description, priority, status, created_at FROM tasks WHERE id = ?"
        try:
            cursor = self._conn.execute(sql, (task_id,))
            row = cursor.fetchone()
            return tuple(row) if row else None
        except sqlite3.Error as exc:
            raise DatabaseError(f"Error al buscar tarea ID={task_id}: {exc}") from exc

    def search_tasks(self, keyword: str) -> List[Tuple]:
        """
        Busca tareas cuyo título o descripción contengan la palabra clave.

        Args:
            keyword: Término de búsqueda (insensible a mayúsculas).

        Returns:
            Lista de tuplas que coinciden.
        """
        sql = """
            SELECT id, title, description, priority, status, created_at
            FROM tasks
            WHERE title LIKE ? OR description LIKE ?
            ORDER BY id ASC
        """
        pattern = f"%{keyword}%"
        try:
            cursor = self._conn.execute(sql, (pattern, pattern))
            return [tuple(row) for row in cursor.fetchall()]
        except sqlite3.Error as exc:
            raise DatabaseError(f"Error al buscar tareas: {exc}") from exc

    def update_task(self, task_id: int, **fields) -> bool:
        """
        Actualiza campos específicos de una tarea.

        Args:
            task_id: ID de la tarea a actualizar.
            **fields: Campos y valores a modificar (title, description,
                      priority, status).

        Returns:
            True si se actualizó alguna fila, False si no existía.

        Raises:
            DatabaseError: Si la actualización falla.
        """
        if not fields:
            return False

        allowed = {"title", "description", "priority", "status"}
        invalid = set(fields) - allowed
        if invalid:
            raise DatabaseError(f"Campos de actualización inválidos: {invalid}")

        set_clause = ", ".join(f"{col} = ?" for col in fields)
        values = list(fields.values()) + [task_id]
        sql = f"UPDATE tasks SET {set_clause} WHERE id = ?"

        try:
            cursor = self._conn.execute(sql, values)
            self._conn.commit()
            updated = cursor.rowcount > 0
            if updated:
                logger.info("Tarea ID=%d actualizada | campos=%s", task_id, list(fields.keys()))
            else:
                logger.warning("Tarea ID=%d no encontrada para actualizar.", task_id)
            return updated
        except sqlite3.Error as exc:
            raise DatabaseError(f"Error al actualizar tarea ID={task_id}: {exc}") from exc

    def delete_task(self, task_id: int) -> bool:
        """
        Elimina una tarea por su ID.

        Returns:
            True si se eliminó, False si no existía.
        """
        sql = "DELETE FROM tasks WHERE id = ?"
        try:
            cursor = self._conn.execute(sql, (task_id,))
            self._conn.commit()
            deleted = cursor.rowcount > 0
            if deleted:
                logger.info("Tarea ID=%d eliminada.", task_id)
            else:
                logger.warning("Tarea ID=%d no encontrada para eliminar.", task_id)
            return deleted
        except sqlite3.Error as exc:
            raise DatabaseError(f"Error al eliminar tarea ID={task_id}: {exc}") from exc
