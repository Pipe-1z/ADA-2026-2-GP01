"""Fase 4: Successive Halving como estrategia, "dos ranuras con filtro por SH" y probabilidad
de eliminar a la mejor configuración (sin GPU).

Dos pasos separados por un commit (CLAUDE.md, regla 16):

    python scripts/fase4_estrategias.py --plan       # escribe resultados/fase4_plan.json
    git add resultados/fase4_plan.json && git commit ...
    python scripts/fase4_estrategias.py --correr     # lee el plan; exige que esté en git sin cambios

Escribe resultados/fase4_estrategias.{csv,json} y resultados/fase4_probabilidad_sh.{csv,json}.
Métrica principal: consultas cobradas (con caché). ``segundos_cpu`` no es tiempo de GPU.
"""

import argparse
import json
import statistics
import time

from oraculo_ada.algoritmos import (
    ascenso_coordenadas,
    cota_eliminar_mejor,
    dos_ranuras_sh,
    fuerza_bruta,
    muestra_configuraciones,
    sh_muestra,
    successive_halving,
    vecindario_doble,
)
from oraculo_ada.experimentos.casos import VARIANTES, casos_de
from oraculo_ada.experimentos.plan import escribir_plan, exigir_plan_en_git
from oraculo_ada.oraculos import generar_calibrado, generar_conjuntivo, generar_disyuntivo
from oraculo_ada.registro import guardar_csv, guardar_resultado

NOMBRE_PLAN = "fase4_plan"
PLAN = {
    "descripcion": "Plan de la Fase 4, escrito antes de correr: Successive Halving como estrategia de búsqueda, "
                   "dos ranuras con filtro por SH y probabilidad de eliminar a la mejor configuración",
    "estrategias": {
        "variantes": VARIANTES,
        "parametros_comunes": {"max_pasadas": 3, "umbral_traza": 3, "semilla_consulta": 1, "n": 100},
        "configuracion_inicial": "primera opción de cada ranura",
        "estrategias": {
            "original": {"tipo": "coordenadas"},
            "dos_ranuras": {"tipo": "coordenadas", "movimientos_dobles": {"pares_muestra": 100, "n_preliminar": 20,
                                                                          "top": 5, "rondas": 2}},
            "sh_512_n1": {"tipo": "sh_muestra", "M": 512, "n0": 1},
            "sh_4096_n1": {"tipo": "sh_muestra", "M": 4096, "n0": 1},
            "sh_4096_n4": {"tipo": "sh_muestra", "M": 4096, "n0": 4},
            "sh_todo_n1": {"tipo": "sh_muestra", "M": 32768, "n0": 1},
            "dos_ranuras_sh_n2": {"tipo": "dos_ranuras_sh", "n0": 2, "rondas": 2},
            "dos_ranuras_sh_n8": {"tipo": "dos_ranuras_sh", "n0": 8, "rondas": 2},
        },
        "semillas": {"muestra_de_configuraciones": "3000 + i", "permutacion_de_instancias": "4000 + i "
                     "(en dos_ranuras_sh, '4000 + i|ronda')", "movimientos_dobles": "2000 + i (como en la Fase 2b)",
                     "i": "número del caso"},
        "metricas": ["precision final (verdad: sin ruido)", "brecha con el óptimo", "encontró el óptimo",
                     "consultas cobradas (métrica principal)", "consultas solicitadas (sin reutilizar)",
                     "segundos de CPU (no es tiempo de GPU)"],
        "resumen": "por variante y estrategia: media, desviación, mínimo y máximo; comparación pareada con la "
                   "original (mejoran / empatan / empeoran)",
        "criterio": "Descriptiva: la elección con el mismo presupuesto es de la Fase 5.",
    },
    "probabilidad": {
        "casos": {
            "calibrado_24": "generar_calibrado(24) (el elegido de la calibración)",
            "calibrado_28": "generar_calibrado(28)",
            "disyuntivo": "generar_disyuntivo(5, 8, 100, 1, interacciones=10)",
            "sin_limpias": "generar_conjuntivo(5, 8, 100, 1, familias=14, limpias_por_ranura=0, interacciones=10)",
        },
        "conjuntos": {
            "muestra_512": {"descripcion": "512 configuraciones al azar (semilla 5000)", "n0": [1, 4]},
            "vecindario_doble": {"descripcion": "los 490 movimientos dobles desde el resultado del Algoritmo 3 "
                                                "original", "n0": [2, 8]},
        },
        "repeticiones": "semillas de permutación de instancias 1 a 200",
        "evento": "el ganador no es óptimo dentro del conjunto (pérdida > 0, con la verdad del sintético)",
        "metricas": ["frecuencia del evento y su error estándar", "pérdida media", "cota (Karnin, Koren y Somekh, "
                     "2013, con Hoeffding, 1963)"],
    },
}


