# Algoritmo 2: Successive Halving (divide y vencerás por rondas)

Derivación formal para el informe final (Fase 8). Código: `src/oraculo_ada/algoritmos/successive_halving.py` (algoritmo, conteo y fórmulas) y `src/oraculo_ada/algoritmos/estrategias.py` (usos como estrategia); pruebas: `pruebas/test_successive_halving.py`; verificación y cifras: `scripts/fase4_formula_sh.py` → `resultados/fase4_formula_sh.json`; experimentos: `scripts/fase4_estrategias.py` → `resultados/fase4_estrategias.json` y `resultados/fase4_probabilidad_sh.json`. Las cifras de este documento son las que calcula ese script; el informe las toma del archivo.

## 1. Entrada, parámetros y operación básica

**Tamaño de la entrada.** Como en el Algoritmo 1 (`algoritmo1_backtracking.md`, Sección 1), la entrada del problema es el catálogo (m ranuras con k_p opciones), las n instancias y el oráculo, de tamaño Θ(m·k + n); |C| = k^m es el espacio de búsqueda derivado. Successive Halving recibe además una **lista explícita** de candidatos S: si S es una muestra o un vecindario, |S| sí es parte de su entrada (la lista se escribe); si S = C, |S| = k^m y todas las expresiones de abajo con |S| se leen con |S| = k^m (por ejemplo, Q_sin = Θ(k^m · n₀ · min(m·log₂k, log₂(n/n₀)))).

- S: conjunto de configuraciones candidatas (todo C, una muestra de C o un vecindario); |S| su tamaño.
- n: número de instancias disponibles (el **tope**; n = 100 en el repositorio, 150 en el enunciado).
- n₀ ≥ 1: tamaño de la muestra de la primera ronda.
- Una permutación al azar de las n instancias, con semilla fija; la ronda r usa sus primeras n_r instancias (muestras **anidadas**).
- **Operación básica:** la consulta (evaluar una configuración sobre una instancia). El ordenamiento de cada ronda es cómputo en CPU de orden |S_r| log |S_r|, despreciable frente a las consultas, y se reporta aparte.

## 2. Mecánica

En la ronda r = 0, 1, …, cada sobreviviente se evalúa sobre las primeras

  n_r = min(n₀ · 2^r, n)

instancias; se ordenan por precisión (en empate, por la posición en la lista anterior) y sobreviven las ⌈|S_r| / 2⌉ mejores. Se repite hasta que queda una sola. Con |S| = 2^R hay exactamente R rondas y |S_r| = 2^{R−r}; en general hay ⌈log₂|S|⌉ rondas.

## 3. Correctitud (sin ruido de muestreo)

**Invariante.** Si en cada ronda la precisión se mide sobre toda la población (n_r = n), al comenzar cada ronda S_r contiene una configuración de precisión máxima en S.

- *Inicialización:* S_0 = S.
- *Mantenimiento:* una configuración óptima de S que está en S_r tiene el puntaje máximo de la ronda, así que queda entre las ⌈|S_r|/2⌉ primeras (o empata con otra óptima que queda); S_{r+1} sigue conteniendo una óptima.
- *Terminación:* para s ≥ 2, ⌈s/2⌉ < s, así que |S_r| decrece estrictamente mientras sea mayor que 1 y el ciclo termina después de ⌈log₂|S|⌉ rondas con un solo sobreviviente, que por el invariante es óptimo.

Con muestras (n_r < n) la medición tiene error y la mejor puede eliminarse: se acota en la Sección 7.

## 4. Costo exacto sin reutilizar (la forma del enunciado)

Si cada ronda evalúa a sus sobrevivientes desde cero, la ronda r cuesta |S_r| · n_r consultas y

  Q_sin = Σ_{r=0}^{R−1} 2^{R−r} · min(n₀ · 2^r, n).

Sea ρ el número de rondas que **no** tocan el tope: ρ = #{r < R : n₀ · 2^r < n} = min(R, ⌈log₂(n/n₀)⌉). Se parte la suma en ρ:

- Rondas r < ρ (sin tope): 2^{R−r} · n₀ · 2^r = 2^R · n₀ = |S| · n₀ cada una. Suman |S| · n₀ · ρ.
- Rondas r ≥ ρ (con tope): 2^{R−r} · n. Con j = R − r: n · Σ_{j=1}^{R−ρ} 2^j = n · (2^{R−ρ+1} − 2) (serie geométrica).

  **Q_sin = |S| · n₀ · ρ + n · (2^{R−ρ+1} − 2).**

