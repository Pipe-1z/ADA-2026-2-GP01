"""Pruebas de la fuerza bruta y del Algoritmo 3 (Fase 2)."""

import csv
import itertools
import json

import pytest

from oraculo_ada import rutas
from oraculo_ada.algoritmos import ascenso_coordenadas, cota_consultas_coordenadas, fuerza_bruta
from oraculo_ada.algoritmos.coordenadas import HIPOTESIS_PRIMERA_ENTREGA
from oraculo_ada.oraculos import OraculoSintetico, generar_conjuntivo, generar_disyuntivo

RANURAS = ["rol", "estrategia", "formato", "estilo", "cierre"]


# ---------------------------------------------------------------- fuerza bruta

@pytest.mark.parametrize("generador", [generar_conjuntivo, generar_disyuntivo])
def test_fuerza_bruta_coincide_con_el_optimo_y_cobra_C_por_n(generador):
    o = generador(4, 4, 50, semilla=3, interacciones=5)
    acc, optimas = o.optimo_exacto()
    r = fuerza_bruta(o)
    assert r.mejor_precision == pytest.approx(acc)
    assert [o.clave(c) for c in r.optimas] == [o.clave(c) for c in optimas]
    assert r.configuraciones_evaluadas == 4 ** 4
    assert r.consultas_oraculo_real == 4 ** 4 * 50
    assert r.consultas_cobradas == r.consultas_oraculo_real == r.consultas_solicitadas


def test_fuerza_bruta_reporta_el_costo_real_aunque_no_cobre():
    o = generar_conjuntivo(3, 5, 40, semilla=1)
    conocida = fuerza_bruta(o, verdad_conocida=True)
    assert conocida.consultas_cobradas == 0 and conocida.consultas_oraculo_real == 5 ** 3 * 40
    primera = fuerza_bruta(o)
    segunda = fuerza_bruta(o)                       # todo en caché
    assert primera.consultas_cobradas == 5 ** 3 * 40 and segunda.consultas_cobradas == 0
    assert segunda.consultas_oraculo_real == 5 ** 3 * 40
    assert conocida.mejor_config == primera.mejor_config


def test_fuerza_bruta_con_temperatura():
    o = generar_conjuntivo(2, 3, 10, semilla=1, temperaturas=(0.0, 0.3, 0.7))
    r = fuerza_bruta(o, con_temperatura=True)
    assert r.configuraciones_evaluadas == 27 and r.consultas_oraculo_real == 270


# ---------------------------------------------------------------- Algoritmo 3 en el sintético

def caso_independiente(semilla=7, n=100, k=8):
    """Cada ranura rompe solo su propia familia (como pruebas/prueba_sintetica.py): ranuras independientes."""
    import random

    rng = random.Random(semilla)
    limpia = {p: rng.randrange(k) for p in range(5)}
    rompe = {(p, a): (set() if a == limpia[p] else {f"f{p}"}) for p in range(5) for a in range(k)}
    familias = [f"f{p}" for p in range(5)]
    instancias = [(f,) for f in familias] + [tuple(rng.sample(familias, rng.choice([1, 2, 3])))
                                             for _ in range(n - 5)]
    o = OraculoSintetico("conjuntivo", 5, k, rompe=rompe, familias_instancia=instancias, ranuras=RANURAS)
    return o, o.config([limpia[p] for p in range(5)])


def test_coordenadas_encuentra_el_optimo_con_ranuras_independientes():
    o, limpia = caso_independiente()
    r = ascenso_coordenadas(o)
    assert r.mejor_config == limpia and r.mejor_precision == 1.0
    assert r.consultas_cobradas <= cota_consultas_coordenadas([8] * 5, o.n, 3)


def test_coordenadas_costo_dentro_de_la_cota_y_ascenso_monotono():
    o = generar_conjuntivo(5, 8, 100, semilla=2, interacciones=10, ranuras=RANURAS, temperaturas=(0.0, 0.3, 0.7))
    r = ascenso_coordenadas(o)
    assert r.consultas_solicitadas == r.evaluaciones * o.n
    assert r.consultas_cobradas <= r.consultas_solicitadas <= cota_consultas_coordenadas([8] * 5, o.n, 3, 3)
    precisiones = [m["precision_despues"] for m in r.movimientos]
    assert all(m["precision_despues"] > m["precision_antes"] for m in r.movimientos)
    assert precisiones == sorted(precisiones)
    assert r.mejor_precision == pytest.approx(o.precision_exacta(r.mejor_config))


def test_coordenadas_en_empate_conserva_la_actual():
    rompe = {(p, a): set() for p in range(3) for a in range(4)}
    o = OraculoSintetico("conjuntivo", 3, 4, rompe=rompe, familias_instancia=[("f0",)] * 10)
    r = ascenso_coordenadas(o)
    assert r.movimientos == [] and r.convergio and r.pasadas == 1
    assert r.evaluaciones == 1 + 3 * 3 and r.mejor_config == o.config([0, 0, 0])


