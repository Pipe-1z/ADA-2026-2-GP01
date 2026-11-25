# Notas para el informe final (Fase 8)

Puntos que deben entrar en el informe final, anotados durante el desarrollo. Ningún número se copia de aquí al informe: cada uno se toma del archivo de `resultados/` indicado, mediante el script que genere la tabla o el texto.

## 1. Evidencia de que las ranuras reales interactúan (apoya los casos con pares acoplados)

- En el registro de la primera entrega, la opción `estilo = 5` dio una precisión con `cierre = 0` (paso 6, configuración (0,0,0,5,0)) y otra mayor con `cierre = 1` (paso 40, configuración (0,0,0,5,1)). El efecto de una opción depende de las demás: las ranuras no son independientes.
- Fuente: `resultados/registro_busqueda.csv` (veredictos originales) y `resultados/registro_busqueda_recalificado_a4cd966.csv` (verificadores de referencia). La diferencia se mantiene con los dos verificadores.
- Uso en el informe: justificar que el oráculo sintético incluya interacciones y pares acoplados (CLAUDE.md §7.1) y que el riesgo de óptimos locales del Algoritmo 3 no es solo teórico. Aclarar que esto prueba **dependencia** entre ranuras, no que el mecanismo real sea exactamente un par acoplado.

## 2. Etiqueta del diagnóstico de la Fase 2b: "descartada solo por cambio de familia"

- En `resultados/fase2b_estrategias.json` (`diagnostico_original`), la cuenta `acoplada_descartada_solo_por_cambio_de_familia` es alta. Es técnicamente correcta: los aumentos de 3 o más fallos en una familia que dispararon el descarte vienen de instancias que ya fallaban y cambiaron de primera restricción violada; las instancias que fallan por primera vez se reparten entre familias y ninguna llega al umbral.
- Pero esas opciones **sí empeoran la precisión** (una opción acoplada sola deja la configuración en 0), así que el descarte no causó el estancamiento: la opción se habría rechazado igual por precisión. El informe debe explicarlo para que la etiqueta no se lea como "la poda descartó opciones buenas".
- Dato que sí importa: la poda **nunca** descartó la opción limpia de una ranura libre (sin acoplar) en las variantes calibradas (`libre_descartada` no aparece en el diagnóstico).

## 3. Techo según el monitor

- Citar en el texto, en formato APA 7 de comunicación personal: "(JuManoel, comunicación personal, noviembre de 2026)", sin entrada en la lista de referencias (CLAUDE.md §1).

## 4. Algoritmo 1: dónde poda poco la cota, y la NP-dureza

- Destacar que en los casos **disyuntivos** (el modelo de la reducción desde 3-SAT) la cota casi no poda: en el disyuntivo genérico con k = 8 y tres pares por instancia, el backtracking evalúa prácticamente todas las hojas (`resultados/fase3_backtracking.json`, familia `disyuntivo`), mientras que en los casos conjuntivos (los del curso) evalúa una fracción mínima.
- Relacionarlo con la NP-dureza demostrada: en el modelo que contiene a 3-SAT ninguna cota sencilla puede garantizar poda (si siempre podara a un número polinomial de nodos, se resolvería 3-SAT en tiempo polinomial).
- **Matiz obligatorio para no exagerar:** en las fórmulas 3-SAT aleatorias medidas (k = 2) la cota sí poda una fracción grande del árbol, aunque los nodos explorados crecen de forma exponencial con el número de variables (familias `3sat_v*` del mismo archivo). La NP-dureza es una afirmación de peor caso.
- Presentar Q (consultas) y K (cómputo de cotas) por separado (`docs/derivaciones/algoritmo1_backtracking.md`, Sección 6), y la respuesta sobre el modelo de información de la cota (Sección 7).

## 5. Algoritmo 4: el ruido con muestras pequeñas (SH con n₀ = 2 y la limitación del reparto uniforme)

- Conectar dos hallazgos: (a) Successive Halving con n₀ = 2 eliminó a la mejor configuración del vecindario doble en cerca de la mitad de las repeticiones en el caso calibrado de 24 % (`resultados/fase4_probabilidad_sh.json`); (b) la limitación del reparto uniforme que menciona el enunciado ("muchas configuraciones buenas parecen tener 0 % por puro ruido").
- Causa común: con evaluación todo o nada y precisiones bajas, la probabilidad de que una configuración con precisión real μ no acierte ninguna de m instancias es (1 − μ)^m; con pocas instancias, las diferencias reales quedan tapadas por el ruido de muestreo. Ver `docs/derivaciones/algoritmo4_reparto.md`, Sección 2, y los resultados del Algoritmo 4 en `resultados/fase5_reparto.json`.
- UCB1: citar el Teorema 1 de Auer, Cesa-Bianchi y Fischer (2002, p. 237) y aclarar que es una garantía de regret acumulado bajo recompensas independientes (Sección 4 de la misma derivación).

## 6. Validación experimental (Fase 6): cómo leer las figuras

