"""Pruebas del registro de experimentos y del cronómetro."""

import json
import re
import time

from oraculo_ada import rutas
from oraculo_ada.medicion import Cronometro
from oraculo_ada.registro import cargar_resultado, guardar_csv, guardar_resultado, metadatos


def test_metadatos_traen_version_y_hardware():
    m = metadatos()
    assert re.fullmatch(r"[0-9a-f]{40}", m["git_hash"])
    assert isinstance(m["git_sucio"], bool)
    assert {"python", "sistema", "gpu"} <= set(m["hardware"])


def test_guardar_resultado_con_parametros_y_semilla(tmp_path):
    ruta = guardar_resultado("prueba", descripcion="d", parametros={"n": 3}, semilla=7,
                             datos={"x": [1, 2]}, directorio=tmp_path)
    contenido = json.loads(ruta.read_text(encoding="utf-8"))
    assert contenido["parametros"] == {"n": 3} and contenido["semilla"] == 7
    assert contenido["datos"] == {"x": [1, 2]} and "git_hash" in contenido["metadatos"]
    assert cargar_resultado("prueba", tmp_path) == contenido


def test_guardar_csv(tmp_path):
    ruta = guardar_csv("tabla", [{"a": 1, "b": "x"}, {"a": 2, "b": "y"}], directorio=tmp_path)
    assert ruta.read_text(encoding="utf-8").splitlines() == ["a,b", "1,x", "2,y"]


def test_carpetas_por_variable_de_entorno(tmp_path, monkeypatch):
    monkeypatch.setenv("ORACULO_DIR_RESULTADOS", str(tmp_path / "drive" / "resultados"))
    assert rutas.dir_resultados() == tmp_path / "drive" / "resultados"
    assert rutas.dir_resultados().is_dir()


def test_cronometro():
    with Cronometro() as c:
        time.sleep(0.01)
    assert c.segundos >= 0.009
