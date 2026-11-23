# CLAUDE.md — Proyecto Oráculo (ADAG1), entrega final

Este archivo es el contexto permanente para Claude Code en este repositorio. Léelo completo antes de cualquier tarea y vuelve a él cuando tengas dudas. Si algo de este archivo contradice lo que pide el usuario en el chat, pregunta antes de actuar.

## 1. Quién soy y qué se entrega

- **Autor:** Juan Felipe Henao (trabajo individual). **Universidad:** Universidad de Caldas. **Curso:** Análisis y Diseño de Algoritmos (ADAG1), 2026-2. **Docente:** Luz Enith Guerrero Mendieta. **Monitor:** JuManoel.
- **Repositorio:** fork `Pipe-1z/ADA-2026-2-GP01` (de `JuManoel/ADA-2026-2-GP01`), rama `main`.
- **Lo que falta es la entrega final**, que reúne todo el proyecto: informe técnico final en APA, manual técnico en APA, repositorio completo y preparación de la sustentación (45 % de la nota: el autor debe explicar sin notas la reducción de NP-dureza y la deducción de T(n) del algoritmo exacto).
- **Nivel exigido:** cero inconsistencias. Cada número que aparezca en un documento debe salir de un archivo de resultados del repositorio, y cada afirmación teórica debe estar demostrada o citada.
- **Objetivo de mejora de la entrega final:** intentar superar el 13–14 % actual en búsqueda (13 % con los verificadores `a4cd966`, 14 % con los originales). Según el monitor, el techo está entre 24 y 28 % (comunicación personal; no es un resultado del repositorio). En el informe se cita en formato APA 7 de comunicación personal **solo en el texto**, por ejemplo "(JuManoel, comunicación personal, noviembre de 2026)", **sin entrada en la lista de referencias**. Causas probables del estancamiento: óptimo local, poda agresiva y permanente, punto de partida único y poco presupuesto. Las estrategias para escapar se comparan primero en el oráculo sintético calibrado (Fases 2b a 5) y la mejor se aplica con el modelo real en Colab T4 (Fase 7). Si ninguna mejora en búsqueda, se reporta así y `entrega.json` no cambia.

## 2. El problema (resumen)

Se busca una configuración de prompt que maximice la precisión de un LLM sobre instancias con restricciones verificables, gastando el menor número de consultas al modelo (cada consulta cuesta tiempo de GPU).

- **Ranuras (m = 5):** `rol`, `estrategia`, `formato`, `estilo`, `cierre`, cada una con **k = 8 opciones** (índices 0–7). Cada ranura actúa sobre una parte de la respuesta (inicio, largo, estructura, caracteres, final). Según el curso, en cada ranura solo una opción es "limpia".
- **Espacio:** |C| = 8⁵ = **32.768** configuraciones con temperatura 0,0; con la variante de temperatura {0,0; 0,3; 0,7}, |C′| = **98.304**. 32.768 = 2¹⁵.
- **Instancias (benchmark del curso, `datos_visibles.json`):** 100 de búsqueda (`n = 100`), 87 de validación, 263 descartadas. Cada instancia trae 2 o 3 restricciones (2,45 en promedio, 49 tipos). Evaluación **todo o nada**.
- **Oráculo del curso (`oraculo.py`, caja negra):** `Oraculo.evaluar(config, instancias, semilla)` → `precision`, `trazas` (`id`, `violo` = primera restricción violada, `salida`); `Oraculo.validar(config, n)`; `espacio(temps)`. Tiene caché; la clave incluye el nombre del modelo.
- **Modelo:** `qwen17b` = Qwen/Qwen3-1.7B en fp16. Costo en T4 según la primera entrega: ≈ 209 s por 100 consultas (≈ 2,1 s/consulta), **sin archivo de resultados que lo respalde** (regla 15). Medido en la GPU local: 4,5 s/consulta (`resultados/fase0_verificacion_gpu.json`).
- **Formalización en dos partes (obligatoria):**
  - **Parte 1, oráculo exacto:** max Acc(c) sobre C. Versión de decisión CONFIG-EXACTA. **Es NP-completa por reducción desde 3-SAT** (no desde Cobertura Máxima: la guía de la primera entrega fija 3-SAT para ADAG1). Ranura por variable con opciones {0,1}, instancia por cláusula, L_j = pares (p,1) por literal x_p y (p,0) por ¬x_p, umbral t = 1. Optimización NP-difícil; inaproximable mejor que 7/8 salvo P = NP (Håstad, 2001), porque Acc = fracción de cláusulas satisfechas (MAX-3-SAT).
  - **Parte 2, consultas limitadas y ruidosas:** salida (m₁,…,m_|C|) y c*, max Acc(c*) s.a. Σ m_j ≤ B, 0 ≤ m_j ≤ n. Se analiza por número de consultas y complejidad de muestreo (Hoeffding: m ≥ ln(2K/δ)/(2ε²)), **no** por NP-dureza.

