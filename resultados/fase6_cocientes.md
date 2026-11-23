# Fase 6: tablas de cocientes observado/teórico

Generado por `scripts/fase6_figuras.py` desde `resultados/fase6_validacion.json`; no se edita a mano.
Como en las presentaciones del curso: si T = Θ(g), el cociente T/g queda entre dos constantes c₁ y c₂.
El tiempo es de CPU con el oráculo sintético, no de GPU.

## Fuerza bruta: Q (consultas) frente a n

Modelo: |C|·n con |C| = 4^4; coeficientes 1. Pendiente log-log: observada 1.000, ajuste 1.000, término dominante 1.000.

| tamaño | observado (media) | teórico ajustado | observado / ajustado | término dominante g | observado / g |
|---|---|---|---|---|---|
| 25 | 6400 | 6400 | 1.0000 | 6400 | 1 |
| 50 | 1.28e+04 | 1.28e+04 | 1.0000 | 1.28e+04 | 1 |
| 100 | 2.56e+04 | 2.56e+04 | 1.0000 | 2.56e+04 | 1 |
| 200 | 5.12e+04 | 5.12e+04 | 1.0000 | 5.12e+04 | 1 |
| 400 | 1.024e+05 | 1.024e+05 | 1.0000 | 1.024e+05 | 1 |
| 800 | 2.048e+05 | 2.048e+05 | 1.0000 | 2.048e+05 | 1 |

c₁ = 1.0000, c₂ = 1.0000 (observado / ajustado).

## Fuerza bruta: Tiempo de CPU (s) frente a n

Modelo: a·|C| (por evaluación) + b·|C|·n (por consulta); coeficientes 0, 5.675e-07. Pendiente log-log: observada 0.942, ajuste 1.000, término dominante 1.000.

| tamaño | observado (media) | teórico ajustado | observado / ajustado | término dominante g | observado / g |
|---|---|---|---|---|---|
| 25 | 0.004483 | 0.003632 | 1.2344 | 6400 | 7.005e-07 |
| 50 | 0.007881 | 0.007264 | 1.0850 | 1.28e+04 | 6.157e-07 |
| 100 | 0.01426 | 0.01453 | 0.9813 | 2.56e+04 | 5.569e-07 |
| 200 | 0.02726 | 0.02906 | 0.9382 | 5.12e+04 | 5.324e-07 |
| 400 | 0.05555 | 0.05811 | 0.9560 | 1.024e+05 | 5.425e-07 |
| 800 | 0.1179 | 0.1162 | 1.0146 | 2.048e+05 | 5.758e-07 |

c₁ = 0.9382, c₂ = 1.2344 (observado / ajustado).

## Fuerza bruta: Q (consultas) frente a |C| = 4^m

Modelo: |C|·n con n = 50; coeficientes 1. Pendiente log-log: observada 1.000, ajuste 1.000, término dominante 1.000.

| tamaño | observado (media) | teórico ajustado | observado / ajustado | término dominante g | observado / g |
|---|---|---|---|---|---|
| 16 | 800 | 800 | 1.0000 | 800 | 1 |
| 64 | 3200 | 3200 | 1.0000 | 3200 | 1 |
| 256 | 1.28e+04 | 1.28e+04 | 1.0000 | 1.28e+04 | 1 |
| 1024 | 5.12e+04 | 5.12e+04 | 1.0000 | 5.12e+04 | 1 |
| 4096 | 2.048e+05 | 2.048e+05 | 1.0000 | 2.048e+05 | 1 |

c₁ = 1.0000, c₂ = 1.0000 (observado / ajustado).

## Fuerza bruta: Tiempo de CPU (s) frente a |C| = 4^m

Modelo: ∝ |C|·n; coeficientes 7.314e-07. Pendiente log-log: observada 1.052, ajuste 1.000, término dominante 1.000.

| tamaño | observado (media) | teórico ajustado | observado / ajustado | término dominante g | observado / g |
|---|---|---|---|---|---|
| 16 | 0.0004588 | 0.0005851 | 0.7841 | 800 | 5.735e-07 |
| 64 | 0.001881 | 0.00234 | 0.8036 | 3200 | 5.877e-07 |
| 256 | 0.008451 | 0.009362 | 0.9027 | 1.28e+04 | 6.602e-07 |
| 1024 | 0.03829 | 0.03745 | 1.0226 | 5.12e+04 | 7.479e-07 |
| 4096 | 0.1496 | 0.1498 | 0.9990 | 2.048e+05 | 7.307e-07 |

