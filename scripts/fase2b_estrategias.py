"""Fase 2b: estrategias para escapar de los óptimos locales del Algoritmo 3 (sin GPU).

Dos pasos, separados por un commit (CLAUDE.md, regla 16):

    python scripts/fase2b_estrategias.py --plan      # escribe resultados/fase2b_plan.json
    git add resultados/fase2b_plan.json && git commit ...
    python scripts/fase2b_estrategias.py --correr    # exige el plan en git y sin cambios

``--correr`` lee los parámetros **del plan** (no de este archivo) y escribe
resultados/fase2b_estrategias.csv (una fila por corrida) y
resultados/fase2b_estrategias.json (resumen por variante y estrategia, comparación
pareada con la original y diagnóstico del estancamiento).

La métrica principal es el número de consultas cobradas; ``segundos_cpu`` es el
tiempo de CPU del oráculo sintético y no es tiempo de GPU.
"""

import argparse
import hashlib
import json
import statistics
import subprocess
import time
from collections import Counter

from oraculo_ada import rutas
from oraculo_ada.algoritmos import fuerza_bruta
from oraculo_ada.algoritmos.coordenadas import ascenso_coordenadas, reinicios
from oraculo_ada.oraculos import familia, generar_calibrado, generar_conjuntivo, generar_disyuntivo
from oraculo_ada.registro import cargar_resultado, guardar_csv, guardar_resultado, metadatos

RANURAS = ["rol", "estrategia", "formato", "estilo", "cierre"]
RUTA_PLAN = rutas.dir_resultados() / "fase2b_plan.json"

DOBLES = {"pares_muestra": 100, "n_preliminar": 20, "top": 5, "rondas": 2}
PLAN = {
    "descripcion": "Plan de la Fase 2b, escrito antes de correr: estrategias para escapar de óptimos locales "
                   "del Algoritmo 3, comparadas en el oráculo sintético",
    "fecha": None,
    "variantes": {
        "calibrado_24": {"generador": "generar_calibrado", "techo": 24,
                         "casos": "los primeros 30 candidatos válidos de resultados/calibracion_sintetico.json "
                                  "(lista_validos, en orden de la rejilla)", "num_casos": 30},
        "calibrado_28": {"generador": "generar_calibrado", "techo": 28,
                         "casos": "todos los candidatos válidos de resultados/calibracion_sintetico_28.json "
                                  "(25; la rejilla de calibración no se amplió)", "num_casos": 25},
        "disyuntivo": {"generador": "generar_disyuntivo", "m": 5, "k": 8, "n": 100, "interacciones": 10,
                       "casos": "semillas 1 a 30", "num_casos": 30},
        "sin_limpias": {"generador": "generar_conjuntivo", "m": 5, "k": 8, "n": 100, "familias": 14,
                        "limpias_por_ranura": 0, "interacciones": 10, "casos": "semillas 1 a 30", "num_casos": 30},
    },
    "configuracion_inicial": "primera opción de cada ranura (como en el problema real)",
    "parametros_comunes": {"max_pasadas": 3, "umbral_traza": 3, "semilla_consulta": 1, "probar_temperaturas": True},
    "estrategias": {
        "original": {},
        "sin_poda": {"poda": "ninguna"},
        "poda_por_pasada": {"poda": "por_pasada"},
        "umbral_6": {"umbral_traza": 6},
        "poda_por_instancias": {"criterio_poda": "instancias"},
        "desempate_trazas": {"desempate": "trazas"},
        "dos_ranuras": {"movimientos_dobles": DOBLES},
        "reinicios_5": {"reinicios": 5},
        "combinada": {"desempate": "trazas", "criterio_poda": "instancias"},
        "combinada_reinicios_5": {"desempate": "trazas", "criterio_poda": "instancias", "reinicios": 5},
        "combinada_dos_ranuras": {"desempate": "trazas", "criterio_poda": "instancias", "movimientos_dobles": DOBLES},
    },
    "semillas": {
        "reinicios": "random.Random(1000 + i), i = número del caso (1, 2, ...); el primer inicio es la "
                     "configuración inicial y los otros 4 se sortean",
        "movimientos_dobles": "semilla 2000 + i para el sorteo de pares y de la submuestra",
    },
    "metricas": ["precision final", "brecha con el óptimo exacto (fuerza bruta con verdad conocida)",
                 "encontró el óptimo", "consultas cobradas (métrica principal de costo)", "consultas solicitadas",
                 "evaluaciones", "segundos de CPU (no es tiempo de GPU)"],
    "resumen": "por variante y estrategia: media, desviación estándar, mínimo y máximo; comparación pareada "
               "con la original en el mismo caso (diferencia media y desviación; casos que mejoran, empatan o "
               "empeoran)",
    "diagnostico": "solo en las variantes calibradas, con la estrategia original: qué pasó con la opción limpia "
                   "de cada ranura (verdad del sintético, que los algoritmos no ven): mejoró, empató o empeoró al "
                   "evaluarla; si la poda la descartó y si el descarte se debió solo a instancias que ya "
                   "fallaban y cambiaron de familia",
    "criterio": "La Fase 2b es descriptiva: no elige estrategia. Una estrategia se considera prometedora si su "
                "precisión media supera a la original en las dos variantes calibradas; la elección final se hace "
                "en la Fase 5 con el mismo presupuesto de consultas.",
}


