# Algoritmo 1: backtracking con poda por cota superior

Derivación formal para el informe final (Fase 8). Código: `src/oraculo_ada/algoritmos/backtracking.py`; cota: `OraculoSintetico.instancias_vivas` y `cota_superior` en `src/oraculo_ada/oraculos/sintetico.py`; pruebas: `pruebas/test_backtracking.py`; medición: `scripts/fase3_backtracking.py` → `resultados/fase3_backtracking.json`. Este documento no contiene resultados medidos: las tablas del informe se generan desde ese archivo.

## 1. Tamaño de la entrada y operación básica

- m: número de ranuras; k_p: opciones de la ranura p (p = 1, …, m); en el proyecto k_p = k = 8.
- |C| = k_1 · k_2 · … · k_m (con k_p = k: |C| = k^m); n: número de instancias.
- **Operación básica:** la **consulta**, evaluar una configuración sobre una instancia. Evaluar una hoja cuesta n consultas.
- **Operación secundaria:** calcular la cota de un nodo interno. No consulta al modelo; recorre las n instancias y, en cada una, sus a lo sumo L pares o familias (L ≤ 4 en los generadores) y las interacciones activas. Su costo es a lo sumo c · n operaciones elementales, con c constante cuando L y el número de interacciones por instancia están acotados.

## 2. Árbol de decisiones

Un nodo de nivel d (0 ≤ d ≤ m) es una asignación parcial σ = (σ_1, …, σ_d) de las primeras d ranuras. La raíz es la asignación vacía (d = 0); las hojas (d = m) son las configuraciones completas. Cada nodo de nivel d < m tiene k_{d+1} hijos, uno por opción de la ranura d + 1.

Por el principio multiplicativo, el número de nodos del nivel d es

  N_d = k_1 · k_2 · … · k_d  (N_0 = 1),  y con k_p = k:  N_d = k^d.

Total de nodos: N = Σ_{d=0}^{m} k^d = (k^{m+1} − 1)/(k − 1) (serie geométrica, k ≥ 2). Hojas: N_m = k^m = |C|. Nodos internos: Σ_{d=0}^{m−1} k^d = (k^m − 1)/(k − 1).

Notación: c ⊒ σ significa que la configuración completa c extiende a σ (coincide con σ en las primeras d ranuras); hojas(σ) = {c ∈ C : c ⊒ σ}; P_σ = {1, …, d} es el conjunto de ranuras fijadas.

## 3. Cota superior

**Definición (instancias vivas).** Para una asignación parcial σ:

- *Modelo conjuntivo.* rotas(σ) = S ∪ ⋃_{p ∈ P_σ} R(p, σ_p) ∪ ⋃ {G : ((p, a), (q, b), G) interacción con p, q ∈ P_σ, σ_p = a, σ_q = b}, donde S son las familias siempre rotas y R(p, a) las familias que rompe la opción a de la ranura p. La instancia i (con familias F_i) está viva si F_i ∩ rotas(σ) = ∅.
- *Modelo disyuntivo.* anuladas(σ) = ⋃ {J : ((p, a), (q, b), J) interacción con p, q ∈ P_σ, σ_p = a, σ_q = b}. La instancia i (con pares L_i) está viva si i ∉ anuladas(σ) y existe (p, a) ∈ L_i tal que p ∉ P_σ (ranura sin fijar) o σ_p = a (ya satisfecha).

**Cota:** UB(σ) = |vivas(σ)| / n.

**Lema 1 (monotonía).** Si τ extiende a σ (P_σ ⊆ P_τ y τ coincide con σ en P_σ), entonces vivas(τ) ⊆ vivas(σ).

*Demostración.* Conjuntivo: cada término de la unión que define rotas(σ) aparece también en rotas(τ), porque las opciones fijadas en σ siguen fijadas igual en τ y una interacción con sus dos ranuras fijadas en σ también las tiene fijadas en τ; luego rotas(σ) ⊆ rotas(τ). Si i está viva en τ, F_i ∩ rotas(τ) = ∅, y por lo tanto F_i ∩ rotas(σ) = ∅: i está viva en σ.

Disyuntivo: por el mismo argumento, anuladas(σ) ⊆ anuladas(τ), así que si i ∉ anuladas(τ) entonces i ∉ anuladas(σ). Sea (p, a) ∈ L_i el par que hace viva a i en τ. Si p ∉ P_τ, entonces p ∉ P_σ (porque P_σ ⊆ P_τ) y el mismo par la hace viva en σ. Si p ∈ P_τ y τ_p = a: o bien p ∈ P_σ, y entonces σ_p = τ_p = a; o bien p ∉ P_σ. En los dos casos el par hace viva a i en σ. ∎

**Lema 2 (la cota es admisible y exacta en las hojas).** Para toda asignación parcial σ y toda configuración c ⊒ σ, Acc(c) ≤ UB(σ). Además, para una configuración completa c, UB(c) = Acc(c).