c₁ = 0.7841, c₂ = 1.0226 (observado / ajustado).

## Algoritmo 1: backtracking (peor caso construido): Q (consultas) frente a n

Modelo: |C|·n; coeficientes 1. Pendiente log-log: observada 1.000, ajuste 1.000, término dominante 1.000.

| tamaño | observado (media) | teórico ajustado | observado / ajustado | término dominante g | observado / g |
|---|---|---|---|---|---|
| 25 | 6400 | 6400 | 1.0000 | 6400 | 1 |
| 50 | 1.28e+04 | 1.28e+04 | 1.0000 | 1.28e+04 | 1 |
| 100 | 2.56e+04 | 2.56e+04 | 1.0000 | 2.56e+04 | 1 |
| 200 | 5.12e+04 | 5.12e+04 | 1.0000 | 5.12e+04 | 1 |
| 400 | 1.024e+05 | 1.024e+05 | 1.0000 | 1.024e+05 | 1 |
| 800 | 2.048e+05 | 2.048e+05 | 1.0000 | 2.048e+05 | 1 |

c₁ = 1.0000, c₂ = 1.0000 (observado / ajustado).

## Algoritmo 1: backtracking (peor caso construido): K (cotas calculadas) frente a n

Modelo: (|C| − 1)/(k − 1); coeficientes 1. Pendiente log-log: observada 0.000, ajuste 0.000, término dominante 0.000.

| tamaño | observado (media) | teórico ajustado | observado / ajustado | término dominante g | observado / g |
|---|---|---|---|---|---|
| 25 | 85 | 85 | 1.0000 | 85 | 1 |
| 50 | 85 | 85 | 1.0000 | 85 | 1 |
| 100 | 85 | 85 | 1.0000 | 85 | 1 |
| 200 | 85 | 85 | 1.0000 | 85 | 1 |
| 400 | 85 | 85 | 1.0000 | 85 | 1 |
| 800 | 85 | 85 | 1.0000 | 85 | 1 |

c₁ = 1.0000, c₂ = 1.0000 (observado / ajustado).

## Algoritmo 1: backtracking (peor caso construido): Tiempo de CPU (s) frente a n

Modelo: a·(hojas + cotas) + b·(hojas + cotas)·n; coeficientes 1.459e-06, 6.696e-07. Pendiente log-log: observada 0.962, ajuste 0.978, término dominante 1.000.

| tamaño | observado (media) | teórico ajustado | observado / ajustado | término dominante g | observado / g |
|---|---|---|---|---|---|
| 25 | 0.006927 | 0.006205 | 1.1162 | 8525 | 8.125e-07 |
| 50 | 0.01139 | 0.01191 | 0.9564 | 1.705e+04 | 6.683e-07 |
| 100 | 0.02313 | 0.02333 | 0.9913 | 3.41e+04 | 6.782e-07 |
| 200 | 0.04499 | 0.04616 | 0.9746 | 6.82e+04 | 6.597e-07 |
| 400 | 0.09351 | 0.09183 | 1.0184 | 1.364e+05 | 6.856e-07 |
| 800 | 0.1826 | 0.1832 | 0.9972 | 2.728e+05 | 6.695e-07 |

c₁ = 0.9564, c₂ = 1.1162 (observado / ajustado).

## Algoritmo 1: backtracking (peor caso construido): Q (consultas) frente a |C| = 4^m

Modelo: |C|·n; coeficientes 1. Pendiente log-log: observada 1.000, ajuste 1.000, término dominante 1.000.

| tamaño | observado (media) | teórico ajustado | observado / ajustado | término dominante g | observado / g |
|---|---|---|---|---|---|
| 16 | 800 | 800 | 1.0000 | 800 | 1 |
| 64 | 3200 | 3200 | 1.0000 | 3200 | 1 |
| 256 | 1.28e+04 | 1.28e+04 | 1.0000 | 1.28e+04 | 1 |
| 1024 | 5.12e+04 | 5.12e+04 | 1.0000 | 5.12e+04 | 1 |
| 4096 | 2.048e+05 | 2.048e+05 | 1.0000 | 2.048e+05 | 1 |
| 2e4 | 8.192e+05 | 8.192e+05 | 1.0000 | 8.192e+05 | 1 |

