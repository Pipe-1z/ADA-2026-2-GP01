"""Fase 0: verificación del entorno local contra el registro de la primera entrega.

El oráculo del curso se usa solo a través de su interfaz pública
(`Oraculo.evaluar`, `Oraculo.validar`, `espacio`, `CATALOGO`). El caché que
escribe (`cache/cache_oraculo.json`, copiado de Google Drive) se trata como un
archivo de datos: cada entrada es `[aprobada, restricción violada, salida]` y su
clave contiene el id de la instancia.

Partes, que se corren por separado:

  --parte cache   (sin GPU)
      A. Cada fila de resultados/registro_busqueda.csv se recalcula con
         `Oraculo.evaluar` leyendo el caché de la T4: misma precisión y mismos
         fallos por familia. También `Oraculo.validar` de la configuración final.
      B. Las salidas guardadas se vuelven a calificar con los verificadores de
         open-instruct de la versión indicada (procedimiento estándar de IFEval).
         El caché recalificado se guarda en cache/ y con él se recalcula cada
         fila del registro (resultados/registro_busqueda_recalificado_<commit>.csv).

  --parte gpu     (usa el modelo real)
      C. Reevalúa (0,0,0,0,0) y (0,0,0,5,1), temperatura 0.0, sobre las 100
         instancias de búsqueda con un caché vacío (todo se genera de nuevo),
         con los parámetros del notebook de búsqueda (lote=16,
         presupuesto=32_000_000, semilla=1). Mide el tiempo y compara instancia
         por instancia con lo que generó la T4.

Uso, desde la raíz del repositorio, con PYTHONUTF8=1:

    python scripts/fase0_verificacion.py --parte cache
    python scripts/fase0_verificacion.py --parte gpu
    python scripts/fase0_verificacion.py --parte resumen   (sin GPU, después de las otras dos)
"""

import argparse
import csv
import json
import platform
import subprocess
import sys
import time
from collections import Counter
from pathlib import Path
from types import SimpleNamespace

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

RUTA_CACHE_T4 = RAIZ / "cache" / "cache_oraculo.json"
RUTA_REGISTRO = RAIZ / "resultados" / "registro_busqueda.csv"
NOMBRE_MODELO_T4 = "Qwen/Qwen3-1.7B"   # el que entra en las claves del caché de la T4

MODELO = "qwen17b"
SEMILLA = 1
LOTE = 16                  # igual que el notebook de búsqueda
PRESUPUESTO = 32_000_000   # igual que el notebook de búsqueda
CONFIGS_GPU = [
    {"rol": 0, "estrategia": 0, "formato": 0, "estilo": 0, "cierre": 0, "temperatura": 0.0},
    {"rol": 0, "estrategia": 0, "formato": 0, "estilo": 5, "cierre": 1, "temperatura": 0.0},
]
RANURAS = ["rol", "estrategia", "formato", "estilo", "cierre"]

# Se fijan en __main__.
RUTA_OPEN_INSTRUCT = RAIZ.parent / "open-instruct"
COMMIT_VERIFICADORES = None
SUFIJO = ""


# ---------------------------------------------------------------- utilidades

def _cmd(args, cwd=None):
    try:
        return subprocess.run(args, cwd=cwd, capture_output=True, text=True, check=True).stdout.strip()
    except Exception as e:  # noqa: BLE001 - solo se usa para metadatos
        return f"no disponible ({type(e).__name__})"


def commit_verificadores():
    return COMMIT_VERIFICADORES or _cmd(["git", "rev-parse", "HEAD"], cwd=RUTA_OPEN_INSTRUCT)


def metadatos():
    """Versión del código, de los verificadores y del hardware."""
    import torch
    import transformers

    mod = sys.modules.get("open_instruct.IFEvalG.instructions")
    meta = {
        "fecha": time.strftime("%Y-%m-%d %H:%M:%S"),
        "git_hash": _cmd(["git", "rev-parse", "HEAD"], cwd=RAIZ),
        "git_sucio": bool(_cmd(["git", "status", "--porcelain", "--untracked-files=no"], cwd=RAIZ)),
        "open_instruct_hash": commit_verificadores(),
        "open_instruct_importado_desde": getattr(mod, "__file__", None),
        "python": platform.python_version(),
        "sistema": platform.platform(),
        "torch": torch.__version__,
        "cuda_torch": torch.version.cuda,
        "transformers": transformers.__version__,
    }
    if torch.cuda.is_available():
        meta["gpu"] = torch.cuda.get_device_name(0)
        meta["gpu_capacidad"] = ".".join(map(str, torch.cuda.get_device_capability(0)))
        meta["gpu_memoria_gb"] = round(torch.cuda.get_device_properties(0).total_memory / 1e9, 2)
        meta["driver"] = _cmd(["nvidia-smi", "--query-gpu=driver_version", "--format=csv,noheader"])
    else:
        meta["gpu"] = None
    return meta


