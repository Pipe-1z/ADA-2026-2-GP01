"""Pruebas del oráculo sintético (Fase 1)."""

import itertools
import random

import pytest

from oraculo_ada.oraculos import (
    OraculoSintetico,
    desde_3sat,
    fallos_por_familia,
    generar_3sat,
    generar_conjuntivo,
    generar_disyuntivo,
)


def configs_al_azar(o, cantidad, semilla=0):
    rng = random.Random(semilla)
    return [o.config([rng.randrange(o.k) for _ in range(o.m)]) for _ in range(cantidad)]


def satisface(clausula, asignacion):
    """Evaluación directa de una cláusula DIMACS; asignacion[v-1] ∈ {0, 1}."""
    return any((asignacion[abs(l) - 1] == 1) == (l > 0) for l in clausula)


# ---------------------------------------------------------------- reproducibilidad

@pytest.mark.parametrize("generador", ["conjuntivo", "disyuntivo"])
def test_misma_semilla_mismo_oraculo(generador):
    gen = generar_conjuntivo if generador == "conjuntivo" else generar_disyuntivo
    a = gen(5, 8, 100, semilla=11, interacciones=6)
    b = gen(5, 8, 100, semilla=11, interacciones=6)
    c = gen(5, 8, 100, semilla=12, interacciones=6)
    configs = configs_al_azar(a, 200)
    assert [a.evaluar(x).precision for x in configs] == [b.evaluar(x).precision for x in configs]
    assert [a.evaluar(x).trazas for x in configs[:20]] == [b.evaluar(x).trazas for x in configs[:20]]
    assert [a.precision_exacta(x) for x in configs] != [c.precision_exacta(x) for x in configs]


def test_ruido_reproducible_y_distinto_por_semilla_de_consulta():
    a = generar_conjuntivo(4, 4, 200, semilla=3, ruido=0.3)
    b = generar_conjuntivo(4, 4, 200, semilla=3, ruido=0.3)
    x = a.config([1, 2, 3, 0])
    assert a.evaluar(x, semilla=1).trazas == b.evaluar(x, semilla=1).trazas
    assert a.evaluar(x, semilla=1).trazas != a.evaluar(x, semilla=2).trazas


# ---------------------------------------------------------------- modelo conjuntivo

def test_conjuntivo_con_opciones_limpias_y_sin_interacciones_tiene_optimo_uno():
    o = generar_conjuntivo(3, 4, 60, semilla=5)
    limpia = o.config([next(a for a in range(o.k) if not o.rompe[(p, a)]) for p in range(o.m)])
    acc, optimas = o.optimo_exacto()
    assert acc == 1.0
    assert limpia in optimas


def test_conjuntivo_sin_limpias_toda_opcion_rompe_algo():
    o = generar_conjuntivo(4, 5, 50, semilla=2, limpias_por_ranura=0)
    assert all(o.rompe[(p, a)] for p in range(o.m) for a in range(o.k))
    acc, _ = o.optimo_exacto()
    assert acc < 1.0


def test_conjuntivo_regla_todo_o_nada():
    """Una instancia pasa si y solo si ninguna de sus familias está rota."""
    o = generar_conjuntivo(4, 4, 80, semilla=9, interacciones=5)
    for x in configs_al_azar(o, 50):
        rotas = set().union(*(o.rompe[(p, x[r])] for p, r in enumerate(o.ranuras)))
        for (p, a), (q, b), fams in o.interacciones:
            if x[o.ranuras[p]] == a and x[o.ranuras[q]] == b:
                rotas |= fams
        esperado = sum(not (set(f) & rotas) for f in o.familias_instancia) / o.n
        assert o.precision_exacta(x) == pytest.approx(esperado)


def test_conjuntivo_genera_familias_por_instancia_pedidas():
    o = generar_conjuntivo(5, 8, 300, semilla=4)
    assert {len(f) for f in o.familias_instancia} == {2, 3}
    assert all(len(set(f)) == len(f) for f in o.familias_instancia)


# ---------------------------------------------------------------- modelo disyuntivo / 3-SAT

def test_reduccion_formula_satisfacible_del_informe():
    """φ = (x1 ∨ ¬x2 ∨ x3) ∧ (¬x1 ∨ x2 ∨ x3): óptimo 1 y óptimos = asignaciones que satisfacen φ."""
    clausulas = [[1, -2, 3], [-1, 2, 3]]
    o = desde_3sat(clausulas, 3)
    acc, optimas = o.optimo_exacto()
    satisfacen = [list(s) for s in itertools.product((0, 1), repeat=3)
                  if all(satisface(c, s) for c in clausulas)]
    assert acc == 1.0
    assert sorted([o.clave(c)[:3] for c in optimas]) == sorted(tuple(s) for s in satisfacen)


