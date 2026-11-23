"""Comparación de lo observado contra una función de eficiencia teórica g (Fase 6).

Sigue la forma de las presentaciones del curso: si T(x) = Θ(g(x)), el cociente
T(x)/g(x) queda acotado entre dos constantes c₁ y c₂ para x grande; en escala
log-log, la pendiente de T frente a x tiende a la de g.

- ``ajustar_constante``: c que minimiza Σ (T_i − c·g_i)² (mínimos cuadrados por el origen).
- ``pendiente_loglog``: pendiente de la recta de mínimos cuadrados de log T contra log x.
- ``tabla_cocientes``: T_i / g_i para cada tamaño (y c₁ = mín, c₂ = máx).
"""

import math


def ajustar_constante(observado, teorico):
    """c = Σ T·g / Σ g² (ajuste por mínimos cuadrados de T ≈ c·g, sin término independiente)."""
    if len(observado) != len(teorico) or not observado:
        raise ValueError("listas vacías o de distinto largo")
    den = sum(g * g for g in teorico)
    if den == 0:
        raise ValueError("la función teórica es cero en todos los puntos")
    return sum(t * g for t, g in zip(observado, teorico)) / den


def ajustar_combinacion(observado, bases):
    """Coeficientes no negativos (a_1, ..., a_k) que minimizan Σ (T_i − Σ_j a_j·g_j(i))², con k = 1 o 2.

    Sirve para el tiempo de CPU, que suma un costo fijo por evaluación y un costo por
    consulta: T ≈ a·(evaluaciones) + b·Q. Si la solución sin restricciones tiene un
    coeficiente negativo, se usa la mejor base sola (mínimos cuadrados no negativos con dos variables).
    """
    if len(bases) == 1:
        return [ajustar_constante(observado, bases[0])]
    if len(bases) != 2:
        raise ValueError("solo se admiten una o dos bases")
    g1, g2 = bases
    s11 = sum(a * a for a in g1)
    s22 = sum(b * b for b in g2)
    s12 = sum(a * b for a, b in zip(g1, g2))
    t1 = sum(t * a for t, a in zip(observado, g1))
    t2 = sum(t * b for t, b in zip(observado, g2))
    det = s11 * s22 - s12 * s12
    if det > 1e-12 * s11 * s22:
        a, b = (t1 * s22 - t2 * s12) / det, (t2 * s11 - t1 * s12) / det
        if a >= 0 and b >= 0:
            return [a, b]
    candidatos = []
    for j, g in enumerate(bases):
        c = max(0.0, ajustar_constante(observado, g))
        error = sum((t - c * v) ** 2 for t, v in zip(observado, g))
        candidatos.append((error, j, c))
    _, j, c = min(candidatos)
    return [c if i == j else 0.0 for i in range(2)]


def pendiente_loglog(x, y):
    """Pendiente de log y contra log x (mínimos cuadrados). Requiere x, y > 0 y al menos 2 puntos distintos."""
    if len(x) != len(y) or len(x) < 2:
        raise ValueError("se necesitan al menos 2 puntos")
    if any(v <= 0 for v in list(x) + list(y)):
        raise ValueError("log-log requiere valores positivos")
    lx, ly = [math.log(v) for v in x], [math.log(v) for v in y]
    mx, my = sum(lx) / len(lx), sum(ly) / len(ly)
    sxx = sum((a - mx) ** 2 for a in lx)
    if sxx == 0:
        raise ValueError("todos los x son iguales")
    return sum((a - mx) * (b - my) for a, b in zip(lx, ly)) / sxx


def tabla_cocientes(tamanos, observado, teorico):
    """[{tamano, observado, teorico, cociente}] y las cotas c₁ = mín, c₂ = máx de los cocientes."""
    filas = [{"tamano": x, "observado": t, "teorico": g, "cociente": t / g}
             for x, t, g in zip(tamanos, observado, teorico)]
    cocientes = [f["cociente"] for f in filas]
    return {"filas": filas, "c1": min(cocientes), "c2": max(cocientes)}