c₁ = 1.0000, c₂ = 1.0000 (observado / ajustado).

## Algoritmo 1: backtracking (peor caso construido): K (cotas calculadas) frente a |C| = 4^m

Modelo: (|C| − 1)/(k − 1); coeficientes 1. Pendiente log-log: observada 1.008, ajuste 1.008, término dominante 1.008.

| tamaño | observado (media) | teórico ajustado | observado / ajustado | término dominante g | observado / g |
|---|---|---|---|---|---|
| 16 | 5 | 5 | 1.0000 | 5 | 1 |
| 64 | 21 | 21 | 1.0000 | 21 | 1 |
| 256 | 85 | 85 | 1.0000 | 85 | 1 |
| 1024 | 341 | 341 | 1.0000 | 341 | 1 |
| 4096 | 1365 | 1365 | 1.0000 | 1365 | 1 |
| 2e4 | 5461 | 5461 | 1.0000 | 5461 | 1 |

c₁ = 1.0000, c₂ = 1.0000 (observado / ajustado).

## Algoritmo 1: backtracking (peor caso construido): Tiempo de CPU (s) frente a |C| = 4^m

Modelo: ∝ |C|·n; coeficientes 1.272e-06. Pendiente log-log: observada 1.056, ajuste 1.000, término dominante 1.000.

| tamaño | observado (media) | teórico ajustado | observado / ajustado | término dominante g | observado / g |
|---|---|---|---|---|---|
| 16 | 0.0006603 | 0.001018 | 0.6487 | 800 | 8.253e-07 |
| 64 | 0.002941 | 0.004071 | 0.7224 | 3200 | 9.191e-07 |
| 256 | 0.01304 | 0.01629 | 0.8009 | 1.28e+04 | 1.019e-06 |
| 1024 | 0.0511 | 0.06514 | 0.7845 | 5.12e+04 | 9.981e-07 |
| 4096 | 0.2245 | 0.2606 | 0.8614 | 2.048e+05 | 1.096e-06 |
| 2e4 | 1.052 | 1.042 | 1.0096 | 8.192e+05 | 1.284e-06 |

c₁ = 0.6487, c₂ = 1.0096 (observado / ajustado).

## Algoritmo 1: backtracking en 3-SAT aleatorio (razón 4,26) frente al peor caso: Q (consultas) frente a |C| = 2^v (razón 4,26)

Modelo: peor caso |C|·n; coeficientes 1. Pendiente log-log: observada 0.363, ajuste 1.098, término dominante 1.098.

| tamaño | observado (media) | teórico ajustado | observado / ajustado | término dominante g | observado / g |
|---|---|---|---|---|---|
| 1024 | 731 | 4.403e+04 | 0.0166 | 4.403e+04 | 0.0166 |
| 4096 | 1040 | 2.089e+05 | 0.0050 | 2.089e+05 | 0.00498 |
| 2e4 | 2100 | 9.83e+05 | 0.0021 | 9.83e+05 | 0.002136 |
| 7e4 | 3808 | 4.456e+06 | 0.0009 | 4.456e+06 | 0.0008545 |
| 3e5 | 6961 | 2.019e+07 | 0.0003 | 2.019e+07 | 0.0003448 |
| 1e6 | 7004 | 8.913e+07 | 0.0001 | 8.913e+07 | 7.858e-05 |

c₁ = 0.0001, c₂ = 0.0166 (observado / ajustado).

## Algoritmo 1: backtracking en 3-SAT aleatorio (razón 4,26) frente al peor caso: K (cotas calculadas) frente a |C| = 2^v (razón 4,26)

Modelo: peor caso (|C| − 1)/(k − 1); coeficientes 1. Pendiente log-log: observada 0.477, ajuste 1.000, término dominante 1.000.

