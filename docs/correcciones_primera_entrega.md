# Correcciones pendientes de la primera entrega

Lista de inconsistencias encontradas en la Fase 0 (revisión del 21 de noviembre de 2026) en el informe, el manual, el README y los notebooks de la primera entrega. Se corrigen en la **Fase 8** (informe) y la **Fase 9** (manual, README y notebooks). Ningún número de esta lista se copia a mano a los documentos finales: cada uno se regenera desde el archivo de `resultados/` que se indica.

## 0. Cambio transversal: verificadores de referencia

Los números de la primera entrega se calificaron en Colab con una versión de `allenai/open-instruct` anterior al 6 de noviembre de 2026. El proyecto queda fijado en el commit `a4cd966` (CLAUDE.md, regla 13). Al recalificar el caché con esa versión cambian 31 de los 6.087 veredictos (28 de `keywords:exclude_word_harder` y 3 de `change_case:english_capital`, en tres instancias), y 29 de las 68 filas del registro bajan un punto. La configuración entregada sigue siendo la mejor del registro, pero su precisión en búsqueda pasa de 14 % a 13 %. La validación no cambia (9 de 87).

- Fuente: `resultados/fase0_verificacion_cache.json` y `resultados/registro_busqueda_recalificado_a4cd966.csv`.
- Las versiones anteriores (`b781e782a`, `8eae24043`) reproducen el registro salvo 1 o 2 veredictos de `change_case:english_capital`, que cambian de una corrida a otra porque esas versiones llaman a `langdetect` sin semilla: la calificación original tenía un componente aleatorio. Fuente: `resultados/fase0_verificacion_cache_oi_*.json`.
- **Qué hacer:** todas las precisiones, tablas de fallos y decisiones del informe, el manual y el README se regeneran desde el registro recalificado, y el informe explica el cambio de versión y la diferencia de 14 % a 13 %.

## 1. Informe (`Informe_primera_entrega_APA.pdf`), Fase 8

| # | Dónde | Problema | Corrección |
|---|---|---|---|
| I1 | Resumen y "Costo de la Búsqueda" | Mezcla "60 configuraciones distintas" con "6.800 consultas". Las 6.800 son 68 evaluaciones × 100 (incluye 8 repetidas que respondió el caché); las consultas nuevas en GPU fueron 6.000. | Definir los dos conteos (consultas registradas y consultas nuevas en GPU) y usarlos siempre con su nombre. |
| I2 | Resumen, Costo de la Búsqueda, Conclusiones | Fracción explorada "0,18 %" = 60/32.768: el numerador incluye las 2 configuraciones con temperatura ≠ 0,0 y el denominador las excluye. El notebook imprime otra cifra (0,069 % = 68/98.304), que cuenta evaluaciones repetidas. | **Definición única:** configuraciones distintas evaluadas / tamaño del espacio en que se buscó. La búsqueda varió la temperatura, así que el espacio es C′ (98.304) y la fracción es 60/98.304 ≈ 0,061 %. Generarla por script desde el registro. |
| I3 | Tabla 11 | La columna "Opciones omitidas por poda" suma omisiones de distintas pasadas (12 + 28 = 40). Ese total no cuenta opciones distintas y coincide por azar con el número total de opciones (5 × 8 = 40). | Reportar omisiones por pasada sin total, o reportar opciones distintas descartadas (29). |
| I4 | Limitaciones de la Evidencia | "28 de 40 (70 %)" usa como denominador todas las opciones; en cada pasada las alternativas son 35 (5 × 7). | Usar 35 como denominador o explicar qué se cuenta. |
| I5 | Parte 2, Elección del Modelo, Costo, Conclusiones | Los tiempos (209 s por 100 consultas, 2,1 s/consulta, 3,4 h, 79 días, 41 min) no salen de ningún archivo de resultados: la columna `segundos` del registro es 0,0 en todas las filas porque el notebook se volvió a ejecutar desde el caché. | Usar el costo medido en `resultados/fase0_verificacion_gpu.json` (indicando el hardware) o una medición nueva en T4 guardada en `resultados/`. Recalcular las cifras derivadas por script. |
| I6 | Todas las tablas de precisión y fallos (Tablas 10, 12, 13 y el párrafo de fallos que persisten) | Calificadas con los verificadores anteriores (sección 0). | Regenerar desde el registro recalificado. |
| I7 | Elección del Modelo | Atribuye al oráculo "el parámetro lote = 16"; 16 es el valor que pasa el notebook de búsqueda, no un valor del oráculo. | Decir que el notebook usa `lote=16` y `presupuesto=32_000_000`. |
| I8 | Alternativas Consideradas | "Successive Halving gastaría cerca de 280.000 consultas" no dice que supone n₀ = 1, el tope n = 100 y que cada ronda se evalúa desde cero (sin aprovechar las instancias ya evaluadas). | Sustituir por la fórmula cerrada de la Fase 4, con sus supuestos explícitos. |
| I9 | Tabla 7 | Successive Halving aparece como O(\|C\| log \|C\|) sin el tope de n instancias. | Usar el costo con tope de la Fase 4. |
| I10 | Entrada de la Parte 1 | "49 tipos distintos" es el número de tipos de restricción en búsqueda; búsqueda y validación juntas tienen 50. | Decir sobre qué partición se cuenta, con el número generado por script. |
| I11 | Reproducibilidad | Afirma que al volver a ejecutar el notebook "se obtienen las mismas decisiones". No era cierto: los notebooks clonaban la versión más reciente de open-instruct, cuyos verificadores cambiaron y además usaban `langdetect` sin semilla. | Explicar que los verificadores quedan fijados en `a4cd966` y qué cambia con eso. |
| I12 | Aclaraciones Resueltas / Algoritmos | Los errores del enunciado (3840, 144, 432, n = 150, 91.444, k_max = 4, falta del factor m en O(I·k·n₀), Cobertura Máxima frente a 3-SAT) se mencionan solo en parte. | Explicarlos todos en el informe final con la corrección y su porqué (Fases 4 y 8). |
| I13 | Formalización: Tamaño de la Entrada (Tabla 2) | **Retroalimentación de la docente, ítem 1.** Presenta \|C\| como tamaño de la entrada; la entrada es el catálogo (m ranuras con k_p opciones), las n instancias y el oráculo, y \|C\| = Πk_p es el espacio de búsqueda derivado, exponencial en m. | Redefinir el tamaño de la entrada como Θ(Σk_p + n) = Θ(m·k + n), presentar \|C\| como espacio de búsqueda, expresar toda T en m, k y n (Θ(\|C\|·n) = Θ(k^m·n)), explicar por qué el enunciado usa \|C\| y alinearlo con la generalización a m ranuras de la prueba de NP-dureza (docs/notas_informe_final.md, Sección 8). |
| I14 | Proceso de Optimización / algoritmos | **Retroalimentación de la docente, ítem 7.** El presupuesto B no se controlaba en los algoritmos. | Documentar el control de B (comprobación antes de cada evaluación, mejor configuración encontrada si no alcanza, modos de conteo nuevas/propias) y la evidencia de pruebas/test_presupuesto.py. |