## 3. Estado actual (primera entrega, ya enviada)

- **Método implementado:** ascenso por coordenadas guiado por trazas (Algoritmo 3), en `notebooks/notebook_busqueda.ipynb` (= `proyecto_oraculo.ipynb` con el punto 4 implementado).
  - Orden de ranuras por fallos en trazas; barrido de 7 opciones por ranura; empate → se conserva la actual; poda: opción descartada si suma ≥ 3 fallos en una familia y no mejora; máximo 3 pasadas; temperatura al final.
  - Cota: T ≤ n[1 + I·Σ(k_p − 1) + (|T| − 1)] = O(I·m·k·n) → 10.800 consultas con I = 3.
- **Resultado:** `{rol: 0, estrategia: 0, formato: 0, estilo: 5, cierre: 1, temperatura: 0.0}` → **14 %** en búsqueda (**13 %** recalificado con `a4cd966`, regla 13), **10,3 %** (9/87) en validación. 68 evaluaciones, 60 configuraciones distintas, ≈ 3,4 h de GPU. Convergió en la pasada 3. Temperatura 0,3 → 12 %, 0,7 → 11 %. Inicial (0,0,0,0,0) = 9 %.
- **Hallazgos:** estilo = 5 dio 9 % con cierre = 0 y 14 % con cierre = 1 (las ranuras **no** son independientes). 29 de 40 opciones descartadas por trazas. Techo del problema según el curso ≈ 24 %.
- **Archivos:** `entrega.json`, `notebooks/notebook_busqueda.ipynb`, `notebooks/notebook_evaluacion.ipynb`, `resultados/registro_busqueda.csv`, `pruebas/verificar_entrega.py`, `pruebas/prueba_sintetica.py`, `docs/Manual_tecnico.pdf`, `README.md`, `README_curso.md`.
- **Documentos de referencia** (el usuario los copia en `docs/referencia/`): enunciado `Proyecto_ADAG1.docx`, guía de la primera entrega (PDF), `Informe_primera_entrega_APA.pdf`, `Manual_tecnico_APA.pdf`, diapositivas del curso (correctitud y notaciones asintóticas). Léelos antes de redactar: el estilo de las deducciones de T(n) debe seguir las diapositivas.

## 4. Reglas que no se rompen