- Fuentes: `resultados/fase6_validacion.json` (resumen), `resultados/fase6_cocientes.md` (tablas de cocientes generadas), `figuras/fase6_*.png`.
- **Q** coincide con la fórmula teórica en todos los algoritmos con conteo exacto (cociente 1 en todos los tamaños); en el Algoritmo 3, Q queda por debajo de su cota superior.
- **Tiempo de CPU** (con el oráculo sintético, no de GPU): se modela con dos términos, un costo fijo por evaluación más un costo por consulta, porque en tamaños pequeños el costo fijo domina y baja la pendiente observada. Explicar que por eso la pendiente observada puede quedar por debajo de la del término dominante y que se acerca a ella al crecer el tamaño.
- **UCB1 frente a |S|:** el término asintótico B·|S| del cálculo del índice tiene un coeficiente tan pequeño (cálculo vectorizado) que en el rango medido (|S| ≤ 1024) domina el costo por jugada; la pendiente observada queda cerca de 1, no de 2. Decirlo así, sin afirmar que se observó el término cuadrático.
- **Backtracking en 3-SAT:** se compara con el peor caso, no se ajusta: Q y K contra el peor caso sin escalar, y el tiempo contra el peor caso con la constante de CPU medida en el peor caso construido. Lo observado queda varios órdenes por debajo y su pendiente log-log es menor que 1, aunque crece con |C| (coherente con la Sección 4 de estas notas).

## 7. Tiempo real en la T4 contra n (Fase 7, paso a)

- Fuente: `resultados/fase7_tiempo.json` (se genera en Colab). Cada medición genera todas sus respuestas (caché vacío propio), para que el tiempo no salga artificialmente bajo.
- **Efecto del lote de 16:** el oráculo genera las respuestas por lotes de hasta 16 prompts (`lote=16`, parámetro público del constructor, el mismo del notebook de búsqueda). Generar un lote de 1 o de 16 prompts cuesta parecido (la GPU los procesa en paralelo y el tiempo lo fija sobre todo el prompt y la respuesta más largos del lote), así que el tiempo crece por **escalones** de ⌈n/16⌉ lotes y no de forma perfectamente proporcional a n: n = 10 usa 1 lote nominal, n = 25 usa 2, n = 50 usa 4 y n = 100 usa 7. Explicar que el ajuste lineal T = a + b·n describe la tendencia y que las desviaciones respecto a la recta vienen de esos escalones (y de que el oráculo también parte lotes por largo de prompt).
- Relacionarlo con la validación sintética (Fase 6): allí el costo por consulta es constante por construcción; en la T4 el costo marginal por consulta se mide con la pendiente b.

## 8. Retroalimentación de la docente a la primera entrega (24 de noviembre de 2026)

El archivo completo de la retroalimentación todavía no está en `docs/referencia/`; estos puntos son los que el autor transmitió.

**Ítem 1: tamaño de la entrada frente a espacio de búsqueda.**
- Redefinir en el informe: la entrada es el catálogo (m ranuras con k_p opciones), las n instancias y el oráculo; su tamaño es Θ(Σ_p k_p + n), es decir Θ(m·k + n) con k_p = k. |C| = Π_p k_p (= k^m) es el **espacio de búsqueda derivado**, exponencial en m.
- Todas las funciones de eficiencia en esos términos: fuerza bruta y backtracking en el peor caso Q = Θ(k^m · n) (abreviado Θ(|C|·n)); Successive Halving sobre todo C, Θ(k^m · n₀ · min(m·log₂k, log₂(n/n₀))); Algoritmo 3, O(I·m·k·n), **polinomial** en el tamaño de la entrada; Algoritmo 4 recibe S como lista explícita, así que ahí |S| sí es parte de su entrada.
- Explicar por qué el enunciado usa |C| (la Parte 2 reparte consultas entre configuraciones enumeradas, y con m = 5, k = 8 fijos |C| es constante) y por qué eso no es el tamaño de la entrada (si lo fuera, con m fijo la fuerza bruta sería O(n) y el problema no podría ser NP-difícil).
- Coherencia con la NP-dureza: en la reducción desde 3-SAT, m = v (una ranura por variable), k = 2 y n = N (una instancia por cláusula): la entrada construida tiene tamaño Θ(v + N), polinomial, y el espacio de búsqueda 2^v. Redacción base en `docs/derivaciones/algoritmo1_backtracking.md`, Sección 1.

**Ítem 7: control del presupuesto B.**
- Todos los algoritmos de búsqueda (coordenadas y sus variantes, reinicios, Successive Halving, SH sobre muestra, dos ranuras + SH, uniforme, UCB1, fuerza bruta y backtracking) reciben B y comprueban, **antes de cada evaluación**, que su costo no supere el presupuesto restante; si no alcanza, se detienen y devuelven la mejor configuración encontrada (ninguna si B no alcanzó ni para una evaluación). Implementación: `OraculoBase.presupuesto`, `costo_evaluacion` y `PresupuestoAgotado` (`src/oraculo_ada/oraculos/base.py`).
- Dos formas de contar B: consultas **nuevas** (las que no están en el caché; costo real en GPU, la de la Fase 7) y consultas **propias** de la corrida (como si el caché estuviera vacío; la de las comparaciones sobre configuraciones ya evaluadas).
- Evidencia: `pruebas/test_presupuesto.py` (ningún algoritmo supera B para una serie de valores de B, incluido B menor que una evaluación; con B holgado el resultado es idéntico al de la corrida sin presupuesto; presupuestos anidados). Documentarlo en el informe y en el manual.

**Test privado.** La configuración de la primera entrega obtuvo 0,1259 frente a un máximo teórico de 0,2007 en el test privado (`resultados/datos_externos.json`, dato externo). Usarlo como motivación de la estrategia de mejora de la Fase 7, aclarando que el test privado no se usa para elegir nada.

## 9. Correcciones de la primera entrega

- Ver `docs/correcciones_primera_entrega.md` (Fases 8 y 9).
