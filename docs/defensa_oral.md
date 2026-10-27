# Defensa oral — Assignment 1 (multiplicación de matrices naive en Python, Java y C)

Guion para explicar el trabajo en 5–7 minutos y responder preguntas. Todos los números salen de
`results/summary/` (generados por `make analysis` a partir de `results/raw/`).

## 1. Pregunta de investigación (30 s)
"En mi portátil (i7-9750H), ¿cómo crecen el tiempo y la memoria del **mismo** algoritmo de triple bucle
(ijk, float64) con el tamaño n en C, Java y Python, y cuánto se diferencian las tres implementaciones a igual n?"
- Factor: n (matrices n×n) × lenguaje. Resultados medidos: tiempo del kernel, tiempo por multiplicación-suma
  (T/n³), exponente de crecimiento b, pico de RSS, n máximo factible.
- Hipótesis (predicciones, escritas antes de medir): H1 crecimiento ≈ n³; H2 C < Java < Python;
  H3 Python usa varias veces más memoria por elemento.

## 2. Por qué la comparación es justa (1 min)
1. **Mismo algoritmo y mismo orden**: ijk con acumulador escalar en los tres → mismas operaciones IEEE-754 en el
   mismo orden → **resultados bit a bit idénticos** (lo compruebo en los tests y con el checksum en cada ejecución).
2. **Mismos datos**: ficheros binarios compartidos generados una vez (NumPy `default_rng(42)`, uniforme [-1,1),
   little-endian, row-major) con SHA-256.
3. **Misma frontera de tiempo** (`kernel`): solo el triple bucle; carga, reserva de C y checksum quedan fuera.
   Reloj monotónico en los tres (`clock_gettime(CLOCK_MONOTONIC)`, `System.nanoTime()`, `perf_counter_ns()`).
4. **Mismo entorno**: misma máquina, un hilo, variables de hilos de BLAS a 1, ejecuciones serializadas con un
   lock global (había otros 3 benchmarks de otras prácticas en el mismo portátil).
5. **Diferencias inevitables y documentadas**: layout idiomático de cada lenguaje (C bloque contiguo `double*`;
   Java `double[][]` = array de filas separadas; Python lista de listas de objetos `float`), JIT de Java,
   intérprete de Python.
6. **Protocolo**: P procesos separados × (W calentamientos + 1 medida). Mediana + IQR. Warm-ups registrados pero
   excluidos. Lotes (batch) para kernels cortos (≥ 0,2 s por muestra). Fallos (timeout) registrados como
   resultado, nunca con un tiempo inventado.

## 3. Resultados más informativos (2 min)
%%RESULTADOS%%

## 4. Limitaciones (45 s)
- Una sola máquina (portátil): governor `powersave` + turbo → la frecuencia depende de la temperatura y de
  cuántos núcleos están activos; había otras cargas (navegador, otros agentes) → load average registrado en
  cada fila; la variabilidad se ve en el IQR.
- Sin contadores hardware (`perf` bloqueado: `perf_event_paranoid = 4`) → las explicaciones de caché/TLB son
  plausibles y coherentes con T/n³, pero **no están medidas directamente** (las llamo conjeturas).
- Menos repeticiones en los casos caros (Python n = 1536: k = 3; n = 2048: un intento) por el presupuesto de 90 min.
- Las métricas internas de memoria (heap de la JVM, `sys.getsizeof`, tamaño de arrays en C) miden cosas
  distintas: solo comparo entre lenguajes el pico de RSS.
- Resultados válidos solo para estas versiones/flags (gcc -O2, OpenJDK 21, CPython 3.12): no digo que "C es más
  rápido que Java" en general.

## 5. Cómo reproducir un experimento en directo
```bash
make setup test                 # compila y pasa los tests (debe decir ALL TESTS PASSED)
make inputs                     # regenera las entradas (mismos SHA-256)
build/c/matmul_naive_c --a data/inputs/A_n512_s42.bin --b data/inputs/B_n512_s42.bin --n 512 --warmup 2 --reps 3
java -Xms1g -Xmx4g -XX:+UseG1GC -cp build/java MatMulNaive --a data/inputs/A_n512_s42.bin --b data/inputs/B_n512_s42.bin --n 512 --warmup 5 --reps 3
.venv/bin/python src/python/matmul_naive.py --a data/inputs/A_n256_s42.bin --b data/inputs/B_n256_s42.bin --n 256 --warmup 1 --reps 3
# con registro en CSV (lock + RSS):
.venv/bin/python scripts/run_experiments.py --experiment size_sweep --languages c --sizes 512
make analysis report            # regenera tablas, figuras y PDF desde results/raw
```
Fijarse en que el `checksum` impreso es el mismo en los tres lenguajes.

