# Algoritmo 4: reparto del presupuesto B (uniforme, Successive Halving y UCB1)

Derivación para el informe final (Fase 8). Código: `src/oraculo_ada/algoritmos/reparto.py`; pruebas: `pruebas/test_reparto.py`; experimento: `scripts/fase5.py --correr reparto` → `resultados/fase5_reparto.json` (plan: `resultados/fase5_plan.json`); figuras: `scripts/fase5_figuras.py` → `figuras/`.

## 1. Problema (Parte 2 de la formalización)

Dado un conjunto S de configuraciones, n instancias y un presupuesto de B consultas, elegir una asignación (m_1, …, m_|S|) con Σ m_j ≤ B y 0 ≤ m_j ≤ n, y una configuración ganadora c*, para maximizar Acc(c*). Se mide con dos métricas, usando la verdad del oráculo sintético (que los esquemas no ven):

- **Probabilidad de elegir la mejor:** P(Acc(c*) = max_{c ∈ S} Acc(c)).
- **Simple regret:** Acc*(S) − Acc(c*), la precisión que se pierde por no elegir la mejor.

Los tres esquemas usan la misma permutación al azar de las instancias (muestras anidadas) y cuentan B en consultas nuevas.

## 2. Reparto uniforme

m = min(⌊B/|S|⌋, n) instancias por configuración; se elige la de mayor precisión observada (en empate, la primera de S). **Costo:** |S|·m ≤ B, es decir T(|S|, m) = Θ(|S|·m) (enunciado).

**Limitación (enunciado).** Con evaluación todo o nada y precisiones bajas, una configuración con precisión real μ tiene probabilidad (1 − μ)^m de no acertar ninguna de sus m instancias. Con μ = 0,24 y m = 2, por ejemplo, (0,76)² ≈ 0,58: más de la mitad de las veces la mejor configuración "parece 0 %". Con muchas configuraciones empatadas en 0 % o en 1/m, la elección es casi al azar entre ellas. Es la misma causa por la que Successive Halving con n₀ = 2 eliminó a la mejor del vecindario doble en cerca de la mitad de las repeticiones en el caso calibrado de 24 % (`resultados/fase4_probabilidad_sh.json`): las primeras rondas deciden con 2 o 4 instancias, donde el ruido de muestreo domina las diferencias reales.

## 3. Successive Halving con presupuesto

Se toma el mayor n₀ entero tal que Q_con(|S|, n₀, n) ≤ B (fórmula de la Fase 4, con reutilización); si ni n₀ = 1 cabe, el esquema no es factible con ese B. Concentra las consultas en las configuraciones que sobreviven, de modo que la ganadora termina evaluada con muchas más instancias que en el reparto uniforme con el mismo B. Su costo y su análisis son los del Algoritmo 2 (`docs/derivaciones/algoritmo2_successive_halving.md`).

## 4. UCB1

**Definición** (Auer, Cesa-Bianchi y Fischer, 2002, Figura 1, p. 237): cada configuración es un "brazo"; jugarlo es evaluarla en su siguiente instancia (recompensa 1 si la respuesta cumple todas las restricciones y 0 si no). Inicialización: jugar cada brazo una vez. Después, jugar el brazo j que maximiza

  x̄_j + √(2 ln t / n_j),

donde x̄_j es la recompensa media del brazo j, n_j el número de veces que se ha jugado y t el número total de jugadas. En este proyecto, un brazo que ya usó las n instancias se conoce con exactitud y no se vuelve a jugar, y al agotar B se recomienda el brazo **más jugado** (en empate, el de mayor media).

**Garantía** (Teorema 1, p. 237, verificado en el artículo). Para K > 1 brazos con distribuciones de recompensa arbitrarias con soporte en [0, 1], el regret esperado de UCB1 después de cualquier número n de jugadas es a lo sumo

  [ 8 · Σ_{i : μ_i < μ*} (ln n / Δ_i) ] + (1 + π²/3) · ( Σ_{j=1}^{K} Δ_j ),

donde μ_i es la recompensa esperada del brazo i, μ* = max_i μ_i y Δ_i = μ* − μ_i. El regret se define como μ*·n − Σ_j μ_j·E[T_j(n)] (p. 236), con T_j(n) el número de veces que se jugó el brazo j en las primeras n jugadas.

**Cómo se aplica aquí (y cómo no):**

1. *Es una garantía de regret acumulado, no de elegir la mejor.* Dice que UCB1 juega pocas veces los brazos malos (O(ln n / Δ_i²) veces cada uno, de lo que sale el término ln n / Δ_i), no que su recomendación final sea la mejor. El objetivo del Algoritmo 4 es el simple regret, que se mide empíricamente.
2. *Supuestos.* El teorema supone recompensas independientes e idénticamente distribuidas para cada brazo (p. 236). Aquí cada brazo recorre las instancias de una permutación sin reemplazo de una población finita de n instancias, así que las recompensas no son independientes en sentido estricto. La herramienta de la demostración (la desigualdad de Chernoff-Hoeffding) sigue valiendo para muestras sin reemplazo (Hoeffding, 1963), pero el teorema se usa como referencia del comportamiento esperado, no como una garantía demostrada para este caso.
3. *Costo.* Cada jugada es una consulta: UCB1 usa exactamente min(B, |S|·n) consultas. El cálculo del índice es cómputo en CPU de orden |S| por jugada (O(B·|S|) en total), que no consume consultas.

## 5. Medición

`scripts/fase5.py --correr reparto` compara los tres esquemas con B = b·|S|, b ∈ {2, 4, 8, 16, 32}, en dos conjuntos por caso (128 configuraciones al azar y el vecindario doble de 490 desde el resultado del Algoritmo 3), en los 3 primeros casos de cada variante (calibrada 24 %, calibrada 28 %, disyuntiva y sin opciones limpias), con 100 permutaciones de las instancias por combinación. Resultados en `resultados/fase5_reparto.json`; gráficas de probabilidad de acierto y simple regret frente a B en `figuras/`.