def test_pares_acoplados_crean_un_optimo_local():
    """Con las opciones limpias de dos ranuras acopladas, partiendo sin ninguna de las dos,
    el ascenso nunca las adopta y termina por debajo del óptimo."""
    o = generar_conjuntivo(4, 4, 80, semilla=5, pares_acoplados=1)
    par = o.parametros["pares_acoplados"][0]
    (p, q), (gp, gq) = par["ranuras"], par["opciones"]
    inicial = [0] * 4
    inicial[p], inicial[q] = (gp + 1) % 4, (gq + 1) % 4
    r = ascenso_coordenadas(o, o.config(inicial))
    acc_opt, _ = o.optimo_exacto()
    sin_el_par = max(o.precision_exacta(c) for c in o.espacio()
                     if c[o.ranuras[p]] != gp and c[o.ranuras[q]] != gq)
    assert r.mejor_config[o.ranuras[p]] != gp and r.mejor_config[o.ranuras[q]] != gq
    assert r.mejor_precision <= sin_el_par < acc_opt == 1.0


def test_pares_acoplados_solo_penalizan_las_combinaciones_mixtas():
    o = generar_conjuntivo(4, 4, 60, semilla=8, pares_acoplados=2)
    for par in o.parametros["pares_acoplados"]:
        (p, q), (gp, gq) = par["ranuras"], par["opciones"]
        for c in o.espacio():
            mixta = (c[o.ranuras[p]] == gp) != (c[o.ranuras[q]] == gq)
            if mixta:
                assert o.precision_exacta(c) == 0.0
    limpia = o.config([next(a for a in range(4) if not o.rompe[(x, a)]) for x in range(4)])
    assert o.precision_exacta(limpia) == 1.0


def test_instancias_insolubles():
    o = generar_conjuntivo(3, 4, 100, semilla=4, fraccion_insoluble=0.3)
    assert o.parametros["instancias_insolubles"] == 30
    acc, _ = o.optimo_exacto()
    assert acc == pytest.approx(0.7)


# ---------------------------------------------------------------- reproducción del registro real

RUTA_CACHE_T4 = rutas.dir_cache() / "cache_oraculo.json"


@pytest.mark.skipif(not RUTA_CACHE_T4.exists(), reason="requiere cache/cache_oraculo.json (copia de Drive)")
def test_reproduce_las_68_evaluaciones_del_registro(tmp_path):
    rutas.preparar_modulos_del_curso()
    pytest.importorskip("open_instruct.IFEvalG.instructions_registry")
    from ayudas import cargar_datos, dividir

    from oraculo_ada.oraculos.real import OraculoReal, oraculo_curso_desde_cache

    busqueda, validacion = dividir(cargar_datos(str(rutas.RAIZ / "datos_visibles.json")))
    curso = oraculo_curso_desde_cache(RUTA_CACHE_T4, busqueda, validacion)
    o = OraculoReal(curso, busqueda, hardware="t4", ruta_libro=tmp_path / "libro.json")
    r = ascenso_coordenadas(o, hipotesis=HIPOTESIS_PRIMERA_ENTREGA)
    with open(rutas.RAIZ / "resultados" / "registro_busqueda.csv", encoding="utf-8") as f:
        registro = list(csv.DictReader(f))
    assert len(r.registro) == len(registro) == 68
    for a, b in zip(r.registro, registro):
        assert (a["fase"], a["ranura_probada"]) == (b["fase"], b["ranura_probada"])
        assert [a["config"][x] for x in RANURAS] == [int(b[x]) for x in RANURAS]
        assert a["config"]["temperatura"] == float(b["temperatura"])
        assert a["precision"] == float(b["precision"])
        assert json.loads(a["fallos_por_familia"]) == json.loads(b["fallos_por_familia"])
        assert a["fallos_por_familia"] == b["fallos_por_familia"] and a["nota"] == b["nota"]
    assert r.mejor_config == {"rol": 0, "estrategia": 0, "formato": 0, "estilo": 5, "cierre": 1, "temperatura": 0.0}
    assert r.consultas_cobradas == 6000 and r.configuraciones_distintas() == 60
    assert sum(len(v) for v in r.descartadas.values()) == 29
    assert (r.pasadas, r.convergio) == (3, True)


# ---------------------------------------------------------------- caso calibrado

def test_caso_calibrado_coincide_con_su_archivo_de_calibracion():
    from oraculo_ada.oraculos import generar_calibrado
    from oraculo_ada.oraculos.sintetico import CALIBRADO
    from oraculo_ada.registro import cargar_resultado

    cal = cargar_resultado("calibracion_sintetico")
    fijos = cal["parametros"]["fijos"]
    esperado = {**fijos, "familias_por_instancia": tuple(fijos["familias_por_instancia"]), **cal["datos"]["elegido"]}
    assert CALIBRADO == esperado
    o = generar_calibrado()
    v = cal["datos"]["verificacion"]
    assert o.precision_exacta(o.config([0] * 5)) == v["precision_inicial"]
    assert o.parametros["instancias_insolubles"] == v["instancias_insolubles"]
    assert ascenso_coordenadas(o).mejor_precision == v["coordenadas_desde_inicial"]["mejor_precision"]