def familia(violo):
    return str(violo).split(":")[0]


def id_de_clave(clave):
    return clave.split("|")[2]


def cargar_particiones():
    from ayudas import cargar_datos, dividir

    return dividir(cargar_datos(str(RAIZ / "datos_visibles.json")))


_INDICE = {}


def config_oficial(fila_o_dict):
    """La config tal como la arma espacio(), a partir de índices y temperatura."""
    from oraculo import TEMPERATURAS, espacio

    if not _INDICE:
        _INDICE.update({tuple(c[r] for r in RANURAS) + (c["temperatura"],): c for c in espacio(TEMPERATURAS)})
    clave = tuple(int(fila_o_dict[r]) for r in RANURAS) + (float(fila_o_dict["temperatura"]),)
    return _INDICE[clave]


def oraculo_desde_cache(ruta_cache, busqueda, validacion):
    """Oraculo del curso sin modelo: solo responde lo que ya está en el caché."""
    from oraculo import Oraculo

    sin_modelo = SimpleNamespace(
        red=None,
        tok=SimpleNamespace(pad_token="<pad>", eos_token="<eos>", chat_template=""),
        nombre=NOMBRE_MODELO_T4,
    )
    return Oraculo(sin_modelo, busqueda, validacion, cache=str(ruta_cache))


def calificar(instancia, salida):
    """Procedimiento estándar de IFEval con los verificadores de open-instruct.

    Devuelve (1, None) si la salida cumple todas las restricciones, o
    (0, id de la primera restricción incumplida).
    """
    from open_instruct.IFEvalG import instructions_registry as reg

    for iid, kw in zip(instancia["ids"], instancia["kwargs"]):
        verificador = reg.INSTRUCTION_DICT[iid](iid)
        verificador.build_description(**kw)
        args = verificador.get_instruction_args()
        if args and "prompt" in args:
            verificador.build_description(prompt=instancia["prompt"])
        if not verificador.check_following(salida):
            return 0, iid
    return 1, None


def precision_y_fallos(res):
    return res.precision, dict(Counter(familia(t["violo"]) for t in res.trazas))


