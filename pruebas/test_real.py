"""Pruebas de la envoltura del oráculo real, con un oráculo falso (sin GPU ni modelo)."""

import itertools
import json
from types import SimpleNamespace

import pytest

from oraculo_ada.hardware import etiqueta_hardware, verificar_hardware
from oraculo_ada.oraculos.real import OraculoReal, ruta_cache_oraculo, ruta_libro_consultas

CATALOGO = {"rol": ["a", "b"], "estilo": ["x", "y", "z"]}
TEMPERATURAS = [0.0, 0.3, 0.7]


def espacio_falso(temperaturas=(0.0,)):
    """Misma forma que ``espacio`` del curso: dicts con las ranuras y la temperatura."""
    return [dict(zip(CATALOGO, combo), temperatura=t)
            for *combo, t in itertools.product(*(range(len(v)) for v in CATALOGO.values()), temperaturas)]


class OraculoCursoFalso:
    """Imita la interfaz pública de ``oraculo.Oraculo``: evaluar y validar."""

    def __init__(self):
        self.llamadas = []

    @staticmethod
    def _pasa(config, iid):
        return (config["rol"] + config["estilo"] + int(iid)) % 3 == 0

    def evaluar(self, config, instancias, semilla=1):
        self.llamadas.append((dict(config), [x["id"] for x in instancias], semilla))
        trazas = [{"id": x["id"], "violo": "familia:regla", "salida": "texto"}
                  for x in instancias if not self._pasa(config, x["id"])]
        return SimpleNamespace(precision=1 - len(trazas) / len(instancias), trazas=trazas, n=len(instancias))

    def validar(self, config, n=None, semilla=1):
        n = 10 if n is None else n
        return self.evaluar(config, [{"id": 1000 + j} for j in range(n)], semilla)


def crear(tmp_path, hardware="t4"):
    instancias = [{"id": i} for i in range(12)]
    return OraculoReal(OraculoCursoFalso(), instancias, hardware=hardware,
                       ruta_libro=ruta_libro_consultas(hardware, tmp_path),
                       catalogo=CATALOGO, temperaturas=TEMPERATURAS, espacio_fn=espacio_falso)


def test_usa_configuraciones_oficiales_y_resultados_del_curso(tmp_path):
    o = crear(tmp_path)
    x = o.config([1, 2], temperatura=0.3)
    r = o.evaluar(x)
    enviada = o.oraculo.llamadas[-1][0]
    assert enviada == {"rol": 1, "estilo": 2, "temperatura": 0.3}
    assert r.aciertos == sum(OraculoCursoFalso._pasa(x, i) for i in range(12))
    assert all(t["salida"] == "texto" for t in r.trazas)


def test_libro_cuenta_consultas_nuevas_y_persiste(tmp_path):
    o = crear(tmp_path)
    x = o.config([0, 1])
    assert o.evaluar(x).consultas_nuevas == 12
    assert o.evaluar(x).consultas_nuevas == 0
    assert o.evaluar(x, instancias=[{"id": 3}, {"id": 99}]).consultas_nuevas == 1
    assert o.evaluar(x, semilla=2).consultas_nuevas == 12
    assert o.consultas == 25

    otra = crear(tmp_path)                      # vuelve a leer el libro del disco
    assert otra.evaluar(x).consultas_nuevas == 0
    assert otra.consultas_hechas(x) == {str(i) for i in range(12)} | {"99"}


def test_registrar_consultas_previas(tmp_path):
    o = crear(tmp_path)
    x = o.config([1, 1])
    o.registrar_consultas(x, range(12))
    assert o.evaluar(x).consultas_nuevas == 0


def test_validar_cuenta_la_muestra_fija(tmp_path):
    o = crear(tmp_path)
    x = o.config([0, 0])
    assert o.validar(x, n=5).consultas_nuevas == 5
    assert o.validar(x, n=8).consultas_nuevas == 3
    assert o.validar(x, n=None).consultas_nuevas == 2
    assert o.validar(x, n=4).consultas_nuevas == 0


def test_costo_por_consulta_solo_con_evaluaciones_nuevas(tmp_path):
    o = crear(tmp_path)
    x = o.config([0, 2])
    o.evaluar(x)
    o.evaluar(x)
    costo = o.costo_por_consulta()
    assert costo["evaluaciones"] == 1 and costo["consultas"] == 12


