"""Suite de tests unitarios y de concurrencia para el sistema de triaje."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import datetime, timedelta
import threading
import unittest

from models import Patient, TriageLevel
from triage_queue import TriageQueue


class TestTriageQueue(unittest.TestCase):
    """Pruebas exhaustivas del modelo Patient y de la cola TriageQueue."""

    def setUp(self) -> None:
        self.queue = TriageQueue()

    def test_enqueue_and_basic_attributes(self) -> None:
        """Verifica que el paciente registra nombre, hora de llegada y nivel."""
        fixed_time = datetime(2026, 11, 16, 20, 30, 0)
        patient = self.queue.enqueue("Ana García", 2, arrival_time=fixed_time)

        self.assertEqual(patient.id, 1)
        self.assertEqual(patient.name, "Ana García")
        self.assertEqual(patient.triage_level, TriageLevel.URGENT)
        self.assertEqual(patient.arrival_time, fixed_time)
        self.assertEqual(len(self.queue), 1)
        self.assertFalse(self.queue.is_empty())

    def test_patient_immutability(self) -> None:
        """Los objetos Patient deben ser inmutables (frozen dataclass)."""
        patient = self.queue.enqueue("Carlos Ruiz", 1)
        with self.assertRaises(FrozenInstanceError):
            patient.name = "Otro Nombre"  # type: ignore[misc]

    def test_priority_ordering_across_levels(self) -> None:
        """Nivel 1 siempre antes que 2, y 2 siempre antes que 3."""
        self.queue.enqueue("Estándar 1", 3)
        self.queue.enqueue("Urgente 1", 2)
        self.queue.enqueue("Crítico 1", 1)

        self.assertEqual(self.queue.dequeue().name, "Crítico 1")  # type: ignore[union-attr]
        self.assertEqual(self.queue.dequeue().name, "Urgente 1")  # type: ignore[union-attr]
        self.assertEqual(self.queue.dequeue().name, "Estándar 1")  # type: ignore[union-attr]
        self.assertIsNone(self.queue.dequeue())

    def test_fifo_ordering_within_same_level(self) -> None:
        """Dentro del mismo nivel de triaje se respeta estrictamente el orden FIFO."""
        self.queue.enqueue("Urgente Primero", 2)
        self.queue.enqueue("Urgente Segundo", 2)
        self.queue.enqueue("Urgente Tercero", 2)

        self.assertEqual(self.queue.dequeue().name, "Urgente Primero")  # type: ignore[union-attr]
        self.assertEqual(self.queue.dequeue().name, "Urgente Segundo")  # type: ignore[union-attr]
        self.assertEqual(self.queue.dequeue().name, "Urgente Tercero")  # type: ignore[union-attr]

    def test_critical_arrival_mid_processing(self) -> None:
        """Si llega un paciente crítico mientras se procesa la cola, salta al frente sin desordenar el resto."""
        self.queue.enqueue("Estándar A", 3)
        self.queue.enqueue("Urgente A", 2)
        self.queue.enqueue("Urgente B", 2)

        # Atendemos al primero (debe ser Urgente A)
        first = self.queue.dequeue()
        self.assertIsNotNone(first)
        self.assertEqual(first.name, "Urgente A")  # type: ignore[union-attr]

        # En mitad del proceso llega un caso Crítico (nivel 1)
        self.queue.enqueue("Crítico Emergencia", 1)

        # El siguiente debe ser inmediatamente el Crítico, seguido de Urgente B y Estándar A
        order = [p.name for p in self.queue.list_queue()]
        self.assertEqual(order, ["Crítico Emergencia", "Urgente B", "Estándar A"])

        self.assertEqual(self.queue.dequeue().name, "Crítico Emergencia")  # type: ignore[union-attr]
        self.assertEqual(self.queue.dequeue().name, "Urgente B")  # type: ignore[union-attr]
        self.assertEqual(self.queue.dequeue().name, "Estándar A")  # type: ignore[union-attr]

    def test_peek_does_not_remove_patient(self) -> None:
        """Peek devuelve el siguiente paciente sin retirarlo de la cola."""
        self.assertIsNone(self.queue.peek())

        self.queue.enqueue("Estándar", 3)
        self.queue.enqueue("Crítico", 1)

        first_peek = self.queue.peek()
        second_peek = self.queue.peek()

        self.assertIsNotNone(first_peek)
        self.assertEqual(first_peek, second_peek)
        self.assertEqual(first_peek.name, "Crítico")  # type: ignore[union-attr]
        self.assertEqual(len(self.queue), 2)

    def test_list_queue_returns_exact_attention_order(self) -> None:
        """list_queue devuelve todos los pacientes en orden exacto de atención sin vaciar la cola."""
        base = datetime(2026, 11, 16, 10, 0, 0)
        self.queue.enqueue("P_Est_1", 3, arrival_time=base)
        self.queue.enqueue("P_Urg_1", 2, arrival_time=base + timedelta(minutes=1))
        self.queue.enqueue("P_Cri_1", 1, arrival_time=base + timedelta(minutes=2))
        self.queue.enqueue("P_Est_2", 3, arrival_time=base + timedelta(minutes=3))
        self.queue.enqueue("P_Cri_2", 1, arrival_time=base + timedelta(minutes=4))
        self.queue.enqueue("P_Urg_2", 2, arrival_time=base + timedelta(minutes=5))

        listed_names = [p.name for p in self.queue.list_queue()]
        expected = [
            "P_Cri_1",
            "P_Cri_2",
            "P_Urg_1",
            "P_Urg_2",
            "P_Est_1",
            "P_Est_2",
        ]
        self.assertEqual(listed_names, expected)
        # Verificar que la cola sigue intacta tras listar
        self.assertEqual(len(self.queue), 6)

    def test_stats_counts_by_triage_level(self) -> None:
        """Stats reporta correctamente los pacientes por cada nivel."""
        self.assertEqual(self.queue.stats(), {1: 0, 2: 0, 3: 0})

        self.queue.enqueue("C1", 1)
        self.queue.enqueue("U1", 2)
        self.queue.enqueue("U2", 2)
        self.queue.enqueue("S1", 3)
        self.queue.enqueue("S2", 3)
        self.queue.enqueue("S3", 3)

        self.assertEqual(self.queue.stats(), {1: 1, 2: 2, 3: 3})

        self.queue.dequeue()  # Sale C1
        self.assertEqual(self.queue.stats(), {1: 0, 2: 2, 3: 3})

    def test_validation_errors(self) -> None:
        """Valida nombres vacíos y niveles de triaje fuera de rango o booleanos."""
        with self.assertRaises(ValueError):
            self.queue.enqueue("", 1)

        with self.assertRaises(ValueError):
            self.queue.enqueue("   ", 2)

        with self.assertRaises(ValueError):
            self.queue.enqueue("Juan", 0)

        with self.assertRaises(ValueError):
            self.queue.enqueue("Juan", 4)

        with self.assertRaises(ValueError):
            self.queue.enqueue("Juan", True)  # En Python bool es subclase de int

    def test_thread_safety_concurrent_enqueues_and_dequeues(self) -> None:
        """Simula múltiples enfermeras registrando pacientes al mismo tiempo sin perder entradas."""
        num_threads = 10
        patients_per_thread = 50
        total_expected = num_threads * patients_per_thread

        def producer(thread_idx: int) -> None:
            for i in range(patients_per_thread):
                level = (i % 3) + 1
                self.queue.enqueue(f"T{thread_idx}_P{i}", level)

        threads = [
            threading.Thread(target=producer, args=(t_idx,))
            for t_idx in range(num_threads)
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Ninguna entrada se ha borrado ni sobrescrito
        self.assertEqual(len(self.queue), total_expected)

        # Todos los IDs son únicos de 1 a total_expected
        all_patients = self.queue.list_queue()
        ids = {p.id for p in all_patients}
        self.assertEqual(len(ids), total_expected)

        # Verificar que al desencolar todos salen ordenados por nivel (1, luego 2, luego 3)
        extracted_levels: list[int] = []
        while not self.queue.is_empty():
            p = self.queue.dequeue()
            self.assertIsNotNone(p)
            extracted_levels.append(int(p.triage_level))  # type: ignore[union-attr]

        self.assertEqual(len(extracted_levels), total_expected)
        self.assertEqual(extracted_levels, sorted(extracted_levels))


if __name__ == "__main__":
    unittest.main()