| tamaño | observado (media) | teórico ajustado | observado / ajustado | término dominante g | observado / g |
|---|---|---|---|---|---|
| 1024 | 143.8 | 1023 | 0.1406 | 1023 | 0.1406 |
| 4096 | 309.4 | 4095 | 0.0756 | 4095 | 0.07556 |
| 2e4 | 823 | 1.638e+04 | 0.0502 | 1.638e+04 | 0.05023 |
| 7e4 | 1029 | 6.554e+04 | 0.0157 | 6.554e+04 | 0.01571 |
| 3e5 | 5806 | 2.621e+05 | 0.0221 | 2.621e+05 | 0.02215 |
| 1e6 | 2423 | 1.049e+06 | 0.0023 | 1.049e+06 | 0.00231 |

c₁ = 0.0023, c₂ = 0.1406 (observado / ajustado).

## Algoritmo 1: backtracking en 3-SAT aleatorio (razón 4,26) frente al peor caso: Tiempo de CPU (s) frente a |C| = 2^v (razón 4,26)

Modelo: peor caso ∝ |C|·n; coeficientes 1.272e-06. Pendiente log-log: observada 0.552, ajuste 1.098, término dominante 1.098.

| tamaño | observado (media) | teórico ajustado | observado / ajustado | término dominante g | observado / g |
|---|---|---|---|---|---|
| 1024 | 0.003621 | 0.05602 | 0.0646 | 4.403e+04 | 8.223e-08 |
| 4096 | 0.008419 | 0.2658 | 0.0317 | 2.089e+05 | 4.03e-08 |
| 2e4 | 0.02505 | 1.251 | 0.0200 | 9.83e+05 | 2.548e-08 |
| 7e4 | 0.03638 | 5.67 | 0.0064 | 4.456e+06 | 8.163e-09 |
| 3e5 | 0.2141 | 25.68 | 0.0083 | 2.019e+07 | 1.06e-08 |
| 1e6 | 0.1017 | 113.4 | 0.0009 | 8.913e+07 | 1.142e-09 |

c₁ = 0.0009, c₂ = 0.0646 (observado / ajustado).

## Algoritmo 2: Successive Halving (n₀ = 1): Q sin reutilizar frente a |S| = 2^R

Modelo: fórmula exacta sin reutilizar; coeficientes 1. Pendiente log-log: observada 1.077, ajuste 1.077, término dominante 1.077.

| tamaño | observado (media) | teórico ajustado | observado / ajustado | término dominante g | observado / g |
|---|---|---|---|---|---|
| 64 | 384 | 384 | 1.0000 | 384 | 1 |
| 128 | 896 | 896 | 1.0000 | 896 | 1 |
| 256 | 1992 | 1992 | 1.0000 | 1992 | 1 |
| 512 | 4184 | 4184 | 1.0000 | 4184 | 1 |
| 1024 | 8568 | 8568 | 1.0000 | 8568 | 1 |
| 2048 | 1.734e+04 | 1.734e+04 | 1.0000 | 1.734e+04 | 1 |
| 4096 | 3.487e+04 | 3.487e+04 | 1.0000 | 3.487e+04 | 1 |

c₁ = 1.0000, c₂ = 1.0000 (observado / ajustado).

## Algoritmo 2: Successive Halving (n₀ = 1): Q con reutilización frente a |S| = 2^R

Modelo: fórmula exacta con reutilización; coeficientes 1. Pendiente log-log: observada 1.038, ajuste 1.038, término dominante 1.038.

| tamaño | observado (media) | teórico ajustado | observado / ajustado | término dominante g | observado / g |
|---|---|---|---|---|---|
| 64 | 224 | 224 | 1.0000 | 224 | 1 |
| 128 | 512 | 512 | 1.0000 | 512 | 1 |
| 256 | 1096 | 1096 | 1.0000 | 1096 | 1 |
| 512 | 2192 | 2192 | 1.0000 | 2192 | 1 |
| 1024 | 4384 | 4384 | 1.0000 | 4384 | 1 |
| 2048 | 8768 | 8768 | 1.0000 | 8768 | 1 |
| 4096 | 1.754e+04 | 1.754e+04 | 1.0000 | 1.754e+04 | 1 |

c₁ = 1.0000, c₂ = 1.0000 (observado / ajustado).

## Algoritmo 2: Successive Halving (n₀ = 1): Tiempo de CPU (s) frente a |S| = 2^R