## 2. Manual técnico (`Manual_tecnico.pdf`), Fase 9

| # | Dónde | Problema | Corrección |
|---|---|---|---|
| M1 | Figura 1 | Lista `docs/manual_tecnico.pdf` y `docs/manual_tecnico.md`; los dos se borraron y el archivo actual es `docs/Manual_tecnico.pdf`. | Regenerar la figura desde el árbol real del repositorio. |
| M2 | Tabla 1 | "Python 3 (probado con 3.13)", mientras el README dice "3.12 o superior" y el entorno local usa 3.12.10. | Una sola versión, la probada. |
| M3 | Reproducción de la Búsqueda | "Cada evaluación nueva tarda alrededor de 205 s", mientras el informe dice 209 s; ninguna de las dos cifras tiene fuente. | Igual que I5. |
| M4 | Resumen, Tabla 5, Figura 4 | Precisión 14,0 % calificada con los verificadores anteriores. | Igual que I6. |
| M5 | Entorno | Solo describe Colab. | Agregar el entorno local de CLAUDE.md §5: `PYTHONUTF8=1`, open-instruct en `a4cd966` en el `PYTHONPATH`, caché en `cache/`. |
| M6 | Pruebas sin GPU | "Python 3.9 o superior, solo biblioteca estándar": las pruebas nuevas usarán pytest. | Actualizar la lista de pruebas y sus requisitos. |
| M7 | Arquitectura | No incluye el paquete `src/oraculo_ada/`, `scripts/`, `resultados/` ni `figuras/` de la entrega final. | Actualizar cuando existan. |
| M8 | Funcionamiento / Uso | **Retroalimentación de la docente, ítem 7.** Falta documentar el presupuesto B. | Explicar el parámetro presupuesto de cada algoritmo, los modos de conteo y qué devuelven cuando B no alcanza; incluir pruebas/test_presupuesto.py en la tabla de pruebas. |

## 3. README y notebooks, Fase 9

| # | Dónde | Problema | Corrección |
|---|---|---|---|
| N1 | Celda 1 de los dos notebooks | Clonaban la versión más reciente de open-instruct. **Corregido en la Fase 0:** ahora hacen checkout de `a4cd966`. Las salidas guardadas del notebook de búsqueda se produjeron con la versión anterior, así que una nueva ejecución dará las precisiones recalificadas. | Explicarlo en el notebook y en el manual; decidir si se vuelve a ejecutar el notebook de búsqueda. |
| N2 | Celda 1 de los dos notebooks | Descargan `oraculo.py`, `ayudas.py` y `datos_visibles.json` de la rama `main` del repositorio del curso, no las copias del fork. Hoy el contenido es idéntico (solo difieren los finales de línea), pero un cambio en el repositorio del curso cambiaría la evaluación sin aviso. | Consultar si conviene fijar un commit del repositorio del curso. |
| N3 | Celda 1 de los dos notebooks | `pip install -U` sin versiones fijas (`transformers`, `accelerate`, `bitsandbytes`, …). | Evaluar si se fijan versiones probadas en T4. |
| N4 | Notebook de búsqueda, sección 9 | Imprime la fracción explorada como evaluaciones / 98.304 (0,069 %). | Usar la definición única de I2. |
| N5 | `resultados/registro_busqueda.csv` | La columna `segundos` es 0,0 en todas las filas (salidas reproducidas desde el caché). | Documentar que el registro no trae tiempos; los tiempos medidos van en archivos nuevos de `resultados/`. |
| N6 | README, tabla "Resultado" | 14,0 %, "0,18 %", "≈ 3,4 h de GPU T4". | Igual que I2, I5 e I6. |

## 4. Pendiente con el equipo docente

- **P1. Familias nuevas en el test privado.** El informe indica que el test privado incluye familias de restricciones que no están en `datos_visibles.json`. El notebook de evaluación crea el `Oraculo` sin el parámetro `registros` (verificadores adicionales, por ejemplo IFBench, según la documentación del constructor), así que una instancia con una restricción que no conocen los verificadores de IFEvalG puede hacer fallar la evaluación (`KeyError`). **El autor lo va a consultar con el monitor.** Según la respuesta, se ajusta el notebook de evaluación en la Fase 9 (sin romper la regla 3 de CLAUDE.md).