def guardar_json(nombre, datos):
    ruta = RAIZ / "resultados" / nombre
    ruta.write_text(json.dumps(datos, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"→ {ruta.relative_to(RAIZ)}")


# ---------------------------------------------------------------- parte cache

def parte_cache():
    busqueda, validacion = cargar_particiones()
    instancias = {str(x["id"]): x for x in busqueda + validacion}
    with open(RUTA_REGISTRO, encoding="utf-8") as f:
        filas = list(csv.DictReader(f))
    final = config_oficial(CONFIGS_GPU[1])

    # A. registro ↔ caché de la T4, con la interfaz pública
    o_t4 = oraculo_desde_cache(RUTA_CACHE_T4, busqueda, validacion)
    discrepancias_a = []
    for fila in filas:
        p, fallos = precision_y_fallos(o_t4.evaluar(config_oficial(fila), busqueda, semilla=SEMILLA))
        if abs(p - float(fila["precision"])) > 1e-9 or fallos != json.loads(fila["fallos_por_familia"]):
            discrepancias_a.append({"paso": int(fila["paso"]), "precision_cache": p,
                                    "precision_registro": float(fila["precision"])})
    val_t4 = o_t4.validar(final, n=None, semilla=SEMILLA)

    # B. recalificar todas las salidas con la versión indicada de los verificadores
    cache_t4 = json.loads(RUTA_CACHE_T4.read_text(encoding="utf-8"))
    commit = commit_verificadores()
    recalificado, cambios = {}, []
    t0 = time.time()
    for clave, (r, violo, salida) in cache_t4.items():
        r2, violo2 = calificar(instancias[id_de_clave(clave)], salida)
        recalificado[clave] = [r2, violo2, salida]
        if (r2, violo2) != (r, violo):
            cambios.append({"clave": clave, "instancia": id_de_clave(clave), "t4": [r, violo], "nuevo": [r2, violo2]})
    seg_b = time.time() - t0
    ruta_recal = RAIZ / "cache" / f"cache_oraculo_recalificado_{commit[:7]}.json"
    ruta_recal.write_text(json.dumps(recalificado), encoding="utf-8")

    o_nuevo = oraculo_desde_cache(ruta_recal, busqueda, validacion)
    filas_nuevas, filas_que_cambian = [], []
    for fila in filas:
        p, fallos = precision_y_fallos(o_nuevo.evaluar(config_oficial(fila), busqueda, semilla=SEMILLA))
        nueva = {"paso": int(fila["paso"]), "fase": fila["fase"], **{r: int(fila[r]) for r in RANURAS},
                 "temperatura": float(fila["temperatura"]), "precision_registro_t4": float(fila["precision"]),
                 f"precision_{commit[:7]}": p, "fallos_por_familia": json.dumps(dict(sorted(fallos.items(), key=lambda x: -x[1])))}
        filas_nuevas.append(nueva)
        if abs(p - float(fila["precision"])) > 1e-9:
            filas_que_cambian.append({k: nueva[k] for k in nueva if k != "fallos_por_familia"})
    val_nuevo = o_nuevo.validar(final, n=None, semilla=SEMILLA)

    if not SUFIJO:
        ruta_csv = RAIZ / "resultados" / f"registro_busqueda_recalificado_{commit[:7]}.csv"
        with open(ruta_csv, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(filas_nuevas[0]))
            w.writeheader()
            w.writerows(filas_nuevas)
        print(f"→ {ruta_csv.relative_to(RAIZ)}")

    mejor_t4 = max(filas, key=lambda x: float(x["precision"]))
    mejor_nuevo = max(filas_nuevas, key=lambda x: x[f"precision_{commit[:7]}"])
    resultado = {
        "descripcion": "Fase 0, parte sin GPU: registro vs caché de la T4 y recalificación de las salidas guardadas",
        "metadatos": metadatos(),
        "parametros": {"semilla": SEMILLA, "modelo": NOMBRE_MODELO_T4,
                       "cache": RUTA_CACHE_T4.relative_to(RAIZ).as_posix(), "verificadores": commit},
        "A_registro_vs_cache_t4": {
            "filas_registro": len(filas),
            "configuraciones_distintas_en_registro": len({tuple(f[r] for r in RANURAS + ["temperatura"]) for f in filas}),
            "respuestas_en_cache": len(cache_t4),
            "filas_con_discrepancia": discrepancias_a,
            "validacion_final": {"aciertos": round(val_t4.precision * val_t4.n), "instancias": val_t4.n,
                                 "precision": val_t4.precision},
        },
        "B_recalificacion": {
            "salidas_recalificadas": len(cache_t4),
            "veredictos_distintos": len(cambios),
            "distintos_por_restriccion": dict(Counter(e["t4"][1] or e["nuevo"][1] for e in cambios).most_common()),
            "instancias_afectadas": sorted({e["instancia"] for e in cambios}, key=int),
            "distintos": cambios,
            "filas_registro_que_cambian": filas_que_cambian,
            "mejor_fila_t4": {"paso": int(mejor_t4["paso"]), "precision": float(mejor_t4["precision"])},
            "mejor_fila_recalificada": {"paso": mejor_nuevo["paso"], "precision": mejor_nuevo[f"precision_{commit[:7]}"]},
            "validacion_final": {"aciertos": round(val_nuevo.precision * val_nuevo.n), "instancias": val_nuevo.n,
                                 "precision": val_nuevo.precision},
            "cache_recalificado": ruta_recal.relative_to(RAIZ).as_posix(),
            "segundos": round(seg_b, 1),
        },
    }
    guardar_json(f"fase0_verificacion_cache{SUFIJO}.json", resultado)
    print(json.dumps({"A": {k: v for k, v in resultado["A_registro_vs_cache_t4"].items()},
                      "B": {k: v for k, v in resultado["B_recalificacion"].items()
                            if k not in ("distintos", "filas_registro_que_cambian")}}, indent=1, ensure_ascii=False))


# ---------------------------------------------------------------- parte gpu

def parte_gpu():
    import torch
    from ayudas import cargar_modelo
    from oraculo import Oraculo

    busqueda, validacion = cargar_particiones()
    instancias = {str(x["id"]): x for x in busqueda}
    cache_t4 = json.loads(RUTA_CACHE_T4.read_text(encoding="utf-8"))

    t0 = time.time()
    modelo = cargar_modelo(MODELO)
    seg_carga = time.time() - t0
    vram_modelo = torch.cuda.memory_allocated() / 1e9
    assert modelo.nombre == NOMBRE_MODELO_T4

    comparaciones = []
    for i, config in enumerate(CONFIGS_GPU):
        c = config_oficial(config)
        ruta = RAIZ / "cache" / f"cache_fase0_local_c{i}.json"
        ruta.unlink(missing_ok=True)          # caché vacío: todo se genera de nuevo
        oraculo = Oraculo(modelo, busqueda, validacion, cache=str(ruta), lote=LOTE, presupuesto=PRESUPUESTO)
        torch.cuda.reset_peak_memory_stats()
        torch.cuda.synchronize()
        t0 = time.time()
        r = oraculo.evaluar(c, busqueda, semilla=SEMILLA)
        torch.cuda.synchronize()
        seg = time.time() - t0

        local = json.loads(ruta.read_text(encoding="utf-8"))   # las mismas claves que en el caché de la T4
        assert len(local) == len(busqueda) and all(k in cache_t4 for k in local)
        filas = []
        for k, (rl, vl, sl) in local.items():
            rt, vt, st = cache_t4[k]
            filas.append({"instancia": id_de_clave(k), "local": [rl, vl], "t4": [rt, vt], "misma_salida": sl == st,
                          "recalificada_local": list(calificar(instancias[id_de_clave(k)], sl))})
        p_t4 = sum(f["t4"][0] for f in filas) / len(filas)
        comp = {
            "config": {k: c[k] for k in RANURAS + ["temperatura"]},
            "precision_local": r.precision,
            "precision_t4_registro": p_t4,
            "coincide_precision": abs(r.precision - p_t4) < 1e-9,
            "instancias": len(filas),
            "mismo_veredicto": sum(f["local"][0] == f["t4"][0] for f in filas),
            "misma_restriccion_violada": sum(f["local"] == f["t4"] for f in filas),
            "misma_salida_texto": sum(f["misma_salida"] for f in filas),
            "calificar_coincide_con_oraculo": sum(f["recalificada_local"] == f["local"] for f in filas),
            "pasa_local_falla_t4": [f["instancia"] for f in filas if f["local"][0] and not f["t4"][0]],
            "falla_local_pasa_t4": [f["instancia"] for f in filas if f["t4"][0] and not f["local"][0]],
            "fallos_familia_local": dict(Counter(familia(f["local"][1]) for f in filas if not f["local"][0]).most_common()),
            "fallos_familia_t4": dict(Counter(familia(f["t4"][1]) for f in filas if not f["t4"][0]).most_common()),
            "consultas": len(filas),
            "segundos": round(seg, 1),
            "segundos_por_consulta": round(seg / len(filas), 3),
            "vram_pico_gb": round(torch.cuda.max_memory_allocated() / 1e9, 2),
            "cache_local": ruta.relative_to(RAIZ).as_posix(),
        }
        comparaciones.append(comp)
        print(f"{comp['config']}: local {r.precision:.1%} vs T4 {p_t4:.1%} | veredicto igual "
              f"{comp['mismo_veredicto']}/{len(filas)} | texto igual {comp['misma_salida_texto']}/{len(filas)} | "
              f"{seg:.0f} s ({comp['segundos_por_consulta']} s/consulta)")

    total_seg = sum(c["segundos"] for c in comparaciones)
    total_q = sum(c["consultas"] for c in comparaciones)
    resultado = {
        "descripcion": "Fase 0, parte GPU: reevaluación sin caché de dos configuraciones del registro",
        "metadatos": metadatos(),
        "parametros": {"modelo": modelo.nombre, "semilla": SEMILLA, "lote": LOTE, "presupuesto": PRESUPUESTO,
                       "cache_inicial": "vacío"},
        "segundos_carga_modelo": round(seg_carga, 1),
        "vram_modelo_gb": round(vram_modelo, 2),
        "comparaciones": comparaciones,
        "costo_medido": {"consultas": total_q, "segundos": round(total_seg, 1),
                         "segundos_por_consulta": round(total_seg / total_q, 3),
                         "nota": "tiempo de evaluar() con caché vacío, sin la carga del modelo"},
    }
    guardar_json(f"fase0_verificacion_gpu{SUFIJO}.json", resultado)


# ---------------------------------------------------------------- parte resumen

def parte_resumen():
    """Sin GPU: separa el efecto de los verificadores del efecto del hardware.

    Compara, para las configuraciones de la parte gpu, la calificación de la T4
    original, la de la T4 recalificada con los verificadores de referencia y la
    de la GPU local (calificada con esos mismos verificadores).
    """
    gpu = json.loads((RAIZ / "resultados" / "fase0_verificacion_gpu.json").read_text(encoding="utf-8"))
    cache_res = json.loads((RAIZ / "resultados" / "fase0_verificacion_cache.json").read_text(encoding="utf-8"))
    commit = cache_res["parametros"]["verificadores"]
    assert gpu["metadatos"]["open_instruct_hash"] == commit, "la parte gpu usó otros verificadores"
    cache_t4 = json.loads(RUTA_CACHE_T4.read_text(encoding="utf-8"))
    recal = json.loads((RAIZ / cache_res["B_recalificacion"]["cache_recalificado"]).read_text(encoding="utf-8"))

    filas = []
    for comp in gpu["comparaciones"]:
        local = json.loads((RAIZ / comp["cache_local"]).read_text(encoding="utf-8"))
        n = len(local)
        pasa = {nombre: {id_de_clave(k) for k in local if fuente[k][0]}
                for nombre, fuente in (("t4_original", cache_t4), ("t4_recalificada", recal), ("local", local))}
        filas.append({
            "config": comp["config"],
            "instancias": n,
            "precision_t4_original": len(pasa["t4_original"]) / n,
            "precision_t4_recalificada": len(pasa["t4_recalificada"]) / n,
            "precision_local": len(pasa["local"]) / n,
            "efecto_verificadores": {"pasan_solo_en_t4_original": sorted(pasa["t4_original"] - pasa["t4_recalificada"], key=int),
                                     "pasan_solo_en_t4_recalificada": sorted(pasa["t4_recalificada"] - pasa["t4_original"], key=int)},
            "efecto_hardware": {"pasan_solo_en_local": sorted(pasa["local"] - pasa["t4_recalificada"], key=int),
                                "pasan_solo_en_t4_recalificada": sorted(pasa["t4_recalificada"] - pasa["local"], key=int),
                                "salidas_texto_identicas": comp["misma_salida_texto"]},
            "segundos_por_consulta_local": comp["segundos_por_consulta"],
        })
    resultado = {
        "descripcion": "Fase 0, resumen: efecto de los verificadores y del hardware en (0,0,0,0,0) y (0,0,0,5,1)",
        "metadatos": metadatos(),
        "verificadores_referencia": commit,
        "hardware_local": gpu["metadatos"]["gpu"],
        "configuraciones": filas,
        "costo_local": gpu["costo_medido"],
    }
    guardar_json("fase0_resumen.json", resultado)
    print(json.dumps(filas, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--parte", choices=["cache", "gpu", "resumen"], required=True)
    ap.add_argument("--open-instruct", default=None,
                    help="carpeta de open-instruct a usar (por defecto ../open-instruct)")
    ap.add_argument("--commit-verificadores", default=None,
                    help="commit de open-instruct de esa carpeta, si no es un clon de git")
    ap.add_argument("--sufijo", default="", help="sufijo para el archivo de resultados")
    args = ap.parse_args()
    if args.open_instruct:
        RUTA_OPEN_INSTRUCT = Path(args.open_instruct).resolve()
    sys.path.insert(0, str(RUTA_OPEN_INSTRUCT))
    COMMIT_VERIFICADORES = args.commit_verificadores
    SUFIJO = args.sufijo
    {"cache": parte_cache, "gpu": parte_gpu, "resumen": parte_resumen}[args.parte]()