Modelo: a·Σ|S_r| (evaluaciones) + b·Q_sin; coeficientes 0, 1.51e-06. Pendiente log-log: observada 1.024, ajuste 1.077, término dominante 1.077.

| tamaño | observado (media) | teórico ajustado | observado / ajustado | término dominante g | observado / g |
|---|---|---|---|---|---|
| 64 | 0.0007537 | 0.0005798 | 1.2998 | 384 | 1.963e-06 |
| 128 | 0.001487 | 0.001353 | 1.0994 | 896 | 1.66e-06 |
| 256 | 0.003078 | 0.003008 | 1.0234 | 1992 | 1.545e-06 |
| 512 | 0.00594 | 0.006318 | 0.9403 | 4184 | 1.42e-06 |
| 1024 | 0.01247 | 0.01294 | 0.9636 | 8568 | 1.455e-06 |
| 2048 | 0.02617 | 0.02618 | 0.9999 | 1.734e+04 | 1.51e-06 |
| 4096 | 0.05281 | 0.05266 | 1.0029 | 3.487e+04 | 1.514e-06 |

c₁ = 0.9403, c₂ = 1.2998 (observado / ajustado).

## Algoritmo 2: Successive Halving (n₀ = 1): Q sin reutilizar frente a n

Modelo: fórmula exacta sin reutilizar; coeficientes 1. Pendiente log-log: observada 0.126, ajuste 0.126, término dominante 0.126.

| tamaño | observado (media) | teórico ajustado | observado / ajustado | término dominante g | observado / g |
|---|---|---|---|---|---|
| 25 | 6670 | 6670 | 1.0000 | 6670 | 1 |
| 50 | 7644 | 7644 | 1.0000 | 7644 | 1 |
| 100 | 8568 | 8568 | 1.0000 | 8568 | 1 |
| 200 | 9392 | 9392 | 1.0000 | 9392 | 1 |
| 400 | 1.002e+04 | 1.002e+04 | 1.0000 | 1.002e+04 | 1 |
| 800 | 1.024e+04 | 1.024e+04 | 1.0000 | 1.024e+04 | 1 |

c₁ = 1.0000, c₂ = 1.0000 (observado / ajustado).

## Algoritmo 2: Successive Halving (n₀ = 1): Q con reutilización frente a n

Modelo: fórmula exacta con reutilización; coeficientes 1. Pendiente log-log: observada 0.152, ajuste 0.152, término dominante 0.152.

| tamaño | observado (media) | teórico ajustado | observado / ajustado | término dominante g | observado / g |
|---|---|---|---|---|---|
| 25 | 3360 | 3360 | 1.0000 | 3360 | 1 |
| 50 | 3872 | 3872 | 1.0000 | 3872 | 1 |
| 100 | 4384 | 4384 | 1.0000 | 4384 | 1 |
| 200 | 4896 | 4896 | 1.0000 | 4896 | 1 |
| 400 | 5408 | 5408 | 1.0000 | 5408 | 1 |
| 800 | 5632 | 5632 | 1.0000 | 5632 | 1 |

c₁ = 1.0000, c₂ = 1.0000 (observado / ajustado).

## Algoritmo 2: Successive Halving (n₀ = 1): Tiempo de CPU (s) frente a n

Modelo: a·Σ|S_r| (evaluaciones) + b·Q_sin; coeficientes 3.495e-06, 6.212e-07. Pendiente log-log: observada 0.054, ajuste 0.053, término dominante 0.126.

| tamaño | observado (media) | teórico ajustado | observado / ajustado | término dominante g | observado / g |
|---|---|---|---|---|---|
| 25 | 0.01129 | 0.0113 | 0.9989 | 6670 | 1.692e-06 |
| 50 | 0.01216 | 0.01191 | 1.0211 | 7644 | 1.59e-06 |
| 100 | 0.01222 | 0.01248 | 0.9795 | 8568 | 1.427e-06 |
| 200 | 0.01276 | 0.01299 | 0.9819 | 9392 | 1.358e-06 |
| 400 | 0.01347 | 0.01338 | 1.0064 | 1.002e+04 | 1.344e-06 |
| 800 | 0.01368 | 0.01352 | 1.0123 | 1.024e+04 | 1.336e-06 |

c₁ = 0.9795, c₂ = 1.0211 (observado / ajustado).