*Demostración.* Si c es completa, P_c son todas las ranuras. En el conjuntivo, rotas(c) es exactamente el conjunto de familias rotas por c y una instancia está viva si y solo si pasa. En el disyuntivo, ninguna ranura queda sin fijar, así que la instancia está viva si y solo si no está anulada y algún par se cumple, es decir, si y solo si pasa. Luego UB(c) = Acc(c). Para c ⊒ σ, por el Lema 1, las instancias que pasan con c (= vivas(c)) están contenidas en vivas(σ); dividiendo por n, Acc(c) ≤ UB(σ). ∎

**Observaciones.**
- La admisibilidad se apoya en la **monotonía** (fijar más ranuras solo puede hacer fallar más instancias), que vale porque las interacciones del generador solo rompen (CLAUDE.md §7.1). No se necesita que cada ranura tenga una opción limpia.
- En la reducción desde 3-SAT (modelo disyuntivo con k = 2 y sin interacciones), UB(σ) es la fracción de cláusulas que la asignación parcial no ha falsificado todavía.
- Consecuencia de los Lemas 1 y 2: UB(hijo) ≤ UB(padre), y en la raíz UB es la fracción de instancias que alguna configuración podría resolver.

## 4. Algoritmo

```
BACKTRACKING(oráculo):
  mejor ← −1; mejor_c ← nulo
  pila ← [(raíz, 1)]                     # (asignación parcial, cota del padre)
  mientras pila no esté vacía:
    (σ, u) ← sacar(pila)
    si σ es hoja (d = m):
      si u ≤ mejor: descartar σ; continuar
      p ← Acc(σ) consultando las n instancias           # n consultas
      si p > mejor: mejor ← p; mejor_c ← σ
      continuar
    b ← UB(σ)                                           # cota del nodo interno
    si b ≤ mejor: descartar el subárbol de σ; continuar
    para cada opción a de la ranura d+1, en orden decreciente de índice:
      meter(pila, (σ·a, b))                             # sale primero el índice menor
  devolver mejor_c, mejor
```

Con este orden, las hojas no descartadas se visitan en orden lexicográfico y, como solo se actualiza la mejor con una mejora estricta, el resultado es la **primera** configuración óptima en ese orden, la misma que devuelve la fuerza bruta. La variante `orden_hijos = "cota"` mete los hijos de modo que salga primero el de mayor cota; encuentra antes una buena solución y puede podar más, pero devuelve alguna configuración óptima, no necesariamente la primera.

## 5. Correctitud por invariante de ciclo

Sea V el conjunto de configuraciones ya **resueltas**: hojas evaluadas, hojas descartadas y hojas de subárboles descartados. Al comienzo de cada iteración del ciclo `mientras` se cumple:

- **(I1) Partición.** C es la unión disjunta de V y de hojas(σ) para cada (σ, u) en la pila.
- **(I2) Mejor.** mejor es la mayor precisión entre las hojas evaluadas (−1 si no hay ninguna) y mejor_c es una hoja evaluada que la alcanza.
- **(I3) Nada resuelto supera a la mejor.** Para toda c ∈ V, Acc(c) ≤ mejor.
- **(I4) La cota guardada es válida.** Para cada (σ, u) en la pila y toda c ⊒ σ, Acc(c) ≤ u.

**Inicialización.** Antes de la primera iteración, la pila tiene solo (raíz, 1) y V = ∅. (I1): hojas(raíz) = C. (I2) y (I3): no hay hojas evaluadas ni resueltas. (I4): Acc(c) ≤ 1 para toda c.

**Mantenimiento.** Se saca (σ, u) de la pila. Hay cuatro casos.

1. *Hoja descartada* (u ≤ mejor). Por (I4), Acc(σ) ≤ u ≤ mejor. Se agrega σ a V: (I1) se conserva porque σ sale de la pila y entra en V; (I3) se conserva; (I2) y (I4) no cambian.
2. *Hoja evaluada.* Se calcula p = Acc(σ) y, si p > mejor, se actualiza mejor ← p y mejor_c ← σ. σ pasa a V. (I2): mejor sigue siendo el máximo de las hojas evaluadas, ahora incluida σ. (I3): las configuraciones que ya estaban en V cumplían Acc ≤ mejor anterior ≤ mejor nuevo, y σ cumple Acc(σ) = p ≤ mejor nuevo.
3. *Nodo interno descartado* (UB(σ) ≤ mejor). Por el Lema 2, toda c ⊒ σ cumple Acc(c) ≤ UB(σ) ≤ mejor. Todas las hojas de σ pasan a V y se conserva (I3); (I1) se conserva.
4. *Nodo interno expandido.* σ sale de la pila y entran sus hijos σ·a con cota guardada b = UB(σ). (I1): hojas(σ) es la unión disjunta de las hojas de sus hijos. (I4): para toda c ⊒ σ·a, también c ⊒ σ, y por el Lema 2 Acc(c) ≤ UB(σ) = b.