**Sin tope** (n₀ · 2^{R−1} ≤ n, es decir ρ = R, o ρ = R − 1 con la última ronda justo en el tope): la segunda parte vale 0 (o n · 2 = n₀ · 2^R) y Q_sin = |S| · n₀ · log₂|S|, **la fórmula del enunciado**.

**Notación asintótica.** Si ρ < R, por la definición de ρ, n ≤ n₀ · 2^ρ, luego 2^{R−ρ} = |S| / 2^ρ ≤ |S| · n₀ / n y la segunda parte es a lo sumo 2 · |S| · n₀. Así, para ρ ≥ 1:

  |S| · n₀ · ρ ≤ Q_sin ≤ |S| · n₀ · (ρ + 2) ≤ 3 · |S| · n₀ · ρ,

y con c₁ = 1, c₂ = 3: **Q_sin = Θ(|S| · n₀ · ρ) = Θ(|S| · n₀ · min(log₂|S|, log₂(n/n₀)))**. Solo es O(|S| log |S|) "independiente de n" mientras el tope no se alcanza; con el tope, el número de rondas caras depende de n/n₀. Si n₀ ≥ n (ρ = 0), todas las rondas usan las n instancias y Q_sin = n · (2|S| − 2) = Θ(|S| · n).

## 5. Costo con reutilización (lo que cobra el oráculo con caché)

Como las muestras están anidadas y el oráculo no vuelve a cobrar una consulta ya hecha, cada configuración paga solo hasta el n_r de la **última** ronda en que se evaluó. En la ronda r se eliminan |S_r| − |S_{r+1}| = 2^{R−r−1} configuraciones, y el ganador se evaluó en la última ronda:

  Q_con = Σ_{r=0}^{R−1} 2^{R−r−1} · n_r + n_{R−1}.

Partiendo igual en ρ: las rondas r < ρ aportan 2^{R−r−1} · n₀ · 2^r = (|S|/2) · n₀ cada una; las rondas r ≥ ρ aportan n · Σ_{j=0}^{R−ρ−1} 2^j = n · (2^{R−ρ} − 1). Luego

  **Q_con = (|S|/2) · n₀ · ρ + n · (2^{R−ρ} − 1) + min(n₀ · 2^{R−1}, n),**

aproximadamente la mitad de Q_sin. Para tener la precisión del ganador sobre las n instancias se agregan n − n_{R−1} consultas (cero si la última ronda ya usó el tope).

**Verificación.** La fórmula cerrada coincide con el conteo ronda por ronda en los 555 casos de la rejilla R = 1..15, n₀ ∈ {1, 2, 3, 4, 5, 8, 16}, n ∈ {1, 2, 10, 50, 100, 150, 1000}, y el código del algoritmo cobra exactamente Q_sin y Q_con (más el ganador) en 40 corridas reales (`resultados/fase4_formula_sh.json`, `verificacion_formula` y `verificacion_codigo`; pruebas `test_formula_cerrada_coincide_con_el_conteo_por_rondas` y `test_el_codigo_cobra_lo_que_dice_la_formula`).

## 6. Las cifras del proyecto y los errores del enunciado

**Caso del proyecto** (|C| = 8^5 = 2^15, así que R = 15 y la mitad es siempre exacta; n₀ = 1; n = 100):

- n_r = 1, 2, 4, 8, 16, 32, 64 para r = 0..6, y 128 ≥ 100 en r = 7: ρ = 7.
- Q_sin = 2^15 · 1 · 7 + 100 · (2^{15−7+1} − 2) = 229.376 + 100 · 510 = **280.376** consultas.
- Q_con = 2^14 · 1 · 7 + 100 · (2^8 − 1) + min(2^14, 100) = 114.688 + 25.500 + 100 = **140.288** consultas.
- La fórmula del enunciado sin tope daría 2^15 · 1 · 15 = 491.520: el tope reduce el costo real.

**Errores del enunciado** ("Para |C| = 144 y n₀ = 2, … T(3840, 2) = 3840 · 2 · log₂ 3840 = 91444"):