# ---------------------------------------------------------------- casos

def casos_de(nombre, var):
    if var["generador"] == "generar_calibrado":
        archivo = "calibracion_sintetico" if var["techo"] == 24 else f"calibracion_sintetico_{var['techo']}"
        validos = cargar_resultado(archivo)["datos"]["lista_validos"][:var["num_casos"]]
        return [(i, (lambda c=c: generar_calibrado(var["techo"], candidato=c)), c) for i, c in enumerate(validos, 1)]
    if var["generador"] == "generar_disyuntivo":
        return [(s, (lambda s=s: generar_disyuntivo(var["m"], var["k"], var["n"], s, interacciones=var["interacciones"],
                                                    ranuras=RANURAS)), {"semilla": s})
                for s in range(1, var["num_casos"] + 1)]
    return [(s, (lambda s=s: generar_conjuntivo(var["m"], var["k"], var["n"], s, familias=var["familias"],
                                                limpias_por_ranura=var["limpias_por_ranura"],
                                                interacciones=var["interacciones"], ranuras=RANURAS)), {"semilla": s})
            for s in range(1, var["num_casos"] + 1)]


def correr_estrategia(o, i, opciones, comunes):
    kw = {"max_pasadas": comunes["max_pasadas"], "umbral_traza": comunes["umbral_traza"],
          "semilla": comunes["semilla_consulta"], "probar_temperaturas": comunes["probar_temperaturas"]}
    opciones = dict(opciones)
    num = opciones.pop("reinicios", None)
    if "movimientos_dobles" in opciones:
        opciones["movimientos_dobles"] = {**opciones["movimientos_dobles"], "semilla": 2000 + i}
    kw.update(opciones)
    if num:
        r = reinicios(o, num, semilla_inicios=1000 + i, **kw)
        evaluaciones = sum(c.evaluaciones for c in r.corridas)
        return r.mejor_config, r.mejor_precision, r.consultas_cobradas, r.consultas_solicitadas, evaluaciones, r.mejor
    r = ascenso_coordenadas(o, **kw)
    return r.mejor_config, r.mejor_precision, r.consultas_cobradas, r.consultas_solicitadas, r.evaluaciones, r


# ---------------------------------------------------------------- diagnóstico

def diagnosticar(o, r, umbral):
    """Qué le pasó a la opción limpia de cada ranura en una corrida de la estrategia original."""
    limpias = o.opciones_limpias()
    acopladas = {o.ranuras[p] for par in o.parametros.get("pares_acoplados", []) for p in par["ranuras"]}
    eventos = Counter()
    for f in r.registro:
        ranura = f["ranura_probada"]
        if ranura not in limpias or f["precision_base"] is None or f["config"][ranura] not in limpias[ranura]:
            continue
        tipo = "acoplada" if ranura in acopladas else "libre"
        p, base = f["precision"], f["precision_base"]
        eventos[f"{tipo}_evaluada"] += 1
        eventos[f"{tipo}_{'mejora' if p > base else 'empata' if p == base else 'empeora'}"] += 1
        if f["nota"].startswith("descartada"):
            eventos[f"{tipo}_descartada"] += 1
            base_cfg = dict(f["config"], **{ranura: f["opcion_base"]})
            v_base, v_cand = o.veredictos_exactos(base_cfg), o.veredictos_exactos(f["config"])
            nuevos = Counter(familia(vc[1]) for vb, vc in zip(v_base, v_cand) if vb[0] and not vc[0])
            if not any(c >= umbral for c in nuevos.values()):
                eventos[f"{tipo}_descartada_solo_por_cambio_de_familia"] += 1
    final = r.mejor_config
    eventos["ranuras_en_limpia_al_final"] = sum(final[x] in limpias[x] for x in limpias)
    eventos["ranuras_libres_en_limpia_al_final"] = sum(final[x] in limpias[x] for x in limpias if x not in acopladas)
    eventos["ranuras_libres"] = sum(1 for x in limpias if x not in acopladas)
    return eventos


# ---------------------------------------------------------------- resumen

def estadisticos(valores):
    return {"n": len(valores), "media": statistics.fmean(valores),
            "desviacion": statistics.stdev(valores) if len(valores) > 1 else 0.0,
            "minimo": min(valores), "maximo": max(valores)}