## Algoritmo 3: ascenso por coordenadas (cota teórica): Q (consultas) frente a n

Modelo: cota n·[1 + I·Σ(k_p − 1)]; coeficientes 0.4495. Pendiente log-log: observada 0.991, ajuste 1.000, término dominante 1.000.

| tamaño | observado (media) | teórico ajustado | observado / ajustado | término dominante g | observado / g |
|---|---|---|---|---|---|
| 25 | 1240 | 1191 | 1.0409 | 2650 | 0.4679 |
| 50 | 2400 | 2382 | 1.0074 | 5300 | 0.4528 |
| 100 | 4760 | 4765 | 0.9990 | 1.06e+04 | 0.4491 |
| 200 | 9880 | 9530 | 1.0367 | 2.12e+04 | 0.466 |
| 400 | 1.896e+04 | 1.906e+04 | 0.9948 | 4.24e+04 | 0.4472 |
| 800 | 3.808e+04 | 3.812e+04 | 0.9990 | 8.48e+04 | 0.4491 |

c₁ = 0.9948, c₂ = 1.0409 (observado / ajustado).

## Algoritmo 3: ascenso por coordenadas (cota teórica): Tiempo de CPU (s) frente a n

Modelo: a·(evaluaciones) + b·cota; coeficientes 6.987e-06, 3.132e-07. Pendiente log-log: observada 0.836, ajuste 0.831, término dominante 1.000.

| tamaño | observado (media) | teórico ajustado | observado / ajustado | término dominante g | observado / g |
|---|---|---|---|---|---|
| 25 | 0.001572 | 0.001571 | 1.0011 | 2650 | 5.933e-07 |
| 50 | 0.002363 | 0.002401 | 0.9843 | 5300 | 4.459e-07 |
| 100 | 0.003816 | 0.004061 | 0.9396 | 1.06e+04 | 3.6e-07 |
| 200 | 0.007928 | 0.007381 | 1.0741 | 2.12e+04 | 3.74e-07 |
| 400 | 0.0137 | 0.01402 | 0.9769 | 4.24e+04 | 3.231e-07 |
| 800 | 0.02736 | 0.0273 | 1.0021 | 8.48e+04 | 3.226e-07 |

c₁ = 0.9396, c₂ = 1.0741 (observado / ajustado).

## Algoritmo 3: ascenso por coordenadas (cota teórica): Q (consultas) frente a m

Modelo: cota n·[1 + I·Σ(k_p − 1)]; coeficientes 0.515. Pendiente log-log: observada 1.182, ajuste 0.990, término dominante 0.990.

| tamaño | observado (media) | teórico ajustado | observado / ajustado | término dominante g | observado / g |
|---|---|---|---|---|---|
| 3 | 3000 | 3296 | 0.9102 | 6400 | 0.4688 |
| 4 | 3900 | 4378 | 0.8909 | 8500 | 0.4588 |
| 5 | 4760 | 5459 | 0.8719 | 1.06e+04 | 0.4491 |
| 6 | 6300 | 6541 | 0.9632 | 1.27e+04 | 0.4961 |
| 7 | 7320 | 7622 | 0.9604 | 1.48e+04 | 0.4946 |
| 8 | 9940 | 8704 | 1.1420 | 1.69e+04 | 0.5882 |

c₁ = 0.8719, c₂ = 1.1420 (observado / ajustado).

## Algoritmo 3: ascenso por coordenadas (cota teórica): Tiempo de CPU (s) frente a m

Modelo: ∝ cota; coeficientes 4.518e-07. Pendiente log-log: observada 1.208, ajuste 0.990, término dominante 0.990.

| tamaño | observado (media) | teórico ajustado | observado / ajustado | término dominante g | observado / g |
|---|---|---|---|---|---|
| 3 | 0.00272 | 0.002892 | 0.9405 | 6400 | 4.249e-07 |
| 4 | 0.003154 | 0.003841 | 0.8213 | 8500 | 3.711e-07 |
| 5 | 0.003991 | 0.004789 | 0.8334 | 1.06e+04 | 3.765e-07 |
| 6 | 0.005449 | 0.005738 | 0.9496 | 1.27e+04 | 4.29e-07 |
| 7 | 0.00649 | 0.006687 | 0.9705 | 1.48e+04 | 4.385e-07 |
| 8 | 0.008937 | 0.007636 | 1.1704 | 1.69e+04 | 5.288e-07 |