## 6. Recorrido por el código
- `src/c/matmul_naive.c`: el kernel (10 líneas). `A[i*n+k]` recorre una fila (stride 1), `B[k*n+j]` una
  columna (stride n·8 bytes). Compilado aparte para que no se pueda eliminar.
- `src/c/bench_naive.c`: lee ficheros, `calloc` de C, bucle de repeticiones, cronómetro, calibración del lote,
  checksum, una línea JSON por repetición.
- `src/java/MatMulNaive.java`: `multiply()` con `double[] ai = a[i]` (izado de fila); lectura por filas con
  `ByteBuffer` little-endian; memoria del heap con `MemoryPoolMXBean.getPeakUsage()`.
- `src/python/matmul_naive.py`: mismo bucle; `array('d').fromfile` + `tolist()` por filas; métrica
  `pyobj_deep_size_bytes` con `sys.getsizeof` (lista exterior + filas + cada float).
- `tests/test_correctness.py`: identidad, cero, 1×1/2×2/3×3 exactos, aleatorios contra NumPy con tolerancia
  2·n·u·(|A||B|), identidad bit a bit entre lenguajes.
- `scripts/run_experiments.py` → `run_measured.py`: lock, procesos, RSS con GNU time, timeouts, CSV.
- `analysis/make_all.py`: medianas/IQR, ajuste log-log, ratios con bootstrap, figuras y `numbers.tex`.

## 7. Preguntas probables (respuestas cortas)
- **¿Por qué la mediana y el IQR y no media y desviación?** Robustos frente a valores atípicos (interferencias del
  SO, GC, JIT); recomendado por Hoefler & Belli.
- **¿Por qué el orden ijk?** Es la definición directa del enunciado y el mismo en los tres; otros órdenes (ikj)
  serían optimizaciones (Assignment 2).
- **¿Por qué -O2 y no -O3/-march=native?** -O2 es el nivel estándar; el estudio de flags es un experimento
  separado (tabla aparte). Con `-std=c11` comprobé en el ensamblador que no hay FMA ni con `-march=native`
  (con `-std=gnu11` sí aparece `vfmadd`), por eso los resultados siguen siendo bit-idénticos.
- **¿Por qué los resultados son idénticos bit a bit?** Mismas operaciones IEEE-754 (mul y add de doble precisión,
  redondeo al más cercano) en el mismo orden; Java es estricto desde JDK 17 (JEP 306); gcc no contrae a FMA.
- **¿Por qué la tolerancia 2·n·u·(|A||B|)?** Cota clásica del producto escalar (Higham): cada resultado tiene
  error ≤ γ_n(|A||B|), γ_n ≈ n·u; NumPy suma en otro orden, así que la diferencia está acotada por ≈ 2·n·u·(|A||B|).
- **¿Qué incluye el RSS?** Toda la memoria residente del proceso: intérprete/JVM + datos. Por eso resto la línea
  base medida con n = 1.
- **¿Por qué Python ocupa tanto?** Cada elemento es un objeto `float` de 24 B más un puntero de 8 B en la lista
  (≈ 32 B por elemento frente a 8 B en C/Java).
- **¿Por qué Java tarda más que C a n grande?** `double[][]`: para cada k hay que cargar la referencia a la fila
  `b[k]` y luego el elemento; las filas son objetos separados → más accesos a memoria y peor localidad. Es una
  explicación plausible; sin contadores hardware no la he medido directamente.
- **¿Qué es el warm-up de Java?** Las primeras iteraciones se interpretan / compilan (JIT por niveles); se excluyen
  y la figura del warm-up lo muestra.
- **¿Qué es la "frontera de tiempo kernel"?** Solo el triple bucle; no se mezcla con tiempos de proceso completo.
- **¿Cuál es el n máximo?** Ver tabla de límites: distinguir "mayor n completado" de "mayor n intentado".