1. **No modificar** `oraculo.py`, `ayudas.py`, `datos_visibles.json` ni `proyecto_oraculo.ipynb`. Se consultan, no se editan.
2. **`entrega.json`** conserva el formato del curso: `{"grupo", "config": {rol, estrategia, formato, estilo, cierre, temperatura}, "semana"}`. Solo cambia si una búsqueda nueva encuentra una configuración mejor **en búsqueda**; nunca se elige con validación.
3. **`notebooks/notebook_evaluacion.ipynb`** debe seguir funcionando en Google Colab con GPU T4 sin editar nada (la docente lo corre ahí).
4. **Ningún número escrito a mano en los documentos.** Todo resultado se guarda en `resultados/` (JSON/CSV) y las tablas y figuras se generan con scripts. Si un número no existe en un archivo de resultados, no se escribe.
5. **Nunca afirmar optimalidad** de una configuración encontrada por heurística: se dice "mejor configuración encontrada".
6. **Pedir confirmación antes de cualquier corrida que use el modelo real** e informar antes el número de consultas y el tiempo estimado (usa ≈ 2,1 s/consulta en T4 hasta que exista la medición de la regla 15, o 4,5 s/consulta en la GPU local).
7. **Semillas fijas** en todo experimento; cada experimento guarda sus parámetros, su semilla, la versión del código (hash de git) y el hardware.
8. **Reutilizar el caché** del oráculo; no recalcular lo ya evaluado.
9. **Cada afirmación teórica** se demuestra en el informe o se cita (APA 7). Referencias ya usadas: Agrawal et al. (2025), Chang y Chen (2026), Cook (1971), Karp (1972), Håstad (2001), Hoeffding (1963), Qwen Team (2025), Wright (2015), DanielMelo404 (2026), JuManoel (2026). Para UCB1: Auer, Cesa-Bianchi y Fischer (2002). Para Successive Halving: Karnin, Koren y Somekh (2013) y Jamieson y Talwalkar (2016). Verifica cada referencia nueva antes de usarla.
10. **Idioma:** documentos en español; código con nombres en español, consistente con el notebook actual.
11. **Commits pequeños**, uno por tarea terminada, con mensaje descriptivo. No reescribir la historia.
12. **`oraculo.py` solo se usa a través de su interfaz pública:** `Oraculo.evaluar`, `Oraculo.validar`, `espacio` y `CATALOGO` (más `TEMPERATURAS`). No se lee ni se usa su contenido interno (constantes, comentarios, funciones o atributos privados): ni para buscar, ni para analizar, ni para probar configuraciones, ni para escribir documentos. El caché que escribe se trata como un archivo de datos (`[aprobada, restricción violada, salida]` por entrada; la clave contiene el id de la instancia).
13. **Verificadores de referencia:** `allenai/open-instruct` fijado en el commit `a4cd966a9e202843baba653115045e6fd6f473db` para todo el proyecto (entorno local y notebooks). Los números de la primera entrega se calificaron con una versión anterior; su recalificación con `a4cd966` está en `resultados/fase0_verificacion_cache.json` y `resultados/registro_busqueda_recalificado_a4cd966.csv`, y es la que se usa de aquí en adelante.
14. **Hardware de referencia y cachés separados por hardware:** todos los experimentos con el modelo real que entran al informe se corren en **Google Colab con GPU T4**; la GPU local (RTX 5050 Laptop) solo se usa para pruebas rápidas. La clave del caché del oráculo no incluye el hardware, así que `cache/cache_oraculo.json` (y su copia en Drive) contiene **solo salidas de la T4**; las salidas de cualquier otro hardware van en archivos aparte dentro de `cache/` (`cache_oraculo_<etiqueta-del-hardware>.json`) y nunca se mezclan con el de la T4. La diferencia medida entre la GPU local y la T4 (1 instancia por configuración) está en `resultados/fase0_resumen.json`.
16. **Experimentos de búsqueda para mejorar la configuración** (sintéticos y reales):
    - Todo punto inicial, muestra de instancias o elección al azar se genera con `random.Random(semilla)` y una semilla fija que se guarda en el resultado.
    - **Los parámetros se deciden antes de correr:** cada experimento escribe primero en `resultados/` un plan (estrategias, parámetros, semillas, presupuesto y criterio de elección) y solo después se ejecuta; el plan no se cambia a la vista de los resultados. Si hay que cambiarlo, se escribe un plan nuevo y se reportan los dos.
    - Ninguna decisión (puntos de partida, orden, opciones a probar, umbrales) puede apoyarse en información interna de `oraculo.py` (regla 12). El caso sintético calibrado se construyó solo con estadísticas públicas y del registro.
    - Con el modelo real: estimación de consultas y tiempo antes de correr y confirmación del usuario (regla 6). La validación se mide después y se reporta, pero no decide.
    - **Margen de mejora (decidido el 22 de noviembre de 2026, antes de ver resultados):** `entrega.json` solo cambia si la nueva configuración **supera a la actual por al menos 3 puntos en búsqueda** (≈ una desviación estándar con n = 100), comparando las dos con los mismos verificadores (`a4cd966`) y las mismas 100 instancias. Con la actual en 13 %, hace falta ≥ 16 %.
