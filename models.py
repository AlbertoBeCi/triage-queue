"""Modelos de dominio para el sistema de triaje de urgencias."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import IntEnum


class TriageLevel(IntEnum):
    """Niveles de prioridad de triaje (menor número = mayor urgencia)."""

    CRITICAL = 1  # Crítico (atención inmediata)
    URGENT = 2    # Urgente (alta prioridad)
    STANDARD = 3  # Estándar (orden normal)

    @property
    def label_es(self) -> str:
        """Etiqueta legible en español para el nivel de triaje."""
        labels = {
            TriageLevel.CRITICAL: "Crítico",
            TriageLevel.URGENT: "Urgente",
            TriageLevel.STANDARD: "Estándar",
        }
        return labels[self]

    @classmethod
    def from_int(cls, value: int) -> TriageLevel:
        """Convierte un entero (1, 2 o 3) en un TriageLevel validado."""
        if isinstance(value, bool) or not isinstance(value, int):
            raise ValueError(
                f"El nivel de triaje debe ser un entero (1, 2 o 3), recibido: {value!r}"
            )
        try:
            return cls(value)
        except ValueError as exc:
            raise ValueError(
                f"Nivel de triaje inválido: {value}. Valores permitidos: 1 (Crítico), 2 (Urgente), 3 (Estándar)."
            ) from exc


@dataclass(frozen=True)
class Patient:
    """Representa un paciente registrado en la cola de triaje.

    Inmutable (`frozen=True`) para garantizar integridad cuando múltiples
    hilos o componentes consultan la cola simultáneamente.
    """

    id: int
    name: str
    triage_level: TriageLevel
    arrival_time: datetime = field(default_factory=datetime.now)

    def __post_init__(self) -> None:
        cleaned_name = self.name.strip() if isinstance(self.name, str) else ""
        if not cleaned_name:
            raise ValueError("El nombre del paciente no puede estar vacío.")
        # Aseguramos el nombre normalizado (sin espacios sobrantes en los extremos)
        object.__setattr__(self, "name", cleaned_name)

        if not isinstance(self.triage_level, TriageLevel):
            level = TriageLevel.from_int(self.triage_level)
            object.__setattr__(self, "triage_level", level)

    def formatted_arrival(self) -> str:
        """Devuelve la hora de llegada en formato HH:MM:SS.mmm."""
        return self.arrival_time.strftime("%H:%M:%S.%f")[:-3]

    def __str__(self) -> str:
        return (
            f"[#{self.id:03d}] {self.name} | "
            f"Nivel {int(self.triage_level)} ({self.triage_level.label_es}) | "
            f"Llegada: {self.formatted_arrival()}"
        )
