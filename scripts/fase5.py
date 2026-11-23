"""Fase 5: Algoritmo 4 (reparto uniforme, Successive Halving y UCB1 con el mismo presupuesto B) y
elección de la estrategia de mejora para la Fase 7 con el mismo presupuesto (sin GPU).

Pasos (CLAUDE.md, regla 16):

    python scripts/fase5.py --plan                          # resultados/fase5_plan.json
    git add resultados/fase5_plan.json && git commit ...
    python scripts/fase5.py --correr reparto                # Algoritmo 4
    python scripts/fase5.py --correr estrategias            # elección para la Fase 7

Escribe resultados/fase5_reparto.{csv,json} y resultados/fase5_estrategias.{csv,json}.
Métrica principal: consultas (el presupuesto B se cuenta en consultas nuevas, con caché).
``segundos_cpu`` no es tiempo de GPU.
"""

import argparse
import json
import math
import statistics
import time

from oraculo_ada.algoritmos import (
    ascenso_coordenadas,
    costo_sh,
    dos_ranuras_sh,
    fuerza_bruta,
    muestra_configuraciones,
    vecindario_doble,
)
from oraculo_ada.algoritmos.coordenadas import reinicios
from oraculo_ada.algoritmos.reparto import ESQUEMAS
from oraculo_ada.experimentos.casos import VARIANTES, casos_de
from oraculo_ada.experimentos.plan import escribir_plan, exigir_plan_en_git
from oraculo_ada.registro import guardar_csv, guardar_resultado

NOMBRE_PLAN = "fase5_plan"
COMUNES = {"max_pasadas": 3, "umbral_traza": 3, "semilla_consulta": 1, "n": 100}
PLAN = {
    "descripcion": "Plan de la Fase 5, escrito antes de correr",
    "reparto": {
        "objetivo": "Algoritmo 4: comparar reparto uniforme, Successive Halving con presupuesto y UCB1 con el "
                    "mismo presupuesto B (consultas nuevas), para varios B",
        "casos": "los 3 primeros casos de cada variante de oraculo_ada.experimentos.casos.VARIANTES "
                 "(calibrado_24, calibrado_28, disyuntivo, sin_limpias)",
        "num_casos_por_variante": 3,
        "conjuntos": {"muestra_128": "128 configuraciones al azar (semilla 6000 + i)",
                      "vecindario_doble": "los 490 movimientos dobles desde el resultado del Algoritmo 3 original"},
        "presupuestos": "B = b · |S| con b ∈ {2, 4, 8, 16, 32}",
        "multiplicadores": [2, 4, 8, 16, 32],
        "repeticiones": "semillas de permutación de instancias 1 a 100",
        "esquemas": {"uniforme": "m = min(⌊B/|S|⌋, n) instancias por configuración",
                     "successive_halving": "mayor n0 con Q_con(|S|, n0, n) <= B; no factible si n0 = 1 no alcanza",
                     "ucb1": "Auer, Cesa-Bianchi y Fischer (2002), Figura 1; recomienda el brazo más jugado"},
        "metricas": ["probabilidad de elegir una configuración óptima dentro de S (verdad del sintético)",
                     "simple regret = Acc*(S) − Acc(elegida)", "consultas usadas", "factibilidad"],
    },
    "estrategias": {
        "objetivo": "elegir la estrategia de mejora que se aplicará con el modelo real en la Fase 7, comparando "
                    "con el mismo presupuesto",
        "variantes": VARIANTES,
        "parametros_comunes": COMUNES,
        "estrategias": {
            "original": {"tipo": "coordenadas"},
            "dos_ranuras": {"tipo": "coordenadas", "movimientos_dobles": {"pares_muestra": 100, "n_preliminar": 20,
                                                                          "top": 5, "rondas": 2}},
            "reinicios": {"tipo": "reinicios", "num_inicios": 20},
            "dos_ranuras_sh_n2_r1": {"tipo": "dos_ranuras_sh", "n0": 2, "rondas": 1},
            "dos_ranuras_sh_n4_r1": {"tipo": "dos_ranuras_sh", "n0": 4, "rondas": 1},
            "dos_ranuras_sh_n8_r1": {"tipo": "dos_ranuras_sh", "n0": 8, "rondas": 1},
            "dos_ranuras_sh_n2_r2": {"tipo": "dos_ranuras_sh", "n0": 2, "rondas": 2},
            "dos_ranuras_sh_n4_r2": {"tipo": "dos_ranuras_sh", "n0": 4, "rondas": 2},
            "dos_ranuras_sh_n8_r2": {"tipo": "dos_ranuras_sh", "n0": 8, "rondas": 2},
        },
        "semillas": {"reinicios": "1000 + i (el primer inicio es la configuración inicial)",
                     "movimientos_dobles": "2000 + i", "permutacion_de_instancias": "'4000 + i|ronda'",
                     "i": "número del caso"},
        "mismo_presupuesto": "cada estrategia corre completa; se registra la trayectoria (consultas nuevas "
                             "acumuladas, mejor precisión entre las configuraciones evaluadas sobre las n "
                             "instancias) y se corta en cada presupuesto B",
        "presupuestos": [5000, 7500, 10000, 15000, 20000, 30000],
        "presupuesto_de_eleccion": 15000,
        "criterio_de_eleccion": "Con B* = 15.000 consultas: (1) elegibles las estrategias cuya mejora media "
                                "pareada frente a la original es >= 0 en las cuatro variantes; (2) entre ellas, "
                                "la de mayor promedio, sobre las cuatro variantes con igual peso (dos calibradas y "
                                "dos teóricas), de la mejora media pareada; (3) si dos quedan a menos de 0,001, la "
                                "que usa menos consultas en promedio.",
        "estimacion_fase7": {
            "consultas": "consultas de la estrategia elegida por encima de las del Algoritmo 3 original (que en "
                         "el caso real ya están en el caché de la primera entrega), cortadas en B*, más 100 de la "
                         "evaluación pendiente (0,0,0,6,1); media, percentil 90 y máximo sobre los casos calibrados",
            "segundos_por_consulta": {"t4_primera_entrega": 2.1, "gpu_local_medida": 4.5,
                                      "nota": "2,1 s/consulta no tiene archivo de respaldo (regla 15); se reemplaza "
                                              "por la medición de la Fase 7"},
            "horas_efectivas_por_sesion_colab": 3,
            "nota_sesiones": "supuesto conservador para Colab gratuito (la duración real varía y no está "
                             "documentada); el usuario puede ajustarlo",
        },
    },
}


