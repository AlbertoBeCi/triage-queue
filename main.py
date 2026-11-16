"""Punto de entrada principal del gestor de colas de triaje hospitalario.

Uso:
  python main.py          -> Inicia el menú interactivo en terminal.
  python main.py --demo   -> Ejecuta la simulación automática y termina.
"""

from __future__ import annotations

import argparse

from cli import run_interactive_cli, run_simulation
from triage_queue import TriageQueue


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Gestor de colas de prioridad para triaje de urgencias."
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Ejecuta una simulación automática de demostración y finaliza.",
    )
    args = parser.parse_args()

    if args.demo:
        queue = TriageQueue()
        run_simulation(queue)
    else:
        run_interactive_cli()


if __name__ == "__main__":
    main()
