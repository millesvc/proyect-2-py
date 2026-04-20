"""
task_model.py
=============
Modelo de datos para la entidad Task.
Define la estructura de una tarea y proporciona métodos utilitarios
para serialización y representación.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


# Constantes de dominio
VALID_PRIORITIES = ("alta", "media", "baja")
VALID_STATUSES = ("pendiente", "en progreso", "completada")

PRIORITY_LABELS = {
    "alta": "🔴 Alta",
    "media": "🟡 Media",
    "baja": "🟢 Baja",
}

STATUS_LABELS = {
    "pendiente": "⏳ Pendiente",
    "en progreso": "🔄 En Progreso",
    "completada": "✅ Completada",
}


@dataclass
class Task:
    """
    Representa una tarea dentro del sistema de gestión.

    Attributes:
        title       : Título descriptivo de la tarea (obligatorio).
        description : Descripción detallada (opcional).
        priority    : Nivel de prioridad — 'alta', 'media' o 'baja'.
        status      : Estado actual — 'pendiente', 'en progreso' o 'completada'.
        created_at  : Timestamp de creación en formato ISO 8601.
        id          : Identificador único asignado por la base de datos.
    """

    title: str
    description: str = ""
    priority: str = "media"
    status: str = "pendiente"
    created_at: str = field(default_factory=lambda: datetime.now().isoformat(sep=" ", timespec="seconds"))
    id: Optional[int] = None

    # ------------------------------------------------------------------
    # Métodos de representación
    # ------------------------------------------------------------------

    def __str__(self) -> str:
        return (
            f"[{self.id}] {self.title} | "
            f"{PRIORITY_LABELS.get(self.priority, self.priority)} | "
            f"{STATUS_LABELS.get(self.status, self.status)}"
        )

    def to_dict(self) -> dict:
        """Convierte la tarea en un diccionario serializable."""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "priority": self.priority,
            "status": self.status,
            "created_at": self.created_at,
        }

    # ------------------------------------------------------------------
    # Fábrica desde registro de base de datos
    # ------------------------------------------------------------------

    @classmethod
    def from_row(cls, row: tuple) -> "Task":
        """
        Crea una instancia Task a partir de una fila SQLite.

        Args:
            row: Tupla (id, title, description, priority, status, created_at).

        Returns:
            Instancia de Task.
        """
        task_id, title, description, priority, status, created_at = row
        return cls(
            id=task_id,
            title=title,
            description=description or "",
            priority=priority,
            status=status,
            created_at=created_at,
        )
