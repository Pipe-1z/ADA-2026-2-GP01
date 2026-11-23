"""Pruebas del Algoritmo 2 (Successive Halving) y de las estrategias de la Fase 4."""

import itertools
import math
import random

import pytest

from oraculo_ada.algoritmos import (
    ascenso_coordenadas,
    costo_enunciado,
    costo_sh,
    costo_sh_cerrado,
    cota_eliminar_mejor,
    dos_ranuras_sh,
    fuerza_bruta,
    muestra_configuraciones,
    successive_halving,
    vecindario_doble,
)
from oraculo_ada.oraculos import generar_3sat, generar_calibrado, generar_conjuntivo

N0S = [1, 2, 3, 4, 5, 8, 16]
NS = [1, 2, 10, 50, 100, 150, 1000]


# ---------------------------------------------------------------- fórmulas

@pytest.mark.parametrize("R", range(1, 16))
def test_formula_cerrada_coincide_con_el_conteo_por_rondas(R):
    for n0, n in itertools.product(N0S, NS):
        if n0 > n:
            continue
        cerrada, conteo = costo_sh_cerrado(R, n0, n), costo_sh(2 ** R, n0, n)
        assert conteo["rondas"] == R
        assert cerrada["sin_reutilizar"] == conteo["sin_reutilizar"]
        assert cerrada["con_reutilizar"] == conteo["con_reutilizar"]


@pytest.mark.parametrize("R", range(1, 16))
def test_sin_tope_es_la_formula_del_enunciado(R):
    for n0 in N0S:
        justo = n0 * 2 ** (R - 1)                # la última ronda alcanza el tope exactamente: ρ = R − 1
        holgado = justo + 1                      # ninguna ronda toca el tope: ρ = R
        assert costo_sh_cerrado(R, n0, justo)["rho"] == R - 1 and costo_sh_cerrado(R, n0, holgado)["rho"] == R
        for n in (justo, holgado):
            assert costo_sh_cerrado(R, n0, n)["sin_reutilizar"] == 2 ** R * n0 * R == costo_enunciado(2 ** R, n0)


def test_con_tope_cuesta_menos_que_el_enunciado_y_depende_de_n():
    a, b = costo_sh(2 ** 15, 2, 100)["sin_reutilizar"], costo_sh(2 ** 15, 2, 150)["sin_reutilizar"]
    assert a < b < costo_enunciado(2 ** 15, 2)


# ---------------------------------------------------------------- el código cuenta lo que dice la fórmula

@pytest.mark.parametrize("R", range(2, 9))
def test_el_codigo_cobra_lo_que_dice_la_formula(R):
    o = generar_3sat(max(R, 3), 4.0, R)          # k = 2, m = R
    if o.m != R:
        pytest.skip("3-SAT necesita al menos 3 variables")
    candidatos = list(o.espacio())
    for n0 in (1, 3, 5):
        o2 = generar_3sat(R, 4.0, R)
        sh = successive_halving(o2, candidatos, n0=n0, semilla_instancias=7)
        esperado = costo_sh(len(candidatos), n0, o2.n)
        assert sh.consultas_solicitadas == esperado["sin_reutilizar"] + o2.n
        assert sh.consultas_cobradas == esperado["con_reutilizar"] + esperado["completar_ganador"]
        assert [x["n_r"] for x in sh.rondas] == [nr for _, nr in esperado["por_ronda"]]


def test_conteo_con_candidatos_que_no_son_potencia_de_dos():
    o = generar_conjuntivo(3, 3, 60, 2)          # |C| = 27
    sh = successive_halving(o, list(o.espacio()), n0=2, semilla_instancias=1)
    esperado = costo_sh(27, 2, 60)
    assert [x["candidatos"] for x in sh.rondas] == [27, 14, 7, 4, 2]
    assert sh.consultas_solicitadas == esperado["sin_reutilizar"] + 60
    assert sh.consultas_cobradas == esperado["con_reutilizar"] + esperado["completar_ganador"]