def test_reduccion_formula_insatisfacible_da_siete_octavos():
    """Las 8 cláusulas sobre x1, x2, x3: cada asignación falsifica exactamente una (MAX-3-SAT = 7/8)."""
    clausulas = [[s1 * 1, s2 * 2, s3 * 3] for s1, s2, s3 in itertools.product((1, -1), repeat=3)]
    o = desde_3sat(clausulas, 3)
    assert all(o.precision_exacta(c) == pytest.approx(7 / 8) for c in o.espacio())
    acc, optimas = o.optimo_exacto()
    assert acc == pytest.approx(7 / 8) and len(optimas) == 8


def test_precision_es_la_fraccion_de_clausulas_satisfechas():
    o = generar_3sat(12, 4.26, semilla=21)
    assert o.n == round(4.26 * 12)
    assert all(len({abs(l) for l in c}) == 3 for c in o.clausulas)
    for x in configs_al_azar(o, 100):
        asignacion = [x[r] for r in o.ranuras]
        esperado = sum(satisface(c, asignacion) for c in o.clausulas) / o.n
        assert o.precision_exacta(x) == pytest.approx(esperado)
        assert o.evaluar(x).precision == pytest.approx(esperado)


def test_disyuntivo_literales_en_ranuras_distintas():
    o = generar_disyuntivo(6, 4, 200, semilla=8, literales_por_instancia=3)
    assert all(len({p for p, _ in L}) == 3 for L in o.literales)


# ---------------------------------------------------------------- interacciones que solo rompen

@pytest.mark.parametrize("generador", ["conjuntivo", "disyuntivo"])
def test_interacciones_solo_rompen(generador):
    gen = generar_conjuntivo if generador == "conjuntivo" else generar_disyuntivo
    sin = gen(4, 3, 60, semilla=17)
    con = gen(4, 3, 60, semilla=17, interacciones=15)
    assert con.interacciones
    alguna_baja = False
    for x in sin.espacio():
        p_sin, p_con = sin.precision_exacta(x), con.precision_exacta(x)
        assert p_con <= p_sin
        alguna_baja |= p_con < p_sin
    assert alguna_baja


def test_monotonia_fallar_con_ranuras_fijas_es_definitivo():
    """Si una instancia falla por las opciones (y pares) de las ranuras fijadas, falla para cualquier completación.

    Es la propiedad en que se apoya la cota del Algoritmo 1.
    """
    o = generar_conjuntivo(4, 3, 40, semilla=6, limpias_por_ranura=0, interacciones=8)
    for prefijo in itertools.product(range(o.k), repeat=2):
        rotas = set(o.rompe[(0, prefijo[0])]) | set(o.rompe[(1, prefijo[1])])
        for (p, a), (q, b), fams in o.interacciones:
            if p < 2 and q < 2 and prefijo[p] == a and prefijo[q] == b:
                rotas |= fams
        fallan = {i for i, f in enumerate(o.familias_instancia) if set(f) & rotas}
        for resto in itertools.product(range(o.k), repeat=2):
            x = o.config(list(prefijo) + list(resto))
            ids_fallidos = {t["id"] for t in o.evaluar(x).trazas}
            assert fallan <= ids_fallidos


def test_interaccion_construida_crea_optimo_local():
    """Contraejemplo mínimo: dos ranuras, el óptimo exige cambiar las dos a la vez."""
    # ranura 0: opción 0 rompe f0, opción 1 limpia; ranura 1: opción 0 rompe f1, opción 1 limpia;
    # la interacción ((0,1),(1,0)) y ((0,0),(1,1)) rompen f2: solo (1,1) y (0,0) evitan f2.
    rompe = {(0, 0): {"f0"}, (0, 1): set(), (1, 0): {"f1"}, (1, 1): set()}
    familias = [("f0",), ("f1",), ("f2",), ("f2",), ("f2",)]
    inter = [((0, 1), (1, 0), {"f2"}), ((0, 0), (1, 1), {"f2"})]
    o = OraculoSintetico("conjuntivo", 2, 2, rompe=rompe, familias_instancia=familias, interacciones=inter)
    acc = {c: o.precision_exacta(o.config(c)) for c in itertools.product((0, 1), repeat=2)}
    assert acc[(1, 1)] == 1.0
    assert acc[(0, 0)] == pytest.approx(3 / 5)
    assert acc[(0, 1)] < acc[(0, 0)] and acc[(1, 0)] < acc[(0, 0)]   # (0,0) es óptimo local de una ranura


# ---------------------------------------------------------------- contador de consultas y caché

def test_contador_cobra_solo_consultas_nuevas():
    o = generar_conjuntivo(3, 4, 50, semilla=1)
    x = o.config([1, 2, 3])
    r1 = o.evaluar(x)
    r2 = o.evaluar(x)
    assert (r1.consultas_nuevas, r2.consultas_nuevas) == (50, 0)
    assert o.contadores()["consultas"] == 50
    assert o.consultas_solicitadas == 100 and o.evaluaciones == 2
    o.evaluar(x, instancias=o.instancias[:10], semilla=2)
    assert o.consultas == 60
    o.evaluar(x, instancias=o.instancias[:20], semilla=2)
    assert o.consultas == 70
    assert len(o.historial) == 4 and all(h["segundos"] >= 0 for h in o.historial)


