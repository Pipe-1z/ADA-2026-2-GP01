# Algoritmo 2 (Successive Halving) explicado para la sustentación

Versión formal: `docs/derivaciones/algoritmo2_successive_halving.md`. Las cifras salen de `resultados/fase4_formula_sh.json`.

## La idea en una frase

Es un torneo por eliminación: todos juegan una ronda corta, pasa la mitad mejor, y a los que pasan les doy el doble de preguntas. Gasto poco en los malos y mucho en los buenos.

## Las rondas

- Ronda 0: todas las configuraciones con n₀ instancias. Ronda 1: la mitad, con 2·n₀. Ronda r: |S|/2^r configuraciones con n₀·2^r instancias.
- **El tope:** no tengo infinitas instancias, solo n = 100. Cuando n₀·2^r pasa de 100, uso las 100 y ya no puedo duplicar.
- Con |C| = 32.768 = 2^15 la mitad siempre es exacta: 15 rondas.

## La cuenta (sin reutilizar, como el enunciado)

- Mientras no llego al tope, cada ronda cuesta lo mismo: la mitad de configuraciones por el doble de instancias = |S|·n₀. Si hay ρ rondas así: |S|·n₀·ρ.
- Cuando llego al tope, las instancias ya no se duplican, pero las configuraciones se siguen dividiendo: n·(2^{R−ρ} + … + 2) = n·(2^{R−ρ+1} − 2). Es una serie geométrica.
- **Q = |S|·n₀·ρ + n·(2^{R−ρ+1} − 2).** Sin tope (ρ = R) queda |S|·n₀·log₂|S|, la del enunciado.
- Ejemplo del proyecto (n₀ = 1, n = 100): las rondas usan 1, 2, 4, 8, 16, 32, 64 instancias (7 rondas sin tope) y desde la octava, 100. Q = 32.768·7 + 100·510 = 229.376 + 51.000 = 280.376.

## Con caché cuesta la mitad

Las muestras están anidadas: las 4 instancias de la ronda 2 incluyen las 2 de la ronda 1. Con caché solo pago las nuevas. Cada configuración paga hasta la última ronda que jugó, y como la mitad se va en cada ronda, sale más o menos la mitad: 140.288 en el ejemplo.

## Los errores del enunciado (para explicarlos en voz alta)

1. Dice |C| = 144 y calcula con 3840.
2. 3840·2·log₂ 3840 = 91.444,92: el 91.444 está truncado.
3. 3840 no es potencia de 2: las mitades no son exactas y el algoritmo real redondea hacia arriba (12 rondas). La cuenta exacta sin tope da 93.696.
4. Olvida el tope: con n₀ = 2, en la ronda 7 pediría 256 instancias y solo hay 150 (o 100). Con tope cuesta 62.610 (n = 150) o 57.980 (n = 100). Entonces **sí depende de n**.
5. "O(|C| log |C|) independiente de n" solo vale sin tope; con tope es Θ(|C|·n₀·min(log₂|C|, log₂(n/n₀))).

## ¿Puede eliminar a la mejor? Sí, en las rondas cortas

- Con 1 o 2 instancias, una configuración buena puede tener mala suerte (todo o nada) y perder contra una peor.
- Cuenta: la probabilidad de que una configuración j le gane a la mejor con n_r instancias es a lo sumo exp(−n_r·Δ²/2), con Δ la diferencia real de precisión (Hoeffding). La mejor solo sale si al menos la mitad le gana (Markov), y sumo sobre las rondas (unión). Es la idea de Karnin, Koren y Somekh (2013).
- Cuando la ronda ya usa las 100 instancias, la medición es exacta y no hay riesgo.
- Esa cota es pesimista: muchas veces da más que 1 y no dice nada. Por eso también medí la frecuencia real en el sintético, con 200 sorteos distintos de las instancias.

## Dos ranuras con filtro por SH

- El Algoritmo 3 se atasca cuando hace falta cambiar dos ranuras a la vez.
- Desde donde se atascó, hay 10 pares de ranuras × 7 × 7 opciones = 490 configuraciones a dos cambios de distancia.
- En vez de evaluar las 490 con 100 instancias (49.000 consultas), las paso por un torneo de SH: casi todas se descartan con pocas instancias y solo las finalistas llegan a las 100.

## Preguntas de práctica

1. *¿Por qué SH es divide y vencerás?* Porque en cada ronda divide el conjunto de candidatos a la mitad y concentra el esfuerzo en la mitad que queda.
2. *¿De dónde sale el log₂|C|?* Del número de rondas: cada ronda divide entre 2 hasta que queda 1.
3. *¿Por qué cada ronda cuesta lo mismo sin tope?* Mitad de configuraciones por doble de instancias.
4. *¿Qué cambia el tope?* Las últimas rondas ya no duplican instancias: cuestan menos, y el costo depende de n.
5. *¿Cuándo es exacto?* Si todas las rondas usan toda la población (n₀ ≥ n), siempre sobrevive una óptima (invariante).