def est(valores):
    valores = list(valores)
    return {"n": len(valores), "media": statistics.fmean(valores),
            "desviacion": statistics.stdev(valores) if len(valores) > 1 else 0.0,
            "minimo": min(valores), "maximo": max(valores)}


# ---------------------------------------------------------------- Algoritmo 4

def correr_reparto(plan):
    filas = []
    for variante, var in VARIANTES.items():
        for i, generar, params in casos_de(var)[:plan["num_casos_por_variante"]]:
            o = generar()
            conjuntos = {"muestra_128": muestra_configuraciones(o, 128, 6000 + i),
                         "vecindario_doble": vecindario_doble(o, ascenso_coordenadas(generar()).mejor_config)}
            for nombre_conj, S in conjuntos.items():
                verdad = {o.clave(c): o.precision_exacta(c) for c in S}
                mejor = max(verdad.values())
                for b in plan["multiplicadores"]:
                    B = b * len(S)
                    for esquema, funcion in ESQUEMAS.items():
                        aciertos, regrets, consultas, factible, param = 0, [], [], True, None
                        for s in range(1, 101):
                            r = funcion(generar(), S, B, semilla_instancias=s, semilla=COMUNES["semilla_consulta"])
                            if not r.factible:
                                factible = False
                                break
                            reg = mejor - verdad[o.clave(r.elegido)]
                            regrets.append(reg)
                            aciertos += reg <= 1e-12
                            consultas.append(r.consultas_cobradas)
                            param = r.parametro
                        filas.append({
                            "variante": variante, "caso": i, "conjunto": nombre_conj, "tamano_S": len(S),
                            "multiplicador": b, "B": B, "esquema": esquema, "factible": factible,
                            "repeticiones": len(regrets), "mejor_de_S": mejor,
                            "prob_elegir_mejor": aciertos / len(regrets) if factible else None,
                            "regret_medio": statistics.fmean(regrets) if factible else None,
                            "regret_desviacion": statistics.stdev(regrets) if factible and len(regrets) > 1 else None,
                            "consultas_medias": statistics.fmean(consultas) if factible else None,
                            "parametro": json.dumps(param)})
                print(f"reparto {variante} caso {i} {nombre_conj}: listo", flush=True)
    resumen = {}
    for f in filas:
        if not f["factible"]:
            continue
        clave = f"{f['variante']}|{f['conjunto']}"
        resumen.setdefault(clave, {}).setdefault(f["esquema"], {}).setdefault(str(f["multiplicador"]), []).append(f)
    resumen = {c: {e: {b: {"casos": len(fs), "prob_elegir_mejor": est(x["prob_elegir_mejor"] for x in fs),
                           "regret_medio": est(x["regret_medio"] for x in fs),
                           "consultas_medias": est(x["consultas_medias"] for x in fs)}
                       for b, fs in por_b.items()} for e, por_b in por_e.items()} for c, por_e in resumen.items()}
    return filas, resumen