c₁ = 0.8213, c₂ = 1.1704 (observado / ajustado).

## Algoritmo 4: reparto uniforme: Q (consultas) frente a |S|

Modelo: |S|·m con m = 10; coeficientes 1. Pendiente log-log: observada 1.000, ajuste 1.000, término dominante 1.000.

| tamaño | observado (media) | teórico ajustado | observado / ajustado | término dominante g | observado / g |
|---|---|---|---|---|---|
| 32 | 320 | 320 | 1.0000 | 320 | 1 |
| 64 | 640 | 640 | 1.0000 | 640 | 1 |
| 128 | 1280 | 1280 | 1.0000 | 1280 | 1 |
| 256 | 2560 | 2560 | 1.0000 | 2560 | 1 |
| 512 | 5120 | 5120 | 1.0000 | 5120 | 1 |
| 1024 | 1.024e+04 | 1.024e+04 | 1.0000 | 1.024e+04 | 1 |

c₁ = 1.0000, c₂ = 1.0000 (observado / ajustado).

## Algoritmo 4: reparto uniforme: Tiempo de CPU (s) frente a |S|

Modelo: ∝ |S|·m; coeficientes 9.159e-07. Pendiente log-log: observada 0.983, ajuste 1.000, término dominante 1.000.

| tamaño | observado (media) | teórico ajustado | observado / ajustado | término dominante g | observado / g |
|---|---|---|---|---|---|
| 32 | 0.0003303 | 0.0002931 | 1.1270 | 320 | 1.032e-06 |
| 64 | 0.0005483 | 0.0005862 | 0.9355 | 640 | 8.568e-07 |
| 128 | 0.001163 | 0.001172 | 0.9918 | 1280 | 9.084e-07 |
| 256 | 0.00228 | 0.002345 | 0.9724 | 2560 | 8.906e-07 |
| 512 | 0.004704 | 0.004689 | 1.0031 | 5120 | 9.188e-07 |
| 1024 | 0.00939 | 0.009379 | 1.0012 | 1.024e+04 | 9.17e-07 |

c₁ = 0.9355, c₂ = 1.1270 (observado / ajustado).

## Algoritmo 4: reparto uniforme: Q (consultas) frente a m

Modelo: |S|·m con |S| = 128; coeficientes 1. Pendiente log-log: observada 1.000, ajuste 1.000, término dominante 1.000.

| tamaño | observado (media) | teórico ajustado | observado / ajustado | término dominante g | observado / g |
|---|---|---|---|---|---|
| 5 | 640 | 640 | 1.0000 | 640 | 1 |
| 10 | 1280 | 1280 | 1.0000 | 1280 | 1 |
| 20 | 2560 | 2560 | 1.0000 | 2560 | 1 |
| 40 | 5120 | 5120 | 1.0000 | 5120 | 1 |
| 80 | 1.024e+04 | 1.024e+04 | 1.0000 | 1.024e+04 | 1 |

c₁ = 1.0000, c₂ = 1.0000 (observado / ajustado).

## Algoritmo 4: reparto uniforme: Tiempo de CPU (s) frente a m

Modelo: a·|S| (evaluaciones) + b·|S|·m; coeficientes 3.074e-06, 5.22e-07. Pendiente log-log: observada 0.699, ajuste 0.749, término dominante 1.000.

| tamaño | observado (media) | teórico ajustado | observado / ajustado | término dominante g | observado / g |
|---|---|---|---|---|---|
| 5 | 0.0008228 | 0.0007275 | 1.1311 | 640 | 1.286e-06 |
| 10 | 0.00114 | 0.001062 | 1.0738 | 1280 | 8.906e-07 |
| 20 | 0.001637 | 0.00173 | 0.9463 | 2560 | 6.394e-07 |
| 40 | 0.002889 | 0.003066 | 0.9424 | 5120 | 5.643e-07 |
| 80 | 0.005834 | 0.005739 | 1.0167 | 1.024e+04 | 5.698e-07 |

c₁ = 0.9424, c₂ = 1.1311 (observado / ajustado).

## Algoritmo 4: UCB1: Q (consultas) frente a B/|S| (|S| = 128)

