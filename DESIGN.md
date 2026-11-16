# Notas de Diseño — Sistema de Triaje Hospitalario

## 1. Elección de la estructura de datos interna

Para modelar la cola de prioridad de triaje se ha elegido un **diccionario indexado por nivel de prioridad con tres `collections.deque` separados** (`{TriageLevel.CRITICAL: deque(), TriageLevel.URGENT: deque(), TriageLevel.STANDARD: deque()}`).

### Comparativa frente a alternativas

* **Frente a una sola `deque`:**
  Una única `deque` solo permite inserciones eficientes `O(1)` en los extremos (`append` / `appendleft`), pero no en posiciones intermedias. Si llega un paciente de nivel 1 (Crítico) mientras hay pacientes de nivel 2 y 3 esperando, habría que recorrer y desplazar elementos en `O(n)` o mantener la cola desordenada.
* **Frente a una lista ordenada (`list` + `sort` / `bisect`):**
  Insertar manteniendo el orden en una lista de Python requiere desplazar elementos en memoria (`O(n)`), y extraer por el principio (`pop(0)`) también es `O(n)`. Con tres `deque`, tanto `enqueue` como `dequeue` son **`O(1)`**.
* **Frente a un Min-Heap (`heapq`):**
  Un heap ofrece `O(log n)` en inserción y extracción, pero su array interno no está completamente ordenado, lo que obligaría a ordenar (`O(n log n)`) en cada llamada a `list_queue()` y a recorrer `O(n)` (o mantener contadores extra) para `stats()`. Como el número de prioridades está acotado a exactamente 3 niveles, las tres cubetas (`deque`) logran **`O(1)` exacto** en `enqueue`, `dequeue`, `peek` y `stats`, y **`O(n)` sin reordenamiento** en `list_queue()`.

---

## 2. Concurrencia: extracción simultánea y llegada de un paciente crítico

### Escenario
Un *worker* (médico/consulta) ejecuta `dequeue()` en el mismo instante en que otro *worker* (enfermera/triaje) ejecuta `enqueue()` con un paciente de nivel 1 (**Crítico**).

### Cómo se gestiona y orden de mutación del estado
Todas las operaciones que leen o mutan el estado de la cola están protegidas por un cerrojo exclusivo (`threading.Lock` mediante `with self._lock:`), lo que **serializa** el acceso concurrente:

1. **Si `dequeue()` adquiere el lock primero:**
   * Revisa los niveles en orden (`1 -> 2 -> 3`), extrae y **elimina** (`popleft()`) al paciente más prioritario disponible en ese instante, y libera el lock.
   * El *worker* de `enqueue()` entra inmediatamente después, crea el `Patient` con el siguiente `id` secuencial y lo añade al `deque` de nivel 1.
   * **Resultado:** El paciente ya extraído no puede volver a ser leído por nadie (evitando el doble procesamiento), y el nuevo paciente crítico queda en cabeza para la siguiente llamada a `dequeue()`.

2. **Si `enqueue()` adquiere el lock primero:**
   * Primero construye la instancia inmutable `Patient` y asigna `self._next_id += 1`, y a continuación lo inserta en `self._queues[TriageLevel.CRITICAL].append(patient)` antes de liberar el lock.
   * El *worker* de `dequeue()` entra inmediatamente después, encuentra el `deque` de nivel 1 no vacío y extrae directamente a ese paciente crítico recién llegado.
   * **Resultado:** Ningún paciente se pierde ni se procesa dos veces, y el caso crítico recibe atención inmediata.
