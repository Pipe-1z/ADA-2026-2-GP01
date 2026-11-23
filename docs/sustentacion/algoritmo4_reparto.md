# Algoritmo 4 (reparto del presupuesto) explicado para la sustentación

Versión formal: `docs/derivaciones/algoritmo4_reparto.md`. Resultados: `resultados/fase5_reparto.json`; gráficas: `figuras/fase5_reparto_*.png`.

## La pregunta

Tengo B consultas y un conjunto S de configuraciones. ¿Cómo reparto las consultas para quedarme con la mejor? Comparo tres formas, siempre con el mismo B y las mismas instancias.

## Uniforme: lo mismo para todas

- Cada configuración recibe m = B/|S| instancias y elijo la de mejor precisión observada.
- **Problema (el que menciona el enunciado):** con todo o nada y precisiones bajas, si m es pequeño muchas configuraciones buenas sacan 0 aciertos por mala suerte. Si la mejor tiene 24 % real y le doy 2 instancias, la probabilidad de que no acierte ninguna es 0,76 × 0,76 ≈ 0,58. Más de la mitad de las veces "parece 0 %".
- Es lo mismo que vi con Successive Halving con n₀ = 2: en el vecindario doble eliminó a la mejor casi la mitad de las veces, porque sus primeras rondas deciden con 2 o 4 instancias.

## Successive Halving: torneo

- Uso el mayor n₀ que cabe en B. Gasto poco en las malas y mucho en las finalistas.

## UCB1: optimismo controlado

- Cada configuración es un "brazo de tragamonedas". Jugar un brazo = evaluarlo en una instancia más.
- Primero juego cada brazo una vez. Después juego el que tiene mayor "media + √(2 ln t / n_j)": la media premia a los que van bien y el segundo término premia a los que he jugado poco (pueden estar subestimados).
- **Garantía (Auer, Cesa-Bianchi y Fischer, 2002, Teorema 1):** el regret acumulado crece como ln(jugadas): los brazos malos se juegan pocas veces.
- **Cuidado al citarla:** (1) es regret **acumulado**, no "elijo la mejor al final", que es lo que yo mido (simple regret); (2) supone recompensas independientes, y yo saco instancias sin reemplazo de 100. Por eso la uso como referencia y mido el resultado en el sintético.

## Qué digo de los resultados

- Leer las gráficas por columnas (cada variante) y por filas (probabilidad de acertar arriba, regret abajo); el eje x es cuántas consultas por configuración tengo en promedio.
- Los números exactos los tomo de `resultados/fase5_reparto.json`, no de memoria.

## Preguntas de práctica

1. *¿Por qué el uniforme falla con B pequeño?* Por el todo o nada: con pocas instancias, la precisión observada es 0 o 1/m para casi todas, y la elección es casi al azar.
2. *¿Qué garantiza UCB1?* Regret acumulado O(Σ ln n / Δ_i): juega los brazos malos un número logarítmico de veces.
3. *¿Por qué SH necesita un presupuesto mínimo?* Porque aun con n₀ = 1 tiene que evaluar a todas al menos una vez y a las sobrevivientes más veces; si B no alcanza, no es factible.