# ---------------------------------------------------------------- estrategias con el mismo presupuesto

def correr_estrategia(o, i, e):
    kw = {"max_pasadas": COMUNES["max_pasadas"], "umbral_traza": COMUNES["umbral_traza"],
          "semilla": COMUNES["semilla_consulta"]}
    if e["tipo"] == "coordenadas":
        extra = {"movimientos_dobles": {**e["movimientos_dobles"], "semilla": 2000 + i}} if "movimientos_dobles" in e else {}
        ascenso_coordenadas(o, **kw, **extra)
    elif e["tipo"] == "reinicios":
        reinicios(o, e["num_inicios"], semilla_inicios=1000 + i, **kw)
    else:
        dos_ranuras_sh(o, n0=e["n0"], rondas=e["rondas"], semilla_instancias=4000 + i, **kw)


def trayectoria(o):
    """[(consultas nuevas acumuladas, mejor precisión con evaluación completa hasta ahí)]."""
    puntos, acumuladas, mejor = [], 0, -1.0
    for h in o.historial:
        acumuladas += h["consultas_nuevas"]
        if h["instancias"] == o.n and not h.get("validacion"):
            mejor = max(mejor, h["aciertos"] / o.n)
            puntos.append((acumuladas, mejor))
    return puntos, acumuladas


def mejor_en(puntos, B):
    previos = [p for c, p in puntos if c <= B]
    return max(previos) if previos else 0.0


def correr_estrategias(plan):
    presupuestos = plan["presupuestos"]
    filas = []
    for variante, var in plan["variantes"].items():
        for i, generar, params in casos_de(var):
            optimo = fuerza_bruta(generar(), verdad_conocida=True).mejor_precision
            for nombre, e in plan["estrategias"].items():
                o = generar()
                t0 = time.perf_counter()
                correr_estrategia(o, i, e)
                segundos = time.perf_counter() - t0
                puntos, total = trayectoria(o)
                fila = {"variante": variante, "caso": i, "estrategia": nombre, "optimo": optimo,
                        "consultas_totales": total, "precision_final": puntos[-1][1], "segundos_cpu": round(segundos, 4)}
                for B in presupuestos:
                    fila[f"precision_B{B}"] = mejor_en(puntos, B)
                filas.append(fila)
            print(f"estrategias {variante} caso {i}: listo", flush=True)

    resumen = {}
    for variante in plan["variantes"]:
        base = {f["caso"]: f for f in filas if f["variante"] == variante and f["estrategia"] == "original"}
        resumen[variante] = {}
        for nombre in plan["estrategias"]:
            fs = [f for f in filas if f["variante"] == variante and f["estrategia"] == nombre]
            r = {"consultas_totales": est(f["consultas_totales"] for f in fs),
                 "precision_final": est(f["precision_final"] for f in fs), "por_presupuesto": {}}
            for B in presupuestos:
                difs = [f[f"precision_B{B}"] - base[f["caso"]][f"precision_B{B}"] for f in fs]
                r["por_presupuesto"][str(B)] = {
                    "precision": est(f[f"precision_B{B}"] for f in fs),
                    "fraccion_optimo": sum(abs(f[f"precision_B{B}"] - f["optimo"]) < 1e-12 for f in fs) / len(fs),
                    "mejora_frente_a_original": {**est(difs), "mejora": sum(d > 1e-12 for d in difs),
                                                 "empata": sum(abs(d) <= 1e-12 for d in difs),
                                                 "empeora": sum(d < -1e-12 for d in difs)}}
            resumen[variante][nombre] = r

    # elección según el criterio del plan
    Bs = str(plan["presupuesto_de_eleccion"])
    tabla = {}
    for nombre in plan["estrategias"]:
        if nombre == "original":
            continue
        mejoras = {v: resumen[v][nombre]["por_presupuesto"][Bs]["mejora_frente_a_original"]["media"] for v in resumen}
        tabla[nombre] = {"mejora_por_variante": mejoras, "elegible": all(m >= -1e-12 for m in mejoras.values()),
                         "promedio": statistics.fmean(mejoras.values()),
                         "consultas_medias": statistics.fmean(resumen[v][nombre]["consultas_totales"]["media"] for v in resumen)}
    elegibles = sorted((n for n in tabla if tabla[n]["elegible"]), key=lambda n: -tabla[n]["promedio"])
    elegida = None
    if elegibles:
        tope = tabla[elegibles[0]]["promedio"]
        cerca = [n for n in elegibles if tope - tabla[n]["promedio"] < 0.001]
        elegida = min(cerca, key=lambda n: tabla[n]["consultas_medias"])
    estimacion = estimar_fase7(plan, filas, elegida) if elegida else None
    return filas, resumen, {"tabla": tabla, "elegibles_en_orden": elegibles, "elegida": elegida,
                            "estimacion_fase7": estimacion}


