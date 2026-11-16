# Gestor de Colas de Triaje Hospitalario (Urgencias)

Sistema de gestión de colas de prioridad para una unidad de urgencias hospitalarias implementado en **Python** (100 % librería estándar), diseñado con complejidad óptima `O(1)` y seguridad ante concurrencia (*thread-safety*).

---

## Arquitectura y Decisiones de Diseño

### 1. ¿Por qué un diccionario de 3 `deque` en lugar de un `heapq` o una lista?
Dado que el dominio de niveles de triaje es **finito y acotado** (`1 = Crítico`, `2 = Urgente`, `3 = Estándar`), una cola de prioridad por cubetas (*Bounded Bucket Priority Queue*) con `{TriageLevel: collections.deque}` supera a un *Min-Heap* (`heapq`) en todas las operaciones:

| Operación | Diccionario de 3 `deque` | `heapq` (Min-Heap) | Lista ordenada / `sort()` |
| :--- | :---: | :---: | :---: |
| **`enqueue` (Encolar)** | **`O(1)`** | `O(log n)` | `O(n)` |
| **`dequeue` (Desencolar)** | **`O(1)`** (máx. 3 niveles) | `O(log n)` | `O(1)` / `O(n)` |
| **`peek` (Ver siguiente)** | **`O(1)`** | `O(1)` | `O(1)` |
| **`stats` (Conteo por nivel)** | **`O(1)`** (`len()` de cada `deque`) | `O(n)` (o contadores extra) | `O(n)` |
| **`list_queue` (Listar en orden)** | **`O(n)`** (concatenar sin ordenar) | `O(n log n)` (el array del heap no está totalmente ordenado) | `O(n)` |

Cuando llega un paciente de **nivel 1 (Crítico)** en mitad del proceso, simplemente se hace `append()` en `O(1)` al `deque` del nivel 1; no hay que reordenar ni desplazar a los pacientes de nivel 2 o 3.

### 2. Concurrencia y Thread-Safety
Para resolver el problema real de la pizarra física (donde dos enfermeras escribiendo a la vez pueden borrar o pisar una entrada), `TriageQueue` incorpora un cerrojo `threading.Lock` que garantiza atomicidad en la asignación de IDs, inserciones, extracciones y lecturas, además de modelar a `Patient` como un `@dataclass(frozen=True)` inmutable.

---

## Estructura del Proyecto

- [models.py](file:///c:/Users/Muro/Documents/Ejercicios%204Geek/triage-queue/models.py): Define `TriageLevel` (`IntEnum`) y el modelo inmutable `Patient`.
- [triage_queue.py](file:///c:/Users/Muro/Documents/Ejercicios%204Geek/triage-queue/triage_queue.py): Implementa `TriageQueue` con `enqueue`, `dequeue`, `peek`, `list_queue` y `stats`.
- [cli.py](file:///c:/Users/Muro/Documents/Ejercicios%204Geek/triage-queue/cli.py): Interfaz de usuario interactiva por terminal y simulación de urgencias.
- [main.py](file:///c:/Users/Muro/Documents/Ejercicios%204Geek/triage-queue/main.py): Punto de entrada (`python main.py` o `python main.py --demo`).
- [tests/test_queue.py](file:///c:/Users/Muro/Documents/Ejercicios%204Geek/triage-queue/tests/test_queue.py): Suite de pruebas unitarias y de concurrencia con `unittest`.

---

## Ejecución

### Ejecutar el menú interactivo en terminal
```bash
python main.py
```

### Ejecutar la simulación automática (Demo)
```bash
python main.py --demo
```

### Ejecutar los tests unitarios
```bash
python -m unittest discover -s tests -v
```