def test_sin_cache_cobra_todo():
    o = generar_conjuntivo(3, 4, 50, semilla=1, cache=False)
    x = o.config([0, 0, 0])
    o.evaluar(x)
    o.evaluar(x)
    assert o.consultas == 100


def test_reiniciar_contadores_conserva_cache():
    o = generar_conjuntivo(3, 4, 30, semilla=1)
    x = o.config([0, 1, 2])
    o.evaluar(x)
    o.reiniciar_contadores()
    assert o.contadores() == {"consultas": 0, "consultas_solicitadas": 0, "evaluaciones": 0, "segundos": 0.0}
    assert o.evaluar(x).consultas_nuevas == 0


def test_verdad_conocida_no_cobra_consultas():
    o = generar_disyuntivo(4, 3, 40, semilla=2)
    o.precision_exacta(o.config([0, 1, 2, 0]))
    o.optimo_exacto()
    assert o.consultas == 0 and o.evaluaciones == 0


# ---------------------------------------------------------------- ruido

def test_ruido_cero_y_uno():
    sin = generar_conjuntivo(3, 4, 80, semilla=5, interacciones=2)
    todo = generar_conjuntivo(3, 4, 80, semilla=5, interacciones=2, ruido=1.0)
    for x in configs_al_azar(sin, 30):
        assert sin.evaluar(x).precision == pytest.approx(sin.precision_exacta(x))
        assert todo.evaluar(x).precision == pytest.approx(1 - sin.precision_exacta(x))


def test_ruido_voltea_la_fraccion_esperada():
    o = generar_conjuntivo(3, 4, 500, semilla=5, ruido=0.25)
    exacta = generar_conjuntivo(3, 4, 500, semilla=5)
    volteos = total = 0
    for s, x in enumerate(configs_al_azar(o, 20)):
        fallos_ruido = {t["id"] for t in o.evaluar(x, semilla=s).trazas}
        fallos_exactos = {t["id"] for t in exacta.evaluar(x).trazas}
        volteos += len(fallos_ruido ^ fallos_exactos)
        total += o.n
    assert 0.22 < volteos / total < 0.28


# ---------------------------------------------------------------- forma de las trazas y del espacio

@pytest.mark.parametrize("generador", ["conjuntivo", "disyuntivo"])
def test_trazas_con_la_forma_del_oraculo_real(generador):
    gen = generar_conjuntivo if generador == "conjuntivo" else generar_disyuntivo
    o = gen(4, 4, 70, semilla=13, interacciones=4)
    for x in configs_al_azar(o, 20):
        r = o.evaluar(x)
        assert len(r.trazas) == r.n - r.aciertos
        assert all(set(t) == {"id", "violo", "salida"} and t["violo"] for t in r.trazas)
        assert sum(fallos_por_familia(r).values()) == len(r.trazas)


def test_optimo_exacto_coincide_con_maximo_del_espacio():
    o = generar_conjuntivo(4, 4, 60, semilla=19, limpias_por_ranura=0, interacciones=6)
    acc, optimas = o.optimo_exacto()
    valores = {o.clave(x): o.precision_exacta(x) for x in o.espacio()}
    assert acc == pytest.approx(max(valores.values()))
    assert {o.clave(x) for x in optimas} == {c for c, v in valores.items() if v == pytest.approx(acc)}


def test_espacio_y_tamano():
    o = generar_conjuntivo(3, 4, 10, semilla=0, temperaturas=(0.0, 0.3, 0.7))
    assert o.tamano_espacio() == 64 and o.tamano_espacio(con_temperatura=True) == 192
    assert len(list(o.espacio())) == 64 and len(list(o.espacio(con_temperatura=True))) == 192


def test_configuraciones_invalidas():
    o = generar_conjuntivo(3, 4, 10, semilla=0)
    with pytest.raises(ValueError):
        o.evaluar({"r0": 0, "r1": 0, "r2": 9, "temperatura": 0.0})
    with pytest.raises(ValueError):
        o.evaluar({"r0": 0, "r1": 0, "temperatura": 0.0})
    with pytest.raises(ValueError):
        o.evaluar(o.config([0, 0, 0], temperatura=0.3))


def test_ranuras_con_nombres_del_proyecto():
    nombres = ["rol", "estrategia", "formato", "estilo", "cierre"]
    o = generar_conjuntivo(5, 8, 100, semilla=1, ranuras=nombres)
    x = o.config(rol=0, estrategia=0, formato=0, estilo=5, cierre=1)
    assert list(x) == nombres + ["temperatura"]
    assert o.tamano_espacio() == 8 ** 5