def generar_caso_probabilidad(nombre):
    return {
        "calibrado_24": lambda: generar_calibrado(24),
        "calibrado_28": lambda: generar_calibrado(28),
        "disyuntivo": lambda: generar_disyuntivo(5, 8, 100, 1, interacciones=10,
                                                 ranuras=["rol", "estrategia", "formato", "estilo", "cierre"]),
        "sin_limpias": lambda: generar_conjuntivo(5, 8, 100, 1, familias=14, limpias_por_ranura=0, interacciones=10,
                                                  ranuras=["rol", "estrategia", "formato", "estilo", "cierre"]),
    }[nombre]


def est(valores):
    return {"n": len(valores), "media": statistics.fmean(valores),
            "desviacion": statistics.stdev(valores) if len(valores) > 1 else 0.0,
            "minimo": min(valores), "maximo": max(valores)}


def correr_estrategia(o, i, e, comunes):
    kw = {"max_pasadas": comunes["max_pasadas"], "umbral_traza": comunes["umbral_traza"],
          "semilla": comunes["semilla_consulta"]}
    if e["tipo"] == "coordenadas":
        extra = {}
        if "movimientos_dobles" in e:
            extra["movimientos_dobles"] = {**e["movimientos_dobles"], "semilla": 2000 + i}
        r = ascenso_coordenadas(o, **kw, **extra)
        return r.mejor_config, r.mejor_precision, r.consultas_cobradas, r.consultas_solicitadas
    if e["tipo"] == "sh_muestra":
        r = sh_muestra(o, e["M"], n0=e["n0"], semilla_muestra=3000 + i, semilla_instancias=4000 + i,
                       semilla=comunes["semilla_consulta"])
        return r.ganador, r.precision_ganador, r.consultas_cobradas, r.consultas_solicitadas
    r = dos_ranuras_sh(o, n0=e["n0"], rondas=e["rondas"], semilla_instancias=4000 + i, **kw)
    return r["mejor_config"], r["mejor_precision"], r["consultas_cobradas"], r["consultas_solicitadas"]


def correr_estrategias(plan):
    comunes, estrategias = plan["parametros_comunes"], plan["estrategias"]
    filas = []
    for variante, var in plan["variantes"].items():
        for i, generar, params in casos_de(var):
            optimo = fuerza_bruta(generar(), verdad_conocida=True).mejor_precision
            for nombre, e in estrategias.items():
                o = generar()
                t0 = time.perf_counter()
                config, p, cobradas, solicitadas = correr_estrategia(o, i, e, comunes)
                segundos = time.perf_counter() - t0
                assert abs(p - o.precision_exacta(config)) < 1e-12
                filas.append({"variante": variante, "caso": i, "parametros_caso": json.dumps(params),
                              "estrategia": nombre, "precision": p, "optimo": optimo, "brecha": round(optimo - p, 10),
                              "encontro_optimo": abs(optimo - p) < 1e-12, "consultas_cobradas": cobradas,
                              "consultas_solicitadas": solicitadas, "segundos_cpu": round(segundos, 4),
                              "config": json.dumps(config)})
            print(f"{variante} caso {i}: listo", flush=True)
    resumen = {}
    for variante in plan["variantes"]:
        base = {f["caso"]: f for f in filas if f["variante"] == variante and f["estrategia"] == "original"}
        resumen[variante] = {}
        for nombre in estrategias:
            fs = [f for f in filas if f["variante"] == variante and f["estrategia"] == nombre]
            difs = [f["precision"] - base[f["caso"]]["precision"] for f in fs]
            resumen[variante][nombre] = {
                "precision": est([f["precision"] for f in fs]), "brecha": est([f["brecha"] for f in fs]),
                "fraccion_optimo": sum(f["encontro_optimo"] for f in fs) / len(fs),
                "consultas_cobradas": est([f["consultas_cobradas"] for f in fs]),
                "consultas_solicitadas": est([f["consultas_solicitadas"] for f in fs]),
                "segundos_cpu": est([f["segundos_cpu"] for f in fs]),
                "frente_a_original": {**est(difs), "mejora": sum(d > 1e-12 for d in difs),
                                      "empata": sum(abs(d) <= 1e-12 for d in difs),
                                      "empeora": sum(d < -1e-12 for d in difs)},
            }
    return filas, resumen