# ---------------------------------------------------------------- comportamiento

def test_con_muestras_completas_devuelve_el_optimo():
    o = generar_conjuntivo(4, 4, 50, 3, limpias_por_ranura=0, interacciones=6)
    fb = fuerza_bruta(o, verdad_conocida=True)
    sh = successive_halving(o, list(o.espacio()), n0=50, semilla_instancias=0)
    assert sh.precision_ganador == pytest.approx(fb.mejor_precision)


def test_reproducible_y_dependiente_de_la_semilla():
    candidatos = muestra_configuraciones(generar_calibrado(), 256, semilla=1)
    a = successive_halving(generar_calibrado(), candidatos, n0=1, semilla_instancias=5)
    b = successive_halving(generar_calibrado(), candidatos, n0=1, semilla_instancias=5)
    c = successive_halving(generar_calibrado(), candidatos, n0=1, semilla_instancias=6)
    assert a.ganador == b.ganador and a.rondas == b.rondas
    assert a.orden_instancias != c.orden_instancias


def test_muestra_y_vecindario():
    o = generar_calibrado()
    muestra = muestra_configuraciones(o, 500, semilla=3)
    assert len({o.clave(c) for c in muestra}) == 500 and muestra == muestra_configuraciones(o, 500, semilla=3)
    chico = generar_conjuntivo(2, 3, 5, 1)
    assert {chico.clave(c) for c in muestra_configuraciones(chico, 9, 0)} == {chico.clave(c) for c in chico.espacio()}
    x = o.config([0, 0, 0, 5, 1])
    vecinos = vecindario_doble(o, x)
    assert len(vecinos) == math.comb(5, 2) * 7 * 7 == 490
    assert all(sum(v[r] != x[r] for r in o.ranuras) == 2 for v in vecinos)
    assert len({o.clave(v) for v in vecinos}) == 490


def test_dos_ranuras_sh_escapa_del_par_acoplado_con_muestra_completa():
    o = generar_conjuntivo(4, 4, 80, semilla=5, pares_acoplados=1)
    par = o.parametros["pares_acoplados"][0]
    (p, q), (gp, gq) = par["ranuras"], par["opciones"]
    inicial = [0] * 4
    inicial[p], inicial[q] = (gp + 1) % 4, (gq + 1) % 4
    simple = ascenso_coordenadas(generar_conjuntivo(4, 4, 80, semilla=5, pares_acoplados=1), o.config(inicial))
    r = dos_ranuras_sh(o, n0=80, rondas=2, semilla_instancias=1, inicial=o.config(inicial))
    assert r["mejor_precision"] > simple.mejor_precision
    assert any(h.get("adoptado") for h in r["historia"])


# ---------------------------------------------------------------- probabilidad de eliminar a la mejor

def test_cota_es_cero_si_todas_las_rondas_usan_toda_la_poblacion():
    assert cota_eliminar_mejor([0.1, 0.2, 0.3, 0.3], n0=100, n=100)["cota"] == 0.0


def test_cota_baja_con_muestras_mas_grandes():
    rng = random.Random(0)
    precisiones = [rng.random() * 0.5 for _ in range(64)] + [0.9]
    cotas = [cota_eliminar_mejor(precisiones, n0, 100)["cota"] for n0 in (1, 4, 16, 64)]
    assert cotas == sorted(cotas, reverse=True)


def test_frecuencia_observada_no_supera_la_cota():
    o = generar_conjuntivo(4, 4, 100, 11, limpias_por_ranura=0, interacciones=4)
    candidatos = list(o.espacio())
    verdad = [o.precision_exacta(c) for c in candidatos]
    cota = cota_eliminar_mejor(verdad, 8, o.n)["cota"]
    fallos = sum(o.precision_exacta(successive_halving(o, candidatos, n0=8, semilla_instancias=s,
                                                        evaluar_ganador=False).ganador) < max(verdad)
                 for s in range(200))
    assert fallos / 200 <= min(1.0, cota) + 0.05