1. *Valores mezclados.* El texto dice |C| = 144 y calcula con |C| = 3840. Ninguno es el del repositorio del curso (8^5 = 32.768, o 98.304 con temperatura).
2. *Redondeo.* 3840 · 2 · log₂ 3840 = 91.444,92…; la cifra 91.444 está truncada.
3. *La fórmula supone mitades exactas.* 3840 no es potencia de 2 (log₂ 3840 ≈ 11,91 no es entero): el algoritmo hace ⌈log₂ 3840⌉ = 12 rondas con ⌈|S_r|/2⌉ sobrevivientes, y el conteo exacto sin tope es **93.696**, no 91.445.
4. *Ignora el tope de instancias.* Con n₀ = 2, la ronda 7 ya pediría 256 > 150 instancias. Con el tope del enunciado (n = 150) el costo exacto es **62.610** (sin reutilizar) o **31.380** (con reutilización); con el del repositorio (n = 100), **57.980** o **29.040**. El costo **sí depende de n**.
5. *"O(|C| log |C|) independiente de n"* solo vale sin tope; con tope el orden es Θ(|C| · n₀ · min(log₂|C|, log₂(n/n₀))) (Sección 4).
6. *No distingue reutilización.* Con muestras anidadas y caché, el costo real es aproximadamente la mitad (Q_con).

Las mismas cuentas para |C| = 144 y |C| = 432 (variante con temperatura del enunciado) y para |C′| = 98.304 están en `resultados/fase4_formula_sh.json` (`cifras`).

## 7. Probabilidad de eliminar a la mejor configuración

Sea μ_j la precisión de la configuración j sobre la población de n instancias, μ* = max_j μ_j y Δ_j = μ* − μ_j ≥ 0. En la ronda r las dos se evalúan sobre las mismas n_r instancias, sorteadas sin reemplazo de la población.

1. *Comparación por pares.* La diferencia por instancia, Y_i − X_i (X de la mejor, Y de j), está en [−1, 1] y tiene media −Δ_j. Por la desigualdad de Hoeffding (1963), que vale también para muestras sin reemplazo de una población finita, P(μ̂_j ≥ μ̂*) ≤ exp(−2 n_r Δ_j² / 2²) = exp(−n_r Δ_j² / 2).
2. *Una ronda.* La mejor sale en la ronda r solo si al menos ⌈|S_r|/2⌉ de los demás sobrevivientes la igualan o superan. Sea N_r ese número; por la desigualdad de Markov, P(N_r ≥ ⌈|S_r|/2⌉) ≤ E[N_r] / ⌈|S_r|/2⌉. En el peor caso los otros |S_r| − 1 sobrevivientes son los de menor brecha Δ_(1) ≤ Δ_(2) ≤ …, así que

  P_r ≤ min(1, Σ_{j=1}^{|S_r|−1} exp(−n_r Δ_(j)² / 2) / ⌈|S_r|/2⌉).

3. *Rondas exactas.* Si n_r = n, la medición es exacta y sobrevive una óptima: P_r = 0.
4. *Todas las rondas.* Por la cota de la unión, P(el ganador no es óptimo) ≤ Σ_r P_r.

Es el argumento de Karnin, Koren y Somekh (2013) adaptado a este caso. La cota es conservadora: cuenta en contra a los competidores empatados con la mejor (Δ = 0 aporta 1) y puede superar 1, en cuyo caso no informa nada; por eso se compara con la frecuencia observada en el sintético con 200 permutaciones distintas de las instancias (`resultados/fase4_probabilidad_sh.json`). En todos los casos medidos la cota resultó mayor que 1, es decir, **no informativa**: con brechas de pocos puntos porcentuales y muestras de 1 a 64 instancias, cada término exp(−n_r Δ²/2) es cercano a 1. Lo que informa es la frecuencia observada, y el informe debe decirlo así. Consecuencia práctica: con n₀ pequeño, las primeras rondas deciden con muy pocas instancias, y con evaluación todo o nada y precisiones bajas (≈ 0,1) las brechas son pequeñas; el riesgo se concentra en esas rondas.

## 8. Successive Halving como estrategia de búsqueda

- **SH sobre una muestra** (`sh_muestra`): M configuraciones sorteadas de manera uniforme de C; costo exacto Q_con(M, n₀, n) (más el ganador). Con M = |C| es SH sobre todo el espacio.
- **Dos ranuras con filtro por SH** (`dos_ranuras_sh`): se corre el Algoritmo 3 y, desde su resultado x, se aplica SH al vecindario completo de movimientos dobles de x, de C(m, 2) · (k − 1)² = 10 · 49 = 490 configuraciones (m = 5, k = 8). Si el ganador mejora a x sobre las n instancias, se adopta y se corre de nuevo el Algoritmo 3 desde él; a lo sumo 2 rondas. Cada filtro cuesta a lo sumo Q_con(490, n₀, n) + n consultas.

Sus resultados en el sintético (precisión, brecha y consultas por variante) están en `resultados/fase4_estrategias.json`; la comparación con el mismo presupuesto es de la Fase 5.