15. **El código corre igual en local y en Colab:** sin rutas absolutas ni dependencias de Windows; las rutas de caché y resultados se toman de la raíz del repositorio o de variables de entorno (para apuntar a Google Drive). La Fase 7 se ejecuta desde un notebook lanzador que clona el fork, instala dependencias con open-instruct en `a4cd966`, usa el caché en Drive y corre los scripts de experimentos. **En la primera corrida en la T4 se mide y se guarda en `resultados/` el costo por consulta**: el valor de ≈ 2,1 s/consulta todavía no está en ningún archivo.

## 5. Entorno local

El código del curso solo exige una GPU NVIDIA con CUDA: `cargar_modelo` usa `cuda:0` y fuerza fp16. No depende de Colab, salvo que `oraculo.py` busca los verificadores en `/content/open-instruct`. Como ese archivo no se modifica, el clon de `allenai/open-instruct` se agrega al `PYTHONPATH`.

Pasos (Windows con PowerShell, o WSL2 si algo falla):

1. Python 3.11 o 3.12 en un entorno virtual: `python -m venv .venv` y activarlo.
2. PyTorch con CUDA según la GPU (https://pytorch.org/get-started/locally/).
3. `pip install -U "bitsandbytes>=0.46.1" transformers accelerate nltk spacy emoji langdetect immutabledict pandas matplotlib tqdm pytest`
4. `python -m spacy download en_core_web_sm`
5. `git clone https://github.com/allenai/open-instruct ..\open-instruct` (fuera del repositorio), `git -C ..\open-instruct checkout a4cd966a9e202843baba653115045e6fd6f473db` (regla 13) y agregar esa ruta al `PYTHONPATH`.
6. Datos de nltk (`punkt`, `punkt_tab`, `averaged_perceptron_tagger`, `averaged_perceptron_tagger_eng`), igual que la celda 1 del notebook.
7. Copiar `cache_oraculo.json` desde Google Drive (`MyDrive/proyecto_oraculo/`) a `cache/cache_oraculo.json` y usarlo como caché local.
8. **`PYTHONUTF8=1`** en el entorno (`$env:PYTHONUTF8 = "1"` en PowerShell, `export PYTHONUTF8=1` en Git Bash). `ayudas.py` abre `datos_visibles.json` sin indicar codificación y en Windows Python usaría cp1252 (`UnicodeDecodeError`); como el archivo no se modifica, se activa el modo UTF-8 de Python.
9. **Verificación obligatoria antes de cualquier experimento:** `python scripts/fase0_verificacion.py --parte cache` (sin GPU) y `--parte gpu` (reevalúa (0,0,0,0,0) y (0,0,0,5,1) **sin caché** y compara con el registro). fp16 en otra GPU puede dar salidas distintas a la T4. Si no coinciden, documentarlo y decidir con el usuario qué hardware es la referencia: los resultados que entran al informe deben ser comparables entre sí.

`.venv/`, cachés y salidas pesadas van en `.gitignore`.

## 6. Requisitos de la entrega final (lista de control)

Del enunciado del proyecto:

- [ ] Definición precisa del tamaño de entrada (|C| y n).
- [ ] **T(n) del algoritmo exacto** deducida paso a paso (conteo de operaciones o recurrencia), con su notación asintótica.
- [ ] T(n) de cada heurística, y su garantía demostrable cuando exista (citada o demostrada).
- [ ] **Validación experimental:** tiempo real y número de consultas para valores crecientes de n y de |C| (al menos 5 tamaños, con repeticiones), graficados contra la T(n) teórica, como en clase.
- [ ] Al menos 3 de los 4 algoritmos implementados, analizados y comparados. **Se harán los 4:**
  - [ ] **Algoritmo 1:** backtracking con poda por cota superior: derivar O(|C|·n) en el peor caso y medir empíricamente cuánto poda frente a ese peor caso.
  - [ ] **Algoritmo 2:** Successive Halving: deducir el costo exacto paso a paso, incluido el tope de n instancias, y demostrar la cifra con los valores reales. El enunciado tiene errores numéricos (3840, 144, 91.444); se corrigen explicando por qué.
  - [ ] **Algoritmo 3:** búsqueda por coordenadas (ya implementada): análisis formal del riesgo de óptimos locales cuando las ranuras no son independientes, con un contraejemplo construido y medición empírica.
  - [ ] **Algoritmo 4:** reparto uniforme frente a adaptativo con el mismo presupuesto B, con datos y gráficas que muestren cuál aprovecha mejor B.
- [ ] Reducción de NP-dureza (desde 3-SAT, ya hecha; revisar y pulir).
- [ ] Variante: temperatura (hecha). Se agrega **UCB1** como esquema adaptativo del Algoritmo 4.
- [ ] Informe técnico final, manual técnico, repositorio reproducible, `entrega.json`, notebooks de búsqueda y evaluación coherentes.

## 7. Arquitectura propuesta

```
src/oraculo_ada/
  oraculos/
    real.py         # envoltura del Oraculo del curso: cuenta consultas, mide tiempo, usa caché
    sintetico.py    # oráculo sintético con estructura conocida (ver 7.1)
  algoritmos/
    fuerza_bruta.py
    backtracking.py      # Algoritmo 1
    successive_halving.py# Algoritmo 2
    coordenadas.py       # Algoritmo 3 (misma lógica que el notebook)
    reparto.py           # Algoritmo 4: uniforme, SH adaptativo, UCB1
  experimentos/     # un script por experimento; cada uno escribe en resultados/
  analisis/         # genera tablas y figuras desde resultados/
scripts/            # puntos de entrada de línea de comandos
pruebas/            # pytest
resultados/         # JSON/CSV: única fuente de verdad de los números
figuras/            # generadas, nunca editadas a mano
docs/
```

Todos los algoritmos reciben el mismo tipo de oráculo (interfaz común: `evaluar(config, instancias)` → precisión y trazas, más un contador de consultas), de modo que corren igual con el oráculo real y con el sintético.

### 7.1 Oráculo sintético

Necesario para la validación experimental con n y |C| crecientes sin gastar GPU, y para tener casos de resultado conocido.

- Parámetros comunes: m ranuras, k opciones por ranura, n instancias, semilla. Todo se genera con un `random.Random(semilla)` propio.
- Soporta **dos modelos**, que se eligen con un parámetro:
  - **Conjuntivo** (descripción del curso): hay un conjunto de familias de restricciones; cada opción (p, a) rompe un subconjunto R(p, a) de familias; cada instancia trae 2 o 3 familias y **pasa si ninguna de sus familias está rota**. El número de opciones "limpias" (R = ∅) por ranura es un parámetro (0 o más); si toda ranura tiene una opción limpia y no hay interacciones, el óptimo es trivial (Acc = 1), por eso los casos de prueba también deben incluir ranuras sin opción limpia.
  - **Disyuntivo** (el de la reducción desde 3-SAT): cada instancia i trae un conjunto L_i de pares (p, a) y **pasa si la configuración contiene al menos uno**. Con k = 2 y |L_i| = 3 sobre ranuras distintas, cada instancia es una cláusula de 3-SAT; el generador debe poder producir fórmulas aleatorias con una razón cláusulas/variables dada, para tener casos difíciles.
- **Interacciones que solo rompen** (en los dos modelos): pares de opciones de ranuras distintas ((p, a), (q, b)) que, cuando aparecen juntas, hacen fallar un conjunto de instancias (en el conjuntivo, rompen familias adicionales). Nunca reparan una instancia. Crean óptimos locales para el Algoritmo 3 sin romper la admisibilidad de la cota del Algoritmo 1, porque fijar más ranuras solo puede hacer fallar más instancias.
- Parámetro de **ruido** para la Parte 2: probabilidad de que una consulta devuelva el resultado contrario.
- Devuelve precisión y trazas con la misma forma que el oráculo real (`violo` = primera restricción/familia violada) y cuenta consultas.
- Debe poder calcular el **óptimo exacto** por fuerza bruta en tamaños pequeños.

### 7.2 Notas técnicas por algoritmo

- **Backtracking:** recorre el árbol ranura por ranura. Cota superior para una asignación parcial: la fracción de instancias que todavía pueden pasar. En el modelo conjuntivo, las que no tienen ninguna familia rota por las opciones ni por los pares ya fijados; en el disyuntivo, las que no tienen un par prohibido ya fijado y o bien ya están satisfechas o bien tienen algún par (p, a) en una ranura p sin fijar. Es válida porque en los dos modelos fijar más ranuras solo puede hacer fallar más instancias (las interacciones solo rompen), no porque exista una opción limpia. Demostrar que la cota es admisible (nunca subestima) y que la poda no descarta el óptimo, usando las técnicas de correctitud del curso. Con el oráculo real no hay una cota exacta conocida, así que el exacto se usa en el sintético y en el subespacio real de la Fase 7.
- **Successive Halving:** con |C| = 2^R y n_r = n₀·2^r, la ronda r cuesta |C|·n₀ hasta que n₀·2^r supera n; desde ahí se topa en n. Deducir la fórmula cerrada con el tope, verificarla contra el conteo real del código y analizar la probabilidad de eliminar la mejor configuración.
- **Coordenadas:** extraer la lógica del notebook a `coordenadas.py` **sin cambiar el comportamiento**; una prueba debe reproducir las decisiones del registro a partir del caché.
- **Reparto:** con el mismo B comparar uniforme, Successive Halving y UCB1. Métricas: probabilidad de elegir la mejor configuración y *simple regret* (Acc* − Acc del elegido), con ≥ 100 repeticiones en el sintético.

## 8. Plan por fases (de lo más pequeño a lo más grande)

Cada fase termina con: pruebas en verde, resultados guardados, commit y un resumen corto para el usuario. **No avanzar a la siguiente fase sin su visto bueno.**

| Fase | Contenido | Criterio de terminado |
|---|---|---|
| 0 | Entorno local (sección 5) y verificación contra el registro | (0,0,0,0,0) y (0,0,0,5,1) reproducidos o la diferencia documentada |
| 1 | Estructura del paquete, interfaz de oráculo, oráculo sintético, contador de consultas, cronómetro y registro de experimentos | Pruebas unitarias del sintético (óptimo conocido, semillas reproducibles) |
| 2 | Fuerza bruta y Algoritmo 3 extraído del notebook | Reproduce el registro real desde el caché; pasa en el sintético (**hecha**) |
| 2b | Variantes del Algoritmo 3 para escapar de óptimos locales, en el sintético calibrado: reinicios múltiples desde puntos al azar, poda no permanente o con umbral mayor, movimientos de dos ranuras con evaluación preliminar barata (submuestra de instancias); diagnóstico de por qué se estanca el Algoritmo 3 original (empates y poda) | Plan escrito antes de correr (regla 16); precisión final y consultas de cada variante, con ≥ 30 repeticiones por semilla |
| 3 | Algoritmo 1 (backtracking con cota) + demostración de la cota + T(n) | Coincide con fuerza bruta en todos los casos pequeños; nodos explorados medidos |
| 4 | Algoritmo 2 (Successive Halving) + fórmula exacta con tope; además, Successive Halving como estrategia de búsqueda sobre muestras grandes del espacio en el sintético calibrado, y la estrategia **"dos ranuras con filtro por Successive Halving"**: el vecindario completo de movimientos dobles de la configuración actual (C(5,2) = 10 pares de ranuras × 7 × 7 = 490 configuraciones) se evalúa con pocas instancias y solo las sobrevivientes llegan a las 100 | El conteo del código coincide con la fórmula para todo n₀, n y |C| probados; precisión y consultas de SH como estrategia |
| 5 | Algoritmo 4: uniforme, Successive Halving y UCB1 con el mismo B; **comparación final de todas las estrategias de mejora con el mismo presupuesto** (incluida "dos ranuras con filtro por Successive Halving") en las variantes calibradas (24 y 28 %) y en los casos teóricos, y elección de la que se aplicará en la Fase 7 | Gráficas de probabilidad de acierto y regret frente a B; tabla de estrategias con precisión, consultas y tiempo estimado en T4 |
| 6 | Validación experimental: para ≥ 5 tamaños de n y de |C|, medir **por separado** Q (consultas al oráculo, la métrica principal) y el cómputo en CPU (p. ej. cotas calculadas en el Algoritmo 1 y su tiempo de CPU, que no es tiempo de GPU), cada uno contra su función teórica | Figuras con curva teórica ajustada, pendiente log-log y tabla de cocientes observado/teórico, para Q y para el cómputo en CPU |
| 7 | Experimentos con el oráculo real en Colab T4 (notebook lanzador), **primero lo barato**: (1) medición del costo por consulta (regla 15); (2) la evaluación pendiente (0,0,0,6,1) que completa el camino del Algoritmo 3 con `a4cd966` (`resultados/fase2_coordenadas_reproduccion.json`); (3) movimientos de dos ranuras desde la configuración actual reutilizando el caché (≈ 2.800 consultas según la Fase 2b; recalcular en la Fase 5); (4) los reinicios solo si el presupuesto lo justifica después de la Fase 5. Además: subespacio pequeño con óptimo exacto (por ejemplo 2 opciones por ranura elegidas al azar con semilla fija = 32 configuraciones = 3.200 consultas) y comparación de los cuatro algoritmos; **aplicación de la mejor estrategia de mejora de la Fase 5**, con estimación de consultas y tiempo y confirmación antes de correr | Resultados reales guardados; `entrega.json` actualizado solo si mejora en búsqueda; validación medida después |
| 8 | Informe final en APA: ampliar el de la primera entrega con todos los algoritmos, deducciones, experimentos y conclusiones; tablas y figuras generadas por script | Cada número del informe trazable a `resultados/` |
| 9 | Manual técnico, README y notebooks actualizados | El notebook de evaluación corre en Colab T4 sin cambios |
| 10 | Auditoría final de consistencia (script que compara los números de los documentos con `resultados/`; revisión de referencias, enlaces, nombres de archivo y formato APA) | Cero diferencias |
| 11 | Preparación de la sustentación: guion, preguntas de práctica y respuestas sobre 3-SAT y T(n) | El autor puede explicar todo sin notas |

## 9. Cómo trabajar con el usuario

- Explica en español sencillo lo que vas a hacer antes de hacerlo, y lo que resultó al terminar.
- Antes de una corrida con GPU real: número de consultas, tiempo estimado y confirmación.
- Si encuentras una inconsistencia en el enunciado, en los documentos o en el código, repórtala con evidencia; no la "arregles" en silencio.
- El autor debe entender todo lo que se entrega: cuando escribas una deducción o una prueba, agrega una explicación intuitiva para la sustentación (en un archivo aparte, `docs/sustentacion/`, no dentro del informe).