**Terminación.** Cada nodo del árbol entra a la pila a lo sumo una vez (solo lo mete su padre, una vez), y en cada iteración sale uno; el árbol es finito (N nodos), así que el ciclo termina después de a lo sumo N iteraciones. Al terminar, la pila está vacía y, por (I1), V = C. Por (I3), Acc(c) ≤ mejor para toda c ∈ C, y por (I2) mejor = Acc(mejor_c). Luego mejor_c es una configuración de precisión máxima: **el algoritmo es correcto** (y la poda no descarta el óptimo).

## 6. Función de eficiencia T

**Peor caso (ninguna poda).** Se visitan todos los nodos. Cada uno de los (k^m − 1)/(k − 1) nodos internos calcula una cota (costo ≤ c·n) y cada una de las k^m hojas cuesta n consultas. Contando operaciones:

  T(m, k, n) = n · k^m + c · n · (k^m − 1)/(k − 1).

**Por recurrencia.** Sea T_d el costo de recorrer completo un subárbol cuya raíz está en el nivel d. Una hoja cuesta n; un nodo interno cuesta su cota más el de sus k hijos:

  T_m = n,  T_d = c·n + k · T_{d+1}  (0 ≤ d < m).

Desplegando: T_0 = c·n·(1 + k + … + k^{m−1}) + k^m · n = n · k^m + c · n · (k^m − 1)/(k − 1), la misma expresión.

**Notación asintótica** (definición de Θ con dos variables de las diapositivas: existen c_1, c_2 > 0 y m_0, n_0 tales que para todo m ≥ m_0 y n ≥ n_0, c_1·g ≤ T ≤ c_2·g). Con g(|C|, n) = n·|C| y k ≥ 2:

- Cota inferior: T ≥ n · k^m = n·|C|, así que c_1 = 1.
- Cota superior: (k^m − 1)/(k − 1) ≤ k^m, luego T ≤ n·|C| + c·n·|C| = (1 + c)·n·|C|, así que c_2 = 1 + c.
- Las dos valen para todo m ≥ 1 y n ≥ 1 (m_0 = n_0 = 1).

Por lo tanto, en el peor caso **T(|C|, n) = Θ(|C| · n) = Θ(n · k^m)**: exponencial en el número de ranuras m. El número de **consultas** del peor caso es exactamente n·|C|, igual que la fuerza bruta.

**El peor caso ocurre.** `generar_peor_caso_backtracking(m, k, n)` construye un caso con un solo par por instancia, siempre en la última ranura (la instancia i pasa si la última ranura vale i mod k). En todo nodo interno la última ranura está sin fijar, así que todas las instancias están vivas y UB = 1; pero ninguna configuración resuelve más de ⌈n/k⌉ instancias, y con k ≥ 2 y n ≥ 2 la mejor precisión es menor que 1. Luego UB > mejor en todos los nodos internos y no se poda nada (lo comprueba `test_peor_caso_construido_no_poda_nada`).

**Mejor caso.** Si la primera hoja visitada tiene precisión igual a la cota de la raíz (por ejemplo, Acc = 1 cuando UB(raíz) = 1), todos los demás nodos se descartan al sacarlos de la pila: se exploran 1 + m·k nodos, se calculan 1 + (m − 1)·k cotas y se evalúa una sola hoja (n consultas). Así T_mejor = n + c·n·(1 + (m − 1)·k) = Θ(n · m · k) (lo comprueba `test_mejor_caso_la_primera_hoja_es_optima`).

Como el mejor caso es Θ(n·m·k) y el peor Θ(n·|C|), y no son del mismo orden, el tiempo del algoritmo es **O(|C| · n)** y **Ω(n · m · k)**; no existe una única función f con T = Θ(f) para todas las entradas (diapositivas: el tiempo es Θ(f) si y solo si el peor caso es O(f) y el mejor es Ω(f)).

**Relación con la NP-dureza.** CONFIG-EXACTA es NP-completa (reducción desde 3-SAT). Salvo que P = NP, ningún algoritmo exacto resuelve todos los casos en tiempo polinomial en m. Por eso el backtracking conserva un peor caso exponencial: la poda ayuda en la práctica (Sección 7), pero no cambia la cota del peor caso.

## 7. Medición empírica de la poda

`scripts/fase3_backtracking.py` mide, para cada caso y cada orden de hijos, los nodos explorados por nivel, las hojas evaluadas y las consultas, y su fracción frente al peor caso (N nodos, |C| hojas, n·|C| consultas). Cada resultado se compara con la fuerza bruta. Casos: el peor caso construido, las variantes calibradas (24 y 28 %), el disyuntivo y el sin opciones limpias (los de la Fase 2b) y fórmulas 3-SAT aleatorias con 10 a 16 variables y razones cláusulas/variables de 2 a 6 (incluida 4,26). Resultados: `resultados/fase3_backtracking.json` (resumen) y `resultados/fase3_backtracking.csv` (por corrida).
