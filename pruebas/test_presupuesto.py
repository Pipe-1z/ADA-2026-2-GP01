"""Pruebas del control del presupuesto B (retroalimentación de la primera entrega, ítem 7).

Ningún algoritmo de búsqueda supera B: antes de cada evaluación se comprueba que su costo no
supere el presupuesto restante; si no alcanza, el algoritmo se detiene y devuelve la mejor
configuración encontrada (o ninguna, si B no alcanzó ni para una evaluación completa).
"""

import pytest

from oraculo_ada.algoritmos import (
    ascenso_coordenadas,
    backtracking,
    dos_ranuras_sh,
    fuerza_bruta,
    muestra_configuraciones,
    sh_muestra,
    successive_halving,
)
from oraculo_ada.algoritmos.coordenadas import reinicios
from oraculo_ada.algoritmos.reparto import reparto_sh, reparto_ucb1, reparto_uniforme
from oraculo_ada.oraculos import PresupuestoAgotado, generar_calibrado, generar_conjuntivo

N = 100   # instancias del caso calibrado
DOBLES = {"pares_muestra": 60, "n_preliminar": 20, "top": 3, "rondas": 2, "semilla": 1}


def caso_pequeno():
    return generar_conjuntivo(3, 4, 40, 2, limpias_por_ranura=0, interacciones=3)


# (nombre, generador del oráculo, función (oráculo, B) → (config, precisión, agotado))
ALGORITMOS = [
    ("coordenadas", generar_calibrado,
     lambda o, B: _r(ascenso_coordenadas(o, presupuesto=B))),
    ("coordenadas_variantes", generar_calibrado,
     lambda o, B: _r(ascenso_coordenadas(o, presupuesto=B, desempate="trazas", criterio_poda="instancias",
                                         movimientos_dobles=DOBLES))),
    ("reinicios", generar_calibrado,
     lambda o, B: _r(reinicios(o, 3, semilla_inicios=4, presupuesto=B))),
    ("fuerza_bruta", caso_pequeno,
     lambda o, B: _r(fuerza_bruta(o, presupuesto=B))),
    ("backtracking", caso_pequeno,
     lambda o, B: _r(backtracking(o, presupuesto=B))),
    ("successive_halving", generar_calibrado,
     lambda o, B: _sh(successive_halving(o, muestra_configuraciones(o, 64, 3), n0=2, semilla_instancias=5,
                                         presupuesto=B))),
    ("sh_muestra", generar_calibrado,
     lambda o, B: _sh(sh_muestra(o, 64, n0=1, semilla_muestra=3, semilla_instancias=5, presupuesto=B))),
    ("dos_ranuras_sh", generar_calibrado,
     lambda o, B: _d(dos_ranuras_sh(o, n0=2, rondas=2, semilla_instancias=7, presupuesto=B))),
]


def _r(r):
    return r.mejor_config, r.mejor_precision, r.presupuesto_agotado


def _sh(r):
    return r.ganador, r.precision_ganador, r.presupuesto_agotado


def _d(r):
    return r["mejor_config"], r["mejor_precision"], r["presupuesto_agotado"]


def costo_sin_presupuesto(generar, funcion):
    o = generar()
    salida = funcion(o, None)
    return o.consultas, salida


@pytest.mark.parametrize("nombre,generar,funcion", ALGORITMOS, ids=[a[0] for a in ALGORITMOS])
def test_ningun_algoritmo_supera_B(nombre, generar, funcion):
    total, sin_presupuesto = costo_sin_presupuesto(generar, funcion)
    n = generar().n
    for B in sorted({0, 1, n - 1, n, n + 1, 3 * n + 7, total // 3, total // 2, total - 1, total, total + 500}):
        if B < 0:
            continue
        o = generar()
        config, precision, agotado = funcion(o, B)
        assert o.consultas <= B, (nombre, B, o.consultas)
        if B >= total:
            # con B holgado el resultado es el mismo que sin presupuesto
            assert (config, precision, agotado) == (sin_presupuesto[0], sin_presupuesto[1], False), (nombre, B)
        if agotado and config is not None and precision is not None:
            # la configuración devuelta fue evaluada de verdad: su precisión es la del oráculo
            assert precision == pytest.approx(o.precision_exacta(config))


@pytest.mark.parametrize("nombre,generar,funcion", [a for a in ALGORITMOS if a[0] != "sh_muestra"],
                         ids=[a[0] for a in ALGORITMOS if a[0] != "sh_muestra"])
def test_B_que_no_alcanza_ni_para_una_evaluacion(nombre, generar, funcion):
    o = generar()
    B = o.n - 1 if nombre not in ("successive_halving",) else 1      # SH: la primera evaluación cuesta n0 = 2
    config, precision, agotado = funcion(o, B)
    assert agotado and config is None and precision is None
    assert o.consultas == 0 and o.evaluaciones == 0                 # no se consultó nada


@pytest.mark.parametrize("funcion", [reparto_uniforme, reparto_sh, reparto_ucb1])
def test_reparto_no_supera_B(funcion):
    o = generar_calibrado()
    S = muestra_configuraciones(o, 64, 2)
    for B in (0, 1, 63, 64, 65, 200, 700, 2000, 6400):
        o2 = generar_calibrado()
        r = funcion(o2, S, B, semilla_instancias=3)
        assert o2.consultas <= B
        if not r.factible:
            assert o2.consultas == 0


def test_modo_propias_cuenta_como_si_el_cache_estuviera_vacio():
    """Con el caché lleno, B en modo "propias" limita igual que B en modo "nuevas" con caché vacío."""
    vacio = generar_calibrado()
    r_vacio = ascenso_coordenadas(vacio, presupuesto=1500)
    lleno = generar_calibrado()
    ascenso_coordenadas(lleno)                                      # llena el caché
    nuevas = lleno.consultas
    r_lleno = ascenso_coordenadas(lleno, presupuesto=1500, modo_presupuesto="propias")
    assert lleno.consultas == nuevas                                # todo salió del caché: 0 nuevas
    assert (r_lleno.mejor_config, r_lleno.mejor_precision, r_lleno.presupuesto_agotado) == \
           (r_vacio.mejor_config, r_vacio.mejor_precision, r_vacio.presupuesto_agotado)
    assert r_vacio.presupuesto_agotado
    # en modo "nuevas", con el caché lleno, el mismo B no limita nada
    assert not ascenso_coordenadas(lleno, presupuesto=1500).presupuesto_agotado


def test_presupuestos_anidados_cada_uno_atrapa_el_suyo():
    o = generar_calibrado()
    with pytest.raises(PresupuestoAgotado):
        with o.presupuesto(250):
            ascenso_coordenadas(o, presupuesto=5000)               # el interno no atrapa el agotamiento del externo
    assert o.consultas <= 250
    o2 = generar_calibrado()
    with o2.presupuesto(5000):
        r = ascenso_coordenadas(o2, presupuesto=250)               # aquí corta el interno
    assert r.presupuesto_agotado and o2.consultas <= 250


def test_restante_y_tope_absoluto():
    o = generar_calibrado()
    assert o.restante() is None
    with o.presupuesto(300):
        o.evaluar(o.config([0] * 5))
        assert o.restante() == 200
    o.fijar_tope_absoluto(o.consultas + 50)
    with pytest.raises(PresupuestoAgotado):
        o.evaluar(o.config([1] * 5))
    assert o.evaluar(o.config([0] * 5)).consultas_nuevas == 0       # repetida: costo 0, permitida