Modelo: B; coeficientes 1. Pendiente log-log: observada 1.000, ajuste 1.000, término dominante 1.000.

| tamaño | observado (media) | teórico ajustado | observado / ajustado | término dominante g | observado / g |
|---|---|---|---|---|---|
| 256 | 256 | 256 | 1.0000 | 256 | 1 |
| 512 | 512 | 512 | 1.0000 | 512 | 1 |
| 1024 | 1024 | 1024 | 1.0000 | 1024 | 1 |
| 2048 | 2048 | 2048 | 1.0000 | 2048 | 1 |
| 4096 | 4096 | 4096 | 1.0000 | 4096 | 1 |
| 8192 | 8192 | 8192 | 1.0000 | 8192 | 1 |

c₁ = 1.0000, c₂ = 1.0000 (observado / ajustado).

## Algoritmo 4: UCB1: Tiempo de CPU (s) frente a B/|S| (|S| = 128)

Modelo: a (fijo por corrida) + b·B (cada jugada: una consulta y el índice de los |S| brazos); coeficientes 0, 9.995e-06. Pendiente log-log: observada 1.067, ajuste 1.000, término dominante 1.000.

| tamaño | observado (media) | teórico ajustado | observado / ajustado | término dominante g | observado / g |
|---|---|---|---|---|---|
| 256 | 0.002039 | 0.002559 | 0.7970 | 256 | 7.966e-06 |
| 512 | 0.004396 | 0.005118 | 0.8590 | 512 | 8.586e-06 |
| 1024 | 0.009302 | 0.01024 | 0.9088 | 1024 | 9.084e-06 |
| 2048 | 0.01919 | 0.02047 | 0.9375 | 2048 | 9.371e-06 |
| 4096 | 0.04022 | 0.04094 | 0.9825 | 4096 | 9.82e-06 |
| 8192 | 0.08274 | 0.08188 | 1.0105 | 8192 | 1.01e-05 |

c₁ = 0.7970, c₂ = 1.0105 (observado / ajustado).

## Algoritmo 4: UCB1: Q (consultas) frente a |S| (B = 16·|S|)

Modelo: B = 16·|S|; coeficientes 1. Pendiente log-log: observada 1.000, ajuste 1.000, término dominante 1.000.

| tamaño | observado (media) | teórico ajustado | observado / ajustado | término dominante g | observado / g |
|---|---|---|---|---|---|
| 32 | 512 | 512 | 1.0000 | 512 | 1 |
| 64 | 1024 | 1024 | 1.0000 | 1024 | 1 |
| 128 | 2048 | 2048 | 1.0000 | 2048 | 1 |
| 256 | 4096 | 4096 | 1.0000 | 4096 | 1 |
| 512 | 8192 | 8192 | 1.0000 | 8192 | 1 |
| 1024 | 1.638e+04 | 1.638e+04 | 1.0000 | 1.638e+04 | 1 |

c₁ = 1.0000, c₂ = 1.0000 (observado / ajustado).

## Algoritmo 4: UCB1: Tiempo de CPU (s) frente a |S| (B = 16·|S|)

Modelo: a·B (consulta por jugada) + b·B·|S| (índice), B = 16·|S|; coeficientes 9.387e-06, 2.431e-09. Pendiente log-log: observada 1.081, ajuste 1.061, término dominante 2.000.

| tamaño | observado (media) | teórico ajustado | observado / ajustado | término dominante g | observado / g |
|---|---|---|---|---|---|
| 32 | 0.004565 | 0.004846 | 0.9421 | 1.638e+04 | 2.786e-07 |
| 64 | 0.009357 | 0.009771 | 0.9576 | 6.554e+04 | 1.428e-07 |
| 128 | 0.01904 | 0.01986 | 0.9586 | 2.621e+05 | 7.263e-08 |
| 256 | 0.04023 | 0.041 | 0.9812 | 1.049e+06 | 3.836e-08 |
| 512 | 0.08816 | 0.08709 | 1.0123 | 4.194e+06 | 2.102e-08 |
| 1024 | 0.1944 | 0.1946 | 0.9990 | 1.678e+07 | 1.159e-08 |

c₁ = 0.9421, c₂ = 1.0123 (observado / ajustado).
