"""Pruebas del Algoritmo 1: backtracking con poda por cota superior (Fase 3)."""

import itertools
import random

import pytest

from oraculo_ada.algoritmos import backtracking, fuerza_bruta, nodos_por_nivel_peor_caso
from oraculo_ada.oraculos import (
    OraculoSintetico,
    generar_3sat,
    generar_calibrado,
    generar_conjuntivo,
    generar_disyuntivo,
    generar_peor_caso_backtracking,
)


def casos_pequenos():
    """Casos pequeños de los dos modelos, con todas las variantes del generador."""
    casos = []
    for s in range(1, 9):
        casos += [
            generar_conjuntivo(4, 3, 40, s),
            generar_conjuntivo(4, 3, 40, s, limpias_por_ranura=0, interacciones=6),
            generar_conjuntivo(5, 3, 50, s, interacciones=4, pares_acoplados=2, fraccion_insoluble=0.3),
            generar_disyuntivo(4, 3, 40, s, interacciones=5),
            generar_disyuntivo(5, 3, 50, s, literales_por_instancia=2, pares_acoplados=1),
            generar_3sat(8, [2.0, 4.26, 6.0][s % 3], s),
        ]
    return casos


def completaciones(o, parcial):
    resto = itertools.product(range(o.k), repeat=o.m - len(parcial))
    return [o.config(list(parcial) + list(r)) for r in resto]


# ---------------------------------------------------------------- correctitud

@pytest.mark.parametrize("o", casos_pequenos(), ids=lambda o: f"{o.modelo}-{o.m}x{o.k}")
def test_coincide_con_fuerza_bruta(o):
    fb = fuerza_bruta(o, verdad_conocida=True)
    bt = backtracking(o)
    assert bt.mejor_precision == pytest.approx(fb.mejor_precision)
    assert bt.mejor_config == fb.mejor_config                    # primera óptima en orden lexicográfico
    bt_cota = backtracking(generar_igual(o), orden_hijos="cota")
    assert bt_cota.mejor_precision == pytest.approx(fb.mejor_precision)
    assert bt_cota.mejor_config in fb.optimas


def generar_igual(o):
    """Copia sin caché ni contadores (misma estructura)."""
    kw = {"rompe": o.rompe, "familias_instancia": o.familias_instancia,
          "familias_siempre_rotas": o.familias_siempre_rotas} if o.modelo == "conjuntivo" else {"literales": o.literales}
    return OraculoSintetico(o.modelo, o.m, o.k, interacciones=o.interacciones, ranuras=o.ranuras, **kw)


@pytest.mark.parametrize("o", casos_pequenos()[:24], ids=lambda o: f"{o.modelo}-{o.m}x{o.k}")
def test_cota_admisible_y_monotona(o):
    """UB(σ) ≥ Acc(c) para toda c que extiende σ; UB(hijo) ≤ UB(padre); UB(hoja) = Acc."""
    rng = random.Random(0)
    for _ in range(15):
        d = rng.randrange(o.m + 1)
        parcial = tuple(rng.randrange(o.k) for _ in range(d))
        ub = o.cota_superior(parcial)
        assert ub >= max(o.precision_exacta(c) for c in completaciones(o, parcial)) - 1e-12
        if d < o.m:
            assert all(o.cota_superior(parcial + (a,)) <= ub + 1e-12 for a in range(o.k))
        else:
            assert ub == pytest.approx(o.precision_exacta(o.config(list(parcial))))
    assert o.consultas == 0


def test_cota_en_la_raiz_de_la_reduccion():
    """En el caso de 3-SAT, en la raíz toda cláusula tiene un literal sin fijar: UB = 1."""
    o = generar_3sat(10, 4.26, 3)
    assert o.cota_superior(()) == 1.0


# ---------------------------------------------------------------- conteo de nodos

@pytest.mark.parametrize("m,k", [(3, 2), (4, 3), (5, 4), (3, 8)])
def test_sin_poda_recorre_el_arbol_completo(m, k):
    o = generar_conjuntivo(m, k, 20, 1)
    r = backtracking(o, podar=False)
    assert r.nodos_por_nivel == [k ** d for d in range(m + 1)] == r.nodos_por_nivel_peor_caso
    assert r.nodos_explorados == (k ** (m + 1) - 1) // (k - 1)
    assert r.hojas_evaluadas == k ** m and r.consultas_cobradas == k ** m * 20 == r.consultas_peor_caso
    assert r.cotas_calculadas == 0


@pytest.mark.parametrize("m,k", [(3, 2), (4, 3), (5, 8)])
def test_peor_caso_construido_no_poda_nada(m, k):
    o = generar_peor_caso_backtracking(m, k, 50)
    r = backtracking(o)
    assert r.nodos_por_nivel == nodos_por_nivel_peor_caso([k] * m)
    assert sum(r.podados_por_nivel) == 0 and r.hojas_evaluadas == k ** m
    assert r.cotas_calculadas == (k ** m - 1) // (k - 1)          # una cota por nodo interno
    assert r.mejor_precision < 1.0


def test_mejor_caso_la_primera_hoja_es_optima():
    """Si la primera hoja tiene precisión 1, se visita una sola rama y se descartan los hermanos."""
    m, k = 5, 4
    rompe = {(p, a): set() for p in range(m) for a in range(k)}
    o = OraculoSintetico("conjuntivo", m, k, rompe=rompe, familias_instancia=[("f0",)] * 10)
    r = backtracking(o)
    assert r.hojas_evaluadas == 1 and r.consultas_cobradas == 10
    assert r.nodos_explorados == 1 + m * k
    assert r.nodos_por_nivel == [1] + [k] * m


@pytest.mark.parametrize("o", casos_pequenos()[:12], ids=lambda o: f"{o.modelo}-{o.m}x{o.k}")
def test_nodos_explorados_y_descartados_cubren_el_arbol(o):
    """Cada nodo del árbol se explora o está dentro del subárbol de un nodo descartado."""
    r = backtracking(o)
    total = nodos_por_nivel_peor_caso([o.k] * o.m)
    debajo = sum(r.podados_por_nivel[d] * (sum(o.k ** j for j in range(1, o.m - d + 1)))
                 for d in range(o.m + 1))
    assert r.nodos_explorados + debajo == sum(total)
    assert r.consultas_cobradas == r.hojas_evaluadas * o.n


def test_poda_en_el_caso_calibrado():
    o = generar_calibrado()
    r = backtracking(o)
    assert r.mejor_precision == pytest.approx(0.24)
    assert r.hojas_evaluadas < r.nodos_por_nivel_peor_caso[-1]


def test_errores():
    with pytest.raises(ValueError):
        backtracking(generar_conjuntivo(3, 2, 10, 1), orden_hijos="otro")

    class SinCota:
        pass
    with pytest.raises(ValueError):
        backtracking(SinCota())
