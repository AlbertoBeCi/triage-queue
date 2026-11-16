"""Interfaz de línea de comandos (CLI) y simulación para el sistema de triaje."""

from __future__ import annotations

import threading
import time

from models import Patient, TriageLevel
from triage_queue import TriageQueue


def format_table(patients: list[Patient]) -> str:
    """Formatea una lista de pacientes en una tabla limpia para terminal."""
    if not patients:
        return "  (No hay pacientes en espera en este momento)"

    lines = [
        f"  {'Pos':<4} | {'ID':<5} | {'Paciente':<24} | {'Nivel de Triaje':<16} | {'Hora Llegada':<12}",
        "  " + "-" * 72,
    ]
    for idx, p in enumerate(patients, start=1):
        level_str = f"{int(p.triage_level)} - {p.triage_level.label_es}"
        lines.append(
            f"  {idx:<4} | #{p.id:03d}  | {p.name:<24.24} | {level_str:<16} | {p.formatted_arrival():<12}"
        )
    return "\n".join(lines)


def print_stats(queue: TriageQueue) -> None:
    """Imprime el resumen estadístico de pacientes en espera por nivel."""
    counts = queue.stats()
    total = sum(counts.values())
    print("\n--- ESTADÍSTICAS DE SALA DE ESPERA ---")
    print(f"  Nivel 1 (Crítico)  : {counts[1]} paciente(s)")
    print(f"  Nivel 2 (Urgente)  : {counts[2]} paciente(s)")
    print(f"  Nivel 3 (Estándar) : {counts[3]} paciente(s)")
    print("  ------------------------------------")
    print(f"  TOTAL EN ESPERA    : {total} paciente(s)")


def run_simulation(queue: TriageQueue) -> None:
    """Ejecuta una simulación realista de urgencias demostrando prioridad, FIFO y concurrencia."""
    print("\n" + "=" * 76)
    print(" SIMULACIÓN EN VIVO: UNIDAD DE URGENCIAS HOSPITALARIAS")
    print("=" * 76)

    print("\n[Paso 1] Llegan 3 pacientes iniciales (Estándar y Urgente)...")
    p1 = queue.enqueue("Ana García", TriageLevel.STANDARD)
    print(f"  + Encolado: {p1}")
    time.sleep(0.01)
    p2 = queue.enqueue("Carlos López", TriageLevel.URGENT)
    print(f"  + Encolado: {p2}")
    time.sleep(0.01)
    p3 = queue.enqueue("María Fernández", TriageLevel.STANDARD)
    print(f"  + Encolado: {p3}")

    print("\n[Paso 2] Consultamos quién es el siguiente (Peek):")
    next_p = queue.peek()
    print(f"  -> Siguiente en ser atendido: {next_p}")

    print("\n[Paso 3] ¡Emergencia! Llega un caso CRÍTICO (Nivel 1) y otro URGENTE (Nivel 2)...")
    time.sleep(0.01)
    p4 = queue.enqueue("Jorge Martínez (Infarto)", TriageLevel.CRITICAL)
    print(f"  + Encolado: {p4}")
    time.sleep(0.01)
    p5 = queue.enqueue("Lucía Gómez (Fractura)", TriageLevel.URGENT)
    print(f"  + Encolado: {p5}")

    print("\n[Paso 4] Dos enfermeras registran pacientes simultáneamente (prueba de concurrencia)...")
    concurrent_arrivals = [
        ("Pedro Sánchez", TriageLevel.STANDARD),
        ("Elena Díaz (Shock)", TriageLevel.CRITICAL),
    ]
    threads: list[threading.Thread] = []
    results: list[Patient] = []

    def worker(name: str, level: TriageLevel) -> None:
        results.append(queue.enqueue(name, level))

    for name, lvl in concurrent_arrivals:
        t = threading.Thread(target=worker, args=(name, lvl))
        threads.append(t)
        t.start()
    for t in threads:
        t.join()

    for p in results:
        print(f"  + Encolado concurrentemente: {p}")

    print_stats(queue)

    print("\n[Paso 5] Estado completo de la cola ordenada por orden real de atención:")
    print(format_table(queue.list_queue()))

    print("\n[Paso 6] Llamando a los 3 primeros pacientes a consulta (Desencolar):")
    for i in range(1, 4):
        attended = queue.dequeue()
        print(f"  {i}. Atendiendo ahora a -> {attended}")

    print("\n[Paso 7] Cola restante tras atender a los 3 más prioritarios:")
    print(format_table(queue.list_queue()))
    print_stats(queue)
    print("=" * 76)


def handle_enqueue(queue: TriageQueue) -> None:
    """Solicita datos por consola y encola un paciente."""
    print("\n--- REGISTRAR NUEVO PACIENTE ---")
    name = input("Nombre del paciente: ").strip()
    if not name:
        print("  [!] Error: El nombre del paciente no puede estar vacío.")
        return

    level_raw = input("Nivel de triaje (1 = Crítico, 2 = Urgente, 3 = Estándar): ").strip()
    try:
        level_int = int(level_raw)
        patient = queue.enqueue(name, level_int)
        print(f"  [OK] Paciente registrado correctamente:\n       {patient}")
    except ValueError as exc:
        print(f"  [!] Error de validación: {exc}")


def handle_dequeue(queue: TriageQueue) -> None:
    """Desencola y muestra el siguiente paciente."""
    patient = queue.dequeue()
    print("\n--- LLAMAR AL SIGUIENTE PACIENTE ---")
    if patient is None:
        print("  (No hay pacientes en la cola de espera)")
    else:
        print(f"  >>> LLAMANDO A CONSULTA: {patient}")


def handle_peek(queue: TriageQueue) -> None:
    """Muestra el siguiente paciente sin retirarlo."""
    patient = queue.peek()
    print("\n--- PRÓXIMO PACIENTE EN ESPERA (PEEK) ---")
    if patient is None:
        print("  (No hay pacientes en la cola de espera)")
    else:
        print(f"  -> Siguiente en turno: {patient}")


def handle_list(queue: TriageQueue) -> None:
    """Muestra todos los pacientes en orden de atención."""
    print("\n--- LISTA DE PACIENTES EN ESPERA (ORDEN DE ATENCIÓN) ---")
    print(format_table(queue.list_queue()))


def run_interactive_cli() -> None:
    """Bucle principal del menú interactivo en terminal."""
    queue = TriageQueue()

    menu = (
        "\n============================================\n"
        "   SISTEMA DE TRIAJE DE URGENCIAS (CLI)\n"
        "============================================\n"
        "  1. Encolar nuevo paciente\n"
        "  2. Desencolar (llamar al siguiente)\n"
        "  3. Peek (ver siguiente sin retirar)\n"
        "  4. Listar cola de espera completa\n"
        "  5. Stats (pacientes por nivel de triaje)\n"
        "  6. Ejecutar simulación de demostración\n"
        "  0. Salir\n"
        "--------------------------------------------"
    )

    while True:
        print(menu)
        try:
            choice = input("Seleccione una opción (0-6): ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nSaliendo del sistema de triaje. ¡Hasta pronto!")
            break

        if choice == "1":
            handle_enqueue(queue)
        elif choice == "2":
            handle_dequeue(queue)
        elif choice == "3":
            handle_peek(queue)
        elif choice == "4":
            handle_list(queue)
        elif choice == "5":
            print_stats(queue)
        elif choice == "6":
            run_simulation(queue)
        elif choice == "0":
            print("\nSaliendo del sistema de triaje. ¡Hasta pronto!")
            break
        else:
            print("  [!] Opción no válida. Por favor, elija un número entre 0 y 6.")