def test_libro_de_otro_hardware_se_rechaza(tmp_path):
    o = crear(tmp_path, hardware="t4")
    o.evaluar(o.config([0, 0]))
    ruta = ruta_libro_consultas("t4", tmp_path)
    datos = json.loads(ruta.read_text(encoding="utf-8"))
    datos["hardware"] = "rtx-5050-laptop"
    ruta.write_text(json.dumps(datos), encoding="utf-8")
    with pytest.raises(RuntimeError):
        crear(tmp_path, hardware="t4")


def test_caches_separados_por_hardware(tmp_path):
    assert ruta_cache_oraculo("t4", tmp_path).name == "cache_oraculo.json"
    assert ruta_cache_oraculo("rtx-5050-laptop", tmp_path).name == "cache_oraculo_rtx-5050-laptop.json"
    assert ruta_libro_consultas("t4", tmp_path) != ruta_libro_consultas("cpu", tmp_path)


def test_etiquetas_y_verificacion_de_hardware():
    assert etiqueta_hardware("Tesla T4") == "t4"
    assert etiqueta_hardware("NVIDIA GeForce RTX 5050 Laptop GPU") == "rtx-5050-laptop"
    assert etiqueta_hardware(None) == "cpu"
    assert verificar_hardware("t4", "Tesla T4") == "t4"
    with pytest.raises(RuntimeError):
        verificar_hardware("t4", "NVIDIA GeForce RTX 5050 Laptop GPU")


# ---------------------------------------------------------------- Fase 7: tope, registro previo y subespacio

def test_tope_de_consultas_nuevas_se_respeta_antes_de_consultar(tmp_path):
    from oraculo_ada.oraculos.real import PresupuestoAgotado

    o = crear(tmp_path)
    o.limite_consultas_nuevas = 20
    o.evaluar(o.config([0, 0]))                     # 12 nuevas
    llamadas = len(o.oraculo.llamadas)
    with pytest.raises(PresupuestoAgotado):
        o.evaluar(o.config([1, 0]))                 # necesitaría 12 más: 24 > 20
    assert len(o.oraculo.llamadas) == llamadas      # no se consultó al modelo
    o.evaluar(o.config([0, 0]))                     # repetida: 0 nuevas, permitida


def test_registrar_primera_entrega(tmp_path):
    from oraculo_ada.oraculos.real import registrar_primera_entrega

    registro = tmp_path / "registro.csv"
    registro.write_text("paso,rol,estilo,temperatura\n1,0,1,0.0\n2,1,2,0.3\n", encoding="utf-8")
    o = crear(tmp_path)
    registrar_primera_entrega(o, registro, o.instancias, config_validada=o.config([0, 1]), n_validacion=10)
    assert o.evaluar(o.config([0, 1])).consultas_nuevas == 0
    assert o.evaluar(o.config([1, 2], temperatura=0.3)).consultas_nuevas == 0
    assert o.validar(o.config([0, 1]), n=None).consultas_nuevas == 0
    assert o.evaluar(o.config([1, 1])).consultas_nuevas == 12


def test_subespacio_delega_y_restringe(tmp_path):
    from oraculo_ada.algoritmos import fuerza_bruta
    from oraculo_ada.oraculos.subespacio import OraculoSubespacio, sortear_subespacio

    o = crear(tmp_path)
    opciones = sortear_subespacio(o, 2, semilla=3)
    assert opciones == sortear_subespacio(o, 2, semilla=3)
    assert all(len(v) == 2 and set(v) <= set(o.opciones[r]) for r, v in opciones.items())
    sub = OraculoSubespacio(o, opciones)
    r = fuerza_bruta(sub)
    assert r.configuraciones_evaluadas == 4 and r.consultas_cobradas == 4 * 12 == o.consultas
    excluida = next(a for a in o.opciones["estilo"] if a not in opciones["estilo"])   # estilo tiene 3 opciones
    with pytest.raises(ValueError):
        sub.evaluar({"rol": opciones["rol"][0], "estilo": excluida, "temperatura": 0.0})
