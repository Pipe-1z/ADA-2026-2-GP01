"""Pruebas de las variantes del Algoritmo 3 (Fase 2b)."""

import pytest

from oraculo_ada.algoritmos.coordenadas import ascenso_coordenadas, reinicios
from oraculo_ada.oraculos import OraculoSintetico, generar_calibrado, generar_conjuntivo


def caso_cambio_de_familia():
    """La opción limpia de la ranura 0 solo cambia la familia de la primera restricción violada.

    Ranura 0: opción 0 rompe fA, opción 1 limpia. Ranura 1: opción 0 rompe fB, opción 1 limpia.
    Tres instancias (fA, fB): en (0, 0) fallan por fA; en (1, 0) fallan por fB (fB +3 sin bajar la
    precisión). Óptimo (1, 1) con precisión 1.
    """
    rompe = {(0, 0): {"fA"}, (0, 1): set(), (1, 0): {"fB"}, (1, 1): set()}
    return OraculoSintetico("conjuntivo", 2, 2, rompe=rompe, familias_instancia=[("fA", "fB")] * 3)


def test_original_queda_atrapado_por_empate_y_poda():
    o = caso_cambio_de_familia()
    r = ascenso_coordenadas(o)
    assert r.mejor_precision == 0.0
    assert 1 in r.descartadas["r0"]                       # la limpia se descartó por fB +3


def test_poda_por_instancias_no_descarta_el_cambio_de_familia():
    o = caso_cambio_de_familia()
    r = ascenso_coordenadas(o, criterio_poda="instancias")
    assert 1 not in r.descartadas["r0"]


def test_desempate_por_trazas_escapa_del_empate():
    o = caso_cambio_de_familia()
    r = ascenso_coordenadas(o, desempate="trazas")
    assert r.mejor_precision == 1.0
    assert r.movimientos[0]["motivo"] == "desempate por trazas"


def test_sin_poda_y_poda_por_pasada_reevaluan():
    o = generar_calibrado()
    original = ascenso_coordenadas(o)
    o2 = generar_calibrado()
    sin = ascenso_coordenadas(o2, poda="ninguna")
    assert all(not v for v in sin.descartadas.values())
    assert sin.evaluaciones >= original.evaluaciones
    o3 = generar_calibrado()
    por_pasada = ascenso_coordenadas(o3, poda="por_pasada")
    assert original.evaluaciones <= por_pasada.evaluaciones <= sin.evaluaciones


def test_umbral_mayor_descarta_menos():
    a = ascenso_coordenadas(generar_calibrado())
    b = ascenso_coordenadas(generar_calibrado(), umbral_traza=6)
    assert sum(map(len, b.descartadas.values())) <= sum(map(len, a.descartadas.values()))


def test_movimientos_dobles_escapan_del_par_acoplado():
    o = generar_conjuntivo(4, 4, 80, semilla=5, pares_acoplados=1)
    par = o.parametros["pares_acoplados"][0]
    (p, q), (gp, gq) = par["ranuras"], par["opciones"]
    inicial = [0] * 4
    inicial[p], inicial[q] = (gp + 1) % 4, (gq + 1) % 4
    simple = ascenso_coordenadas(o, o.config(inicial))
    o2 = generar_conjuntivo(4, 4, 80, semilla=5, pares_acoplados=1)
    dobles = ascenso_coordenadas(o2, o2.config(inicial), movimientos_dobles={
        "pares_muestra": 1000, "n_preliminar": 20, "top": 5, "rondas": 2, "semilla": 1})
    assert dobles.mejor_precision > simple.mejor_precision
    assert any(m["motivo"] == "movimiento doble" for m in dobles.movimientos)
    preliminares = [f for f in dobles.registro if "preliminar" in f["fase"]]
    assert preliminares and all(f["consultas"] == 20 for f in preliminares)


def test_movimientos_dobles_son_reproducibles():
    kw = {"movimientos_dobles": {"pares_muestra": 50, "n_preliminar": 20, "top": 3, "rondas": 2, "semilla": 9}}
    a = ascenso_coordenadas(generar_calibrado(), **kw)
    b = ascenso_coordenadas(generar_calibrado(), **kw)
    assert [f["config"] for f in a.registro] == [f["config"] for f in b.registro]


def test_reinicios_comparten_cache_y_eligen_la_mejor():
    o = generar_calibrado()
    r = reinicios(o, 5, semilla_inicios=3)
    assert len(r.corridas) == 5 and r.inicios[0] == o.config([0] * 5)
    assert r.mejor_precision == max(c.mejor_precision for c in r.corridas)
    assert r.consultas_cobradas == sum(c.consultas_cobradas for c in r.corridas)
    assert r.consultas_cobradas <= r.consultas_solicitadas
    r2 = reinicios(generar_calibrado(), 5, semilla_inicios=3)
    assert r2.inicios == r.inicios and r2.mejor_precision == r.mejor_precision


def test_variante_desconocida():
    with pytest.raises(ValueError):
        ascenso_coordenadas(caso_cambio_de_familia(), poda="otra")


def test_veredictos_exactos_y_opciones_limpias():
    o = generar_calibrado()
    x = o.config([0] * 5)
    assert sum(ok for ok, _ in o.veredictos_exactos(x)) / o.n == o.precision_exacta(x)
    assert all(len(v) == 1 for v in o.opciones_limpias().values())
    assert o.consultas == 0