def correr_probabilidad(plan, n=100):
    semillas = range(1, 201)
    filas, resumen = [], {}
    for nombre in plan["casos"]:
        generar = generar_caso_probabilidad(nombre)
        o = generar()
        base = ascenso_coordenadas(generar())
        conjuntos = {"muestra_512": muestra_configuraciones(o, 512, 5000),
                     "vecindario_doble": vecindario_doble(o, base.mejor_config)}
        for conjunto, candidatos in conjuntos.items():
            verdad = [o.precision_exacta(c) for c in candidatos]
            mejor = max(verdad)
            for n0 in plan["conjuntos"][conjunto]["n0"]:
                cota = cota_eliminar_mejor(verdad, n0, n)
                perdidas = []
                for s in semillas:
                    sh = successive_halving(o, candidatos, n0=n0, semilla_instancias=s, evaluar_ganador=False)
                    perdidas.append(mejor - o.precision_exacta(sh.ganador))
                frecuencia = sum(p > 1e-12 for p in perdidas) / len(perdidas)
                fila = {"caso": nombre, "conjunto": conjunto, "candidatos": len(candidatos), "n0": n0,
                        "mejor_del_conjunto": mejor, "optimos_en_el_conjunto": sum(abs(v - mejor) < 1e-12 for v in verdad),
                        "repeticiones": len(perdidas), "frecuencia_no_optimo": frecuencia,
                        "error_estandar": (frecuencia * (1 - frecuencia) / len(perdidas)) ** 0.5,
                        "perdida_media": statistics.fmean(perdidas), "perdida_maxima": max(perdidas),
                        "cota": cota["cota"], "cota_por_ronda": json.dumps([round(x, 6) for x in cota["por_ronda"]])}
                filas.append(fila)
                print(f"{nombre:13s} {conjunto:16s} n0={n0}: frecuencia {frecuencia:.3f}  pérdida media "
                      f"{fila['perdida_media']:.4f}  cota {cota['cota']:.3f}", flush=True)
    return filas


def correr():
    plan, huella = exigir_plan_en_git(NOMBRE_PLAN)
    prob = correr_probabilidad(plan["probabilidad"])
    guardar_csv("fase4_probabilidad_sh", prob)
    guardar_resultado("fase4_probabilidad_sh",
                      descripcion="Fase 4: probabilidad de que Successive Halving elimine a la mejor configuración "
                                  "(frecuencia observada frente a la cota)",
                      parametros=huella, semilla={"permutaciones": "1 a 200", "muestra_512": 5000},
                      datos={"filas": prob})
    filas, resumen = correr_estrategias(plan["estrategias"])
    guardar_csv("fase4_estrategias", filas)
    guardar_resultado("fase4_estrategias",
                      descripcion="Fase 4: Successive Halving como estrategia y dos ranuras con filtro por SH "
                                  "(métrica principal: consultas; segundos_cpu no es tiempo de GPU)",
                      parametros=huella, semilla=plan["estrategias"]["semillas"],
                      datos={"resumen": resumen, "corridas": len(filas)})
    for variante, por_e in resumen.items():
        print(f"\n{variante}")
        for e, s in por_e.items():
            print(f"  {e:20s} precisión {s['precision']['media']:.3f} ± {s['precision']['desviacion']:.3f}  "
                  f"óptimo {s['fraccion_optimo']:.0%}  consultas {s['consultas_cobradas']['media']:8.0f}  "
                  f"vs original {s['frente_a_original']['media']:+.3f} "
                  f"({s['frente_a_original']['mejora']}/{s['frente_a_original']['empata']}/{s['frente_a_original']['empeora']})")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--plan", action="store_true")
    g.add_argument("--correr", action="store_true")
    args = ap.parse_args()
    if args.plan:
        print("plan escrito en", escribir_plan(NOMBRE_PLAN, PLAN))
    else:
        correr()
