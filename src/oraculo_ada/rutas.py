"""Carpetas del proyecto.

Por defecto todo cuelga de la raíz del repositorio. Las variables de entorno
permiten apuntar a otra carpeta sin tocar el código, por ejemplo a Google Drive
cuando los experimentos corren en Colab (CLAUDE.md, regla 15):

- ``ORACULO_DIR_CACHE``: cachés del oráculo y libros de consultas (por defecto ``cache/``).
- ``ORACULO_DIR_RESULTADOS``: archivos de resultados (por defecto ``resultados/``).
- ``ORACULO_DIR_FIGURAS``: figuras generadas (por defecto ``figuras/``).
- ``ORACULO_OPEN_INSTRUCT``: clon de ``allenai/open-instruct``.
"""

import os
from pathlib import Path

# src/oraculo_ada/rutas.py → raíz del repositorio (instalación editable o PYTHONPATH=src).
RAIZ = Path(__file__).resolve().parents[2]


def _carpeta(variable, defecto):
    ruta = Path(os.environ.get(variable) or defecto)
    ruta.mkdir(parents=True, exist_ok=True)
    return ruta


def dir_cache():
    return _carpeta("ORACULO_DIR_CACHE", RAIZ / "cache")


def dir_resultados():
    return _carpeta("ORACULO_DIR_RESULTADOS", RAIZ / "resultados")


def dir_figuras():
    return _carpeta("ORACULO_DIR_FIGURAS", RAIZ / "figuras")


def preparar_modulos_del_curso():
    """Pone en ``sys.path`` la raíz del repositorio (``oraculo.py``, ``ayudas.py``) y
    open-instruct (verificadores), para importar el oráculo del curso sin modificarlo."""
    import sys

    oi = ruta_open_instruct()
    for ruta in (oi, RAIZ):
        if ruta and str(ruta) not in sys.path:
            sys.path.insert(0, str(ruta))
    return oi


def ruta_open_instruct():
    """Clon de open-instruct: variable de entorno, ``../open-instruct`` o ``/content/open-instruct``."""
    if os.environ.get("ORACULO_OPEN_INSTRUCT"):
        return Path(os.environ["ORACULO_OPEN_INSTRUCT"])
    for candidata in (RAIZ.parent / "open-instruct", Path("/content/open-instruct")):
        if candidata.exists():
            return candidata
    return None
