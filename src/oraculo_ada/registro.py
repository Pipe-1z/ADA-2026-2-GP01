"""Registro de experimentos (CLAUDE.md, reglas 4 y 7).

Cada archivo de resultados guarda, además de los datos, los parámetros, la
semilla, la versión del código (hash de git y si había cambios sin commit), la
versión de los verificadores y el hardware. ``resultados/`` es la única fuente
de los números que aparecen en los documentos.
"""

import csv
import json
import subprocess
import time

from . import rutas
from .hardware import info_hardware


def _git(args, cwd):
    try:
        return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, check=True).stdout.strip()
    except Exception:  # noqa: BLE001 - sin git (p. ej. copia sin .git)
        return None


def metadatos():
    """Fecha, versión del código, versión de los verificadores y hardware."""
    oi = rutas.ruta_open_instruct()
    # "Sucio" se refiere al código: los cambios en resultados/ y figuras/ (lo que generan
    # los propios experimentos) no cuentan.
    estado = _git(["status", "--porcelain", "--untracked-files=no", "--", ".",
                   ":(exclude)resultados", ":(exclude)figuras"], rutas.RAIZ)
    return {
        "fecha": time.strftime("%Y-%m-%d %H:%M:%S"),
        "git_hash": _git(["rev-parse", "HEAD"], rutas.RAIZ),
        "git_sucio": None if estado is None else bool(estado),
        "open_instruct_hash": _git(["rev-parse", "HEAD"], oi) if oi else None,
        "hardware": info_hardware(),
    }


def guardar_resultado(nombre, *, descripcion, parametros, semilla, datos, directorio=None):
    """Escribe ``<directorio>/<nombre>.json`` y devuelve su ruta.

    ``semilla`` es obligatoria (regla 7); si el experimento no tiene azar, se pasa ``None``
    de forma explícita.
    """
    directorio = directorio or rutas.dir_resultados()
    ruta = directorio / f"{nombre}.json"
    contenido = {
        "descripcion": descripcion,
        "parametros": parametros,
        "semilla": semilla,
        "metadatos": metadatos(),
        "datos": datos,
    }
    ruta.write_text(json.dumps(contenido, indent=1, ensure_ascii=False), encoding="utf-8")
    return ruta


def cargar_resultado(nombre, directorio=None):
    directorio = directorio or rutas.dir_resultados()
    return json.loads((directorio / f"{nombre}.json").read_text(encoding="utf-8"))


def guardar_csv(nombre, filas, directorio=None):
    """Escribe una lista de diccionarios en ``<directorio>/<nombre>.csv``."""
    directorio = directorio or rutas.dir_resultados()
    ruta = directorio / f"{nombre}.csv"
    if not filas:
        raise ValueError("no hay filas para guardar")
    campos = list(dict.fromkeys(k for fila in filas for k in fila))   # unión de columnas, en orden de aparición
    with open(ruta, "w", newline="", encoding="utf-8") as f:
        escritor = csv.DictWriter(f, fieldnames=campos, restval="")
        escritor.writeheader()
        escritor.writerows(filas)
    return ruta
