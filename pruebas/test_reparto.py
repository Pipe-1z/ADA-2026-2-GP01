"""Pruebas del Algoritmo 4: reparto uniforme, Successive Halving con presupuesto y UCB1."""

import pytest

from oraculo_ada.algoritmos import costo_sh, muestra_configuraciones
from oraculo_ada.algoritmos.reparto import (
    ESQUEMAS,
    n0_para_presupuesto,
    reparto_sh,
    reparto_ucb1,
    reparto_uniforme,
)
from oraculo_ada.oraculos import generar_calibrado, generar_conjuntivo


def conjunto(semilla=1, M=32):
    o = generar_conjuntivo(4, 4, 60, semilla, limpias_por_ranura=0, interacciones=4)
    return o, muestra_configuraciones(o, M, semilla)


@pytest.mark.parametrize("esquema", list(ESQUEMAS))
@pytest.mark.parametrize("B", [32, 100, 300, 1000, 5000])
def test_ningun_esquema_supera_el_presupuesto(esquema, B):
    o, S = conjunto()
    r = ESQUEMAS[esquema](o, S, B, semilla_instancias=3)
    assert r.consultas_cobradas <= B
    if r.factible:
        assert r.elegido in S


def test_uniforme_gasta_S_por_m():
    o, S = conjunto()
    r = reparto_uniforme(o, S, 250, semilla_instancias=1)
    assert r.parametro["m"] == 250 // 32 and r.consultas_cobradas == 32 * (250 // 32)
    assert not reparto_uniforme(o, S, 31, semilla_instancias=1).factible


def test_n0_para_presupuesto_es_el_mayor_que_cabe():
    for B in (300, 1000, 2500, 10000):
        n0 = n0_para_presupuesto(128, B, 100)
        if n0 is not None:
            assert costo_sh(128, n0, 100)["con_reutilizar"] <= B
            assert n0 == 100 or costo_sh(128, n0 + 1, 100)["con_reutilizar"] > B
    assert n0_para_presupuesto(128, 10, 100) is None


def test_con_presupuesto_completo_los_tres_eligen_la_mejor():
    o, S = conjunto(5, M=16)
    mejor = max(o.precision_exacta(c) for c in S)
    for esquema in ESQUEMAS:
        o2, _ = conjunto(5, M=16)
        r = ESQUEMAS[esquema](o2, S, 16 * o.n, semilla_instancias=2)
        assert o.precision_exacta(r.elegido) == pytest.approx(mejor), esquema


def test_ucb1_juega_cada_brazo_al_menos_una_vez_y_es_reproducible():
    o, S = conjunto()
    r = reparto_ucb1(o, S, 200, semilla_instancias=4)
    assert r.parametro["jugadas_min"] >= 1 and r.parametro["jugadas_totales"] == 200
    o2, _ = conjunto()
    assert reparto_ucb1(o2, S, 200, semilla_instancias=4).elegido == r.elegido
    assert not reparto_ucb1(o, S, 31, semilla_instancias=4).factible


def test_sh_con_presupuesto_usa_el_n0_calculado():
    o = generar_calibrado()
    S = muestra_configuraciones(o, 128, 7)
    r = reparto_sh(o, S, 2000, semilla_instancias=1)
    assert r.parametro["n0"] == n0_para_presupuesto(128, 2000, 100)
    assert r.consultas_cobradas == costo_sh(128, r.parametro["n0"], 100)["con_reutilizar"]
