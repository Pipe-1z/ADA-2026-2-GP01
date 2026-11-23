# Algoritmo 1 explicado para la sustentación

Guía para explicar sin notas el backtracking con poda, su correctitud y su T(n). La versión formal está en `docs/derivaciones/algoritmo1_backtracking.md`. Los números medidos se citan desde `resultados/fase3_backtracking.json`, no de memoria.

## La idea en una frase

Es la fuerza bruta organizada como un árbol, con un "detector de ramas inútiles": antes de bajar por una rama, calculo cuántas instancias **todavía podrían** pasar; si ni en el mejor de los casos esa rama supera lo que ya tengo, no la recorro.

## El árbol

- Decido las ranuras una por una: primero rol, después estrategia, etc. Cada decisión es un nivel del árbol.
- En el nivel 0 no he decidido nada (1 nodo). En el nivel 1 hay k nodos (uno por opción de rol). En el nivel 2, k·k. En el nivel d, k^d.
- Las hojas (nivel m) son las configuraciones completas: k^m = |C|. Con m = 5 y k = 8 son 8^5 = 32.768.
- Solo en las hojas pregunto al modelo (n consultas por hoja). En los nodos internos solo hago cuentas.

## La cota: "¿cuántas instancias siguen vivas?"

- Una instancia está **muerta** si lo que ya fijé la hace fallar sin remedio: en el modelo del curso (conjuntivo), si alguna de sus familias ya está rota; en el de la reducción (disyuntivo), si ya fijé todas las ranuras de sus literales sin cumplir ninguno (o una interacción la anuló).
- La cota es la fracción de instancias vivas. Es **optimista**: supone que todas las vivas van a pasar.
- **Por qué no falla nunca (admisible):** fijar más ranuras nunca revive una instancia muerta. Las opciones solo rompen y las interacciones solo rompen. Entonces lo que pase al final es un subconjunto de lo que está vivo ahora: Acc(completa) ≤ cota(parcial).
- No necesito que exista una opción limpia: basta con que "romper" sea irreversible.

## Correctitud: el invariante (como en las diapositivas de insertion sort)

Pienso en tres cosas que siempre son ciertas al empezar cada vuelta del ciclo:

1. Todo el espacio C está repartido entre lo que ya resolví (V) y lo que está pendiente en la pila.
2. "mejor" es la mejor precisión de las hojas que ya evalué.
3. Nada de lo que ya resolví supera a "mejor".

- **Inicialización:** al principio la pila tiene la raíz (todo C), no he resuelto nada: se cumple trivialmente.
- **Mantenimiento:** si evalúo una hoja, actualizo "mejor" si mejora: se mantiene. Si descarto una rama, es porque su cota ≤ mejor, y la cota nunca subestima: ninguna hoja de esa rama supera a "mejor". Si expando un nodo, cambio un nodo por sus hijos, que cubren exactamente las mismas hojas.
- **Terminación:** cada nodo entra a la pila una sola vez y el árbol es finito, así que termina. Al final la pila está vacía, todo C está resuelto y nada supera a "mejor": encontré el óptimo.

## T(n): contar nodos nivel por nivel, con dos "monedas"

- Hay dos recursos que **no se pueden sumar como si costaran lo mismo**:
  - **Q = consultas al modelo** (lo caro: segundos de GPU cada una). Solo en las hojas.
  - **K = cómputo de cotas** (cuentas en CPU, baratísimas). En los nodos internos.
- Peor caso (no poda nada): visito todo.
  - Hojas: k^m = |C|, cada una n consultas → **Q = n·|C|** (igual que la fuerza bruta).
  - Nodos internos: 1 + k + k² + … + k^{m−1} = (k^m − 1)/(k − 1), cada uno una cota de costo ≈ c·n → **K = c·n·(|C| − 1)/(k − 1)**.
  - T = Q + K = n·k^m + c·n·(k^m − 1)/(k − 1). La suma solo sirve para el orden de crecimiento; para comparar algoritmos uso Q, y K lo reporto aparte.
