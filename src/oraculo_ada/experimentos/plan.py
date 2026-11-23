"""Planes de experimento escritos antes de correr (CLAUDE.md, regla 16).

``escribir_plan`` guarda el plan en ``resultados/``; ``exigir_plan_en_git`` se niega a
continuar si el plan no está en un commit o tiene cambios, y devuelve el plan junto
con el commit en que se fijó y su huella SHA-256, para guardarlos en el resultado.
"""

import hashlib
import json
import subprocess
import time

from .. import rutas
from ..registro import metadatos


def escribir_plan(nombre, plan):
    ruta = rutas.dir_resultados() / f"{nombre}.json"
    contenido = dict(plan, fecha=time.strftime("%Y-%m-%d %H:%M:%S"), metadatos=metadatos())
    ruta.write_text(json.dumps(contenido, indent=1, ensure_ascii=False), encoding="utf-8")
    return ruta


def exigir_plan_en_git(nombre):
    ruta = rutas.dir_resultados() / f"{nombre}.json"
    rel = ruta.relative_to(rutas.RAIZ).as_posix()
    rastreado = subprocess.run(["git", "ls-files", "--error-unmatch", rel], cwd=rutas.RAIZ, capture_output=True)
    cambiado = subprocess.run(["git", "diff", "--quiet", "HEAD", "--", rel], cwd=rutas.RAIZ)
    if not ruta.exists() or rastreado.returncode or cambiado.returncode:
        raise SystemExit(f"el plan {rel} debe estar en un commit y sin cambios antes de correr (regla 16)")
    commit = subprocess.run(["git", "log", "-1", "--format=%H", "--", rel], cwd=rutas.RAIZ,
                            capture_output=True, text=True).stdout.strip()
    contenido = ruta.read_bytes()
    return json.loads(contenido), {"plan": rel, "commit_del_plan": commit,
                                   "sha256_del_plan": hashlib.sha256(contenido).hexdigest()}