def resumir(filas, estrategias):
    resumen = {}
    for variante in dict.fromkeys(f["variante"] for f in filas):
        por_caso = {}
        for f in filas:
            if f["variante"] == variante:
                por_caso.setdefault(f["estrategia"], {})[f["caso"]] = f
        base = por_caso["original"]
        resumen[variante] = {}
        for e in estrategias:
            fs = list(por_caso[e].values())
            difs = [por_caso[e][c]["precision"] - base[c]["precision"] for c in base]
            resumen[variante][e] = {
                "precision": estadisticos([f["precision"] for f in fs]),
                "brecha": estadisticos([f["brecha"] for f in fs]),
                "fraccion_optimo": sum(f["encontro_optimo"] for f in fs) / len(fs),
                "consultas_cobradas": estadisticos([f["consultas_cobradas"] for f in fs]),
                "segundos_cpu": estadisticos([f["segundos_cpu"] for f in fs]),
                "frente_a_original": {**estadisticos(difs), "mejora": sum(d > 1e-12 for d in difs),
                                      "empata": sum(abs(d) <= 1e-12 for d in difs),
                                      "empeora": sum(d < -1e-12 for d in difs)},
            }
    return resumen


# ---------------------------------------------------------------- pasos

def escribir_plan():
    plan = dict(PLAN, fecha=time.strftime("%Y-%m-%d %H:%M:%S"), metadatos=metadatos())
    RUTA_PLAN.write_text(json.dumps(plan, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"plan escrito en {RUTA_PLAN}; hacer commit antes de --correr")


def exigir_plan_en_git():
    rel = RUTA_PLAN.relative_to(rutas.RAIZ).as_posix()
    rastreado = subprocess.run(["git", "ls-files", "--error-unmatch", rel], cwd=rutas.RAIZ, capture_output=True)
    cambiado = subprocess.run(["git", "diff", "--quiet", "HEAD", "--", rel], cwd=rutas.RAIZ)
    if rastreado.returncode or cambiado.returncode:
        raise SystemExit("el plan debe estar en un commit y sin cambios antes de correr (regla 16)")
    commit = subprocess.run(["git", "log", "-1", "--format=%H", "--", rel], cwd=rutas.RAIZ,
                            capture_output=True, text=True).stdout.strip()
    contenido = RUTA_PLAN.read_bytes()
    return json.loads(contenido), {"commit_del_plan": commit, "sha256_del_plan": hashlib.sha256(contenido).hexdigest()}


def correr():
    plan, huella = exigir_plan_en_git()
    comunes, estrategias = plan["parametros_comunes"], plan["estrategias"]
    filas, diagnostico = [], {}
    for variante, var in plan["variantes"].items():
        casos = casos_de(variante, var)
        assert len(casos) == var["num_casos"], (variante, len(casos))
        diag = Counter()
        for i, generar, params in casos:
            optimo = fuerza_bruta(generar(), verdad_conocida=True).mejor_precision
            for nombre, opciones in estrategias.items():
                o = generar()
                t0 = time.perf_counter()
                config, p, cobradas, solicitadas, evaluaciones, detalle = correr_estrategia(o, i, opciones, comunes)
                segundos = time.perf_counter() - t0
                assert abs(p - o.precision_exacta(config)) < 1e-12   # sin ruido: lo medido es la verdad
                filas.append({"variante": variante, "caso": i, "parametros_caso": json.dumps(params),
                              "estrategia": nombre, "precision": p, "optimo": optimo, "brecha": round(optimo - p, 10),
                              "encontro_optimo": abs(optimo - p) < 1e-12, "consultas_cobradas": cobradas,
                              "consultas_solicitadas": solicitadas, "evaluaciones": evaluaciones,
                              "segundos_cpu": round(segundos, 4), "config": json.dumps(config)})
                if nombre == "original" and var["generador"] == "generar_calibrado":
                    diag += diagnosticar(o, detalle, comunes["umbral_traza"])
            print(f"{variante} caso {i}: listo")
        if diag:
            diagnostico[variante] = {"corridas": len(casos), **dict(sorted(diag.items()))}
    guardar_csv("fase2b_estrategias", filas)
    resumen = resumir(filas, list(estrategias))
    guardar_resultado(
        "fase2b_estrategias",
        descripcion="Fase 2b: estrategias para escapar de óptimos locales del Algoritmo 3 en el sintético "
                    "(métrica principal: consultas; segundos_cpu no es tiempo de GPU)",
        parametros={"plan": "resultados/fase2b_plan.json", **huella},
        semilla={"reinicios": "1000 + caso", "movimientos_dobles": "2000 + caso",
                 "consulta": comunes["semilla_consulta"]},
        datos={"resumen": resumen, "diagnostico_original": diagnostico, "corridas": len(filas)},
    )
    for variante, por_e in resumen.items():
        print(f"\n{variante}")
        for e, s in por_e.items():
            print(f"  {e:24s} precisión {s['precision']['media']:.3f} ± {s['precision']['desviacion']:.3f}  "
                  f"óptimo {s['fraccion_optimo']:.0%}  consultas {s['consultas_cobradas']['media']:7.0f}  "
                  f"vs original {s['frente_a_original']['media']:+.3f} "
                  f"({s['frente_a_original']['mejora']}/{s['frente_a_original']['empata']}/{s['frente_a_original']['empeora']})")
    print("\ndiagnóstico:", json.dumps(diagnostico, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    grupo = ap.add_mutually_exclusive_group(required=True)
    grupo.add_argument("--plan", action="store_true")
    grupo.add_argument("--correr", action="store_true")
    args = ap.parse_args()
    escribir_plan() if args.plan else correr()