def estimar_fase7(plan, filas, elegida):
    est7 = plan["estimacion_fase7"]
    Bstar = plan["presupuesto_de_eleccion"]
    extras = []
    for variante in ("calibrado_24", "calibrado_28"):
        base = {f["caso"]: f["consultas_totales"] for f in filas
                if f["variante"] == variante and f["estrategia"] == "original"}
        for f in filas:
            if f["variante"] == variante and f["estrategia"] == elegida:
                extras.append(min(f["consultas_totales"], Bstar) - base[f["caso"]])
    extras.sort()
    resumen_q = {"media": statistics.fmean(extras), "percentil_90": extras[math.ceil(0.9 * len(extras)) - 1],
                 "maximo": extras[-1], "casos": len(extras)}
    e = plan["estrategias"][elegida]
    detalle = {}
    if e["tipo"] == "dos_ranuras_sh":
        c = costo_sh(490, e["n0"], COMUNES["n"])
        detalle = {"consultas_exactas_por_ronda_de_filtro": c["con_reutilizar"] + c["completar_ganador"],
                   "nota": "cada ronda de filtro cuesta exactamente esto; el resto es el Algoritmo 3 que se corre "
                           "desde el ganador si se adopta"}
    horas_sesion = est7["horas_efectivas_por_sesion_colab"]
    escenarios = {}
    for nombre_q, q in (("media", resumen_q["media"] + 100), ("percentil_90", resumen_q["percentil_90"] + 100),
                        ("maximo", resumen_q["maximo"] + 100)):
        escenarios[nombre_q] = {"consultas_nuevas": q}
        for etiqueta, spc in (("t4_2_1_s", 2.1), ("local_4_5_s", 4.5)):
            horas = q * spc / 3600
            escenarios[nombre_q][etiqueta] = {"horas": horas, "sesiones": math.ceil(horas / horas_sesion)}
    return {"estrategia": elegida, "presupuesto_de_corte": Bstar, "consultas_extra_sintetico": resumen_q,
            "incluye_evaluacion_pendiente": 100, "escenarios": escenarios, "detalle": detalle,
            "horas_efectivas_por_sesion": horas_sesion, "supuestos": est7}


# ---------------------------------------------------------------- principal

def main():
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--plan", action="store_true")
    g.add_argument("--correr", choices=["reparto", "estrategias"])
    args = ap.parse_args()
    if args.plan:
        print("plan escrito en", escribir_plan(NOMBRE_PLAN, PLAN))
        return
    plan, huella = exigir_plan_en_git(NOMBRE_PLAN)
    if args.correr == "reparto":
        filas, resumen = correr_reparto(plan["reparto"])
        guardar_csv("fase5_reparto", filas)
        guardar_resultado("fase5_reparto", descripcion="Fase 5: Algoritmo 4, reparto uniforme, SH y UCB1 con el "
                          "mismo presupuesto B", parametros=huella,
                          semilla={"permutaciones": "1 a 100", "muestra_128": "6000 + i"},
                          datos={"resumen": resumen, "filas": len(filas)})
    else:
        filas, resumen, eleccion = correr_estrategias(plan["estrategias"])
        guardar_csv("fase5_estrategias", filas)
        guardar_resultado("fase5_estrategias", descripcion="Fase 5: estrategias de mejora con el mismo presupuesto "
                          "y elección para la Fase 7 (métrica: consultas; segundos_cpu no es tiempo de GPU)",
                          parametros=huella, semilla=plan["estrategias"]["semillas"],
                          datos={"resumen": resumen, "eleccion": eleccion, "corridas": len(filas)})
        print(json.dumps(eleccion, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
