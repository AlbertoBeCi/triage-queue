"""Gestor de cola de prioridad para el sistema de triaje de urgencias.

Diseño arquitectónico:
- Estructura interna: Diccionario de 3 `collections.deque` indexado por `TriageLevel` (1, 2, 3).
- Complejidad temporal:
  * `enqueue`: O(1) — inserción al final del deque correspondiente a su nivel.
  * `dequeue`: O(1) — revisa como máximo 3 niveles y extrae del frente (`popleft`).
  * `peek`: O(1) — consulta el primer elemento del nivel más prioritario no vacío.
  * `stats`: O(1) — calcula `len()` de cada uno de los 3 deques.
  * `list_queue`: O(N) — recorre secuencialmente los deques de nivel 1, 2 y 3 en orden FIFO exacto.
- Seguridad en concurrencia (Thread-safety):
  * Un `threading.Lock` protege todas las lecturas y escrituras, evitando condiciones
    de carrera cuando dos enfermeras/terminales registran o llaman pacientes al mismo tiempo.
"""

from __future__ import annotations

from collections import deque
from datetime import datetime
from itertools import chain
import threading

from models import Patient, TriageLevel


class TriageQueue:
    """Cola de prioridad acotada y thread-safe para triaje hospitalario."""

    def __init__(self) -> None:
        self._queues: dict[TriageLevel, deque[Patient]] = {
            level: deque() for level in TriageLevel
        }
        self._lock = threading.Lock()
        self._next_id = 1

    def enqueue(
        self,
        name: str,
        triage_level: int | TriageLevel,
        arrival_time: datetime | None = None,
    ) -> Patient:
        """Añade un nuevo paciente a la cola según su nivel de triaje en O(1).

        Args:
            name: Nombre completo del paciente (no vacío).
            triage_level: Nivel de prioridad (1 = Crítico, 2 = Urgente, 3 = Estándar).
            arrival_time: Momento de llegada opcional (por defecto `datetime.now()`).

        Returns:
            La instancia inmutable `Patient` creada y encolada.

        Raises:
            ValueError: Si el nombre está vacío o el nivel de triaje no es válido.
        """
        level = (
            triage_level
            if isinstance(triage_level, TriageLevel)
            else TriageLevel.from_int(triage_level)
        )

        with self._lock:
            patient = Patient(
                id=self._next_id,
                name=name,
                triage_level=level,
                arrival_time=arrival_time if arrival_time is not None else datetime.now(),
            )
            self._next_id += 1
            self._queues[level].append(patient)
            return patient

    def dequeue(self) -> Patient | None:
        """Llama y retira al siguiente paciente a ser atendido en O(1).

        Atiende siempre primero el nivel 1 (Crítico), luego el 2 (Urgente) y
        por último el 3 (Estándar). Dentro de cada nivel respeta el orden FIFO.

        Returns:
            El siguiente `Patient` o `None` si la cola está vacía.
        """
        with self._lock:
            for level in TriageLevel:
                bucket = self._queues[level]
                if bucket:
                    return bucket.popleft()
            return None

    def peek(self) -> Patient | None:
        """Muestra quién es el siguiente paciente sin retirarlo de la cola en O(1).

        Returns:
            El siguiente `Patient` a ser atendido o `None` si la cola está vacía.
        """
        with self._lock:
            for level in TriageLevel:
                bucket = self._queues[level]
                if bucket:
                    return bucket[0]
            return None

    def list_queue(self) -> list[Patient]:
        """Devuelve todos los pacientes en espera en el orden exacto de atención en O(N).

        Al estar separados en un deque por cada nivel de prioridad, no es necesario
        ordenar (`sort`), sino simplemente concatenar los niveles 1, 2 y 3.
        """
        with self._lock:
            return list(
                chain(
                    self._queues[TriageLevel.CRITICAL],
                    self._queues[TriageLevel.URGENT],
                    self._queues[TriageLevel.STANDARD],
                )
            )

    def stats(self) -> dict[int, int]:
        """Reporta el número de pacientes en espera por nivel de triaje en O(1).

        Returns:
            Diccionario `{1: count_critico, 2: count_urgente, 3: count_estandar}`.
        """
        with self._lock:
            return {int(level): len(self._queues[level]) for level in TriageLevel}

    def __len__(self) -> int:
        """Devuelve el total de pacientes esperando en la cola en O(1)."""
        with self._lock:
            return sum(len(bucket) for bucket in self._queues.values())

    def is_empty(self) -> bool:
        """Indica si no hay ningún paciente en espera en O(1)."""
        return len(self) == 0