- La misma cuenta como recurrencia: el costo de un subárbol en el nivel d es "mi cota + k veces el subárbol de abajo": T_d = c·n + k·T_{d+1}, con T_m = n. Al desplegar sale la misma suma.
- Asintótica: como (k^m − 1)/(k − 1) ≤ k^m, queda n·|C| ≤ T ≤ (1 + c)·n·|C|. Con c₁ = 1, c₂ = 1 + c y m₀ = n₀ = 1: **T = Θ(n·|C|)** en el peor caso. Es exponencial en m (|C| = k^m).
- Mejor caso: si la primera hoja ya alcanza la cota de la raíz, descarto todo lo demás: recorro una rama y miro los hermanos de cada nivel: 1 + m·k nodos, una sola hoja: Θ(n·m·k).
- Por eso digo "O(n·|C|)" y no "Θ" a secas: el mejor y el peor caso no son del mismo orden.

## ¿Ocurre de verdad el peor caso? Sí, y lo construí

- Todas las instancias dependen solo de la **última** ranura. Mientras la última ranura no esté fijada, todas están vivas y la cota vale 1.
- Pero cada configuración solo resuelve las instancias que coinciden con su última opción: a lo sumo una de cada k. La mejor es menor que 1, así que nunca cota ≤ mejor: no poda nada y recorre los N nodos.

## "Si la cota ya sabe qué rompe cada opción, ¿para qué consulta en las hojas?"

- Porque el backtracking es el **exacto de referencia para cuando el modelo de rupturas se conoce**: es la Parte 1 (oráculo exacto) y la situación de la reducción desde 3-SAT. Su análisis es el del algoritmo exacto que pide el enunciado.
- La consulta en las hojas es la operación que el enunciado cuenta (evaluar la configuración en las n instancias). La mantengo para que su costo en consultas sea comparable con el de los demás algoritmos y con el problema real.
- En el problema real **no conozco qué rompe cada opción**: solo veo la primera restricción violada de cada instancia que falla. Podría estimar un modelo de rupturas con las trazas, pero eso cuesta consultas, una familia rota puede quedar escondida detrás de otra, y las ranuras interactúan. Con un modelo estimado la cota **podría subestimar** y descartar la rama del óptimo: perdería la garantía de exactitud.
- Por eso, con el modelo real el exacto lo hago por **fuerza bruta en un subespacio pequeño** (Fase 7), donde evaluar todo sí es posible.

## ¿Dónde poda poco? (y la NP-dureza)

- En los casos disyuntivos genéricos (k = 8, tres pares por instancia), la cota casi no poda: una instancia sigue "viva" mientras cualquiera de sus pares esté en una ranura sin fijar, y eso dura hasta casi el final del árbol (ver `resultados/fase3_backtracking.json`).
- Ese es el modelo de la reducción desde 3-SAT. Es coherente con la NP-dureza: en el modelo que contiene a 3-SAT ninguna cota sencilla puede garantizar poda, porque si siempre podara lo suficiente tendríamos un algoritmo polinomial para un problema NP-completo.
- Cuidado con exagerar: en las fórmulas 3-SAT aleatorias que medí (k = 2) la cota sí podó bastante, aunque los nodos explorados siguen creciendo de forma exponencial con el número de variables. La NP-dureza habla del **peor caso**, no de cada caso.

## Preguntas de práctica

1. *¿Por qué el backtracking es exacto si no evalúa todo?* Porque solo descarta ramas cuya cota optimista no supera a la mejor, y la cota nunca subestima (Lemas 1 y 2).
2. *¿Qué pasa si la cota no fuera admisible?* Podría descartar la rama del óptimo y devolver algo peor: el invariante (3) dejaría de valer.
3. *¿Por qué no mejora el peor caso a algo polinomial?* Porque el problema es NP-difícil: si un algoritmo exacto fuera siempre polinomial en m, resolvería 3-SAT en tiempo polinomial.
4. *¿Por qué con el oráculo real no se puede usar?* Porque la cota necesita saber qué rompe cada opción; con el modelo real eso no se conoce (solo hay trazas de la primera restricción violada). Por eso el exacto se mide en el sintético y, en la Fase 7, en un subespacio pequeño del real.
5. *¿Cuántos nodos tiene el árbol con m = 5 y k = 8?* (8⁶ − 1)/7 = 37.449; hojas 32.768.
6. *¿Para qué sirve ordenar los hijos por cota?* Para encontrar antes una buena solución; con una "mejor" más alta se poda más. No cambia el peor caso.
