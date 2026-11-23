"""Fase 3: poda del Algoritmo 1 (backtracking con cota) frente a su peor caso (sin GPU).

Casos (los mismos de la Fase 2b, más dos familias propias de esta fase):
- peor_caso: generar_peor_caso_backtracking(5, 8, 100): la cota no poda nada.
- calibrado_24 (30 casos), calibrado_28 (25), disyuntivo (30) y sin_limpias (30): como en la Fase 2b.
- 3sat: fórmulas aleatorias con v ∈ {10, 12, 14, 16} variables, razón cláusulas/variables
  ∈ {2, 3, 4, 4.26, 5, 6} y semillas 1 a 10 (|C| = 2^v).

Para cada caso y cada orden de hijos ("indice" y "cota") se mide: nodos explorados,
hojas evaluadas y consultas, y su fracción frente al peor caso (sin poda). Cada
resultado se comprueba contra la fuerza bruta (verdad conocida).

Métrica principal: consultas (y nodos). ``segundos_cpu`` no es tiempo de GPU.
Escribe resultados/fase3_backtracking.csv y resultados/fase3_backtracking.json.
"""

import json
import statistics

from oraculo_ada.algoritmos import backtracking, fuerza_bruta
from oraculo_ada.oraculos import (
    generar_3sat,
    generar_calibrado,
    generar_conjuntivo,
    generar_disyuntivo,
    generar_peor_caso_backtracking,
)
from oraculo_ada.registro import cargar_resultado, guardar_csv, guardar_resultado

RANURAS = ["rol", "estrategia", "formato", "estilo", "cierre"]
ORDENES = ["indice", "cota"]
SAT = {"variables": [10, 12, 14, 16], "razones": [2, 3, 4, 4.26, 5, 6], "semillas": list(range(1, 11))}


def casos():
    yield "peor_caso", 1, {}, lambda: generar_peor_caso_backtracking(5, 8, 100, ranuras=RANURAS)
    for techo, archivo, num in ((24, "calibracion_sintetico", 30), (28, "calibracion_sintetico_28", 25)):
        for i, c in enumerate(cargar_resultado(archivo)["datos"]["lista_validos"][:num], 1):
            yield f"calibrado_{techo}", i, c, (lambda c=c, t=techo: generar_calibrado(t, candidato=c))
    for s in range(1, 31):
        yield "disyuntivo", s, {"semilla": s}, (lambda s=s: generar_disyuntivo(5, 8, 100, s, interacciones=10,
                                                                               ranuras=RANURAS))
    for s in range(1, 31):
        yield "sin_limpias", s, {"semilla": s}, (lambda s=s: generar_conjuntivo(
            5, 8, 100, s, familias=14, limpias_por_ranura=0, interacciones=10, ranuras=RANURAS))
    for v in SAT["variables"]:
        for razon in SAT["razones"]:
            for s in SAT["semillas"]:
                yield f"3sat_v{v}", s, {"variables": v, "razon": razon, "semilla": s}, \
                    (lambda v=v, r=razon, s=s: generar_3sat(v, r, s))


def est(valores):
    return {"n": len(valores), "media": statistics.fmean(valores),
            "desviacion": statistics.stdev(valores) if len(valores) > 1 else 0.0,
            "minimo": min(valores), "maximo": max(valores)}


def main():
    filas = []
    for familia_caso, i, params, generar in casos():
        optimo = fuerza_bruta(generar(), verdad_conocida=True).mejor_precision
        for orden in ORDENES:
            r = backtracking(generar(), orden_hijos=orden)
            assert abs(r.mejor_precision - optimo) < 1e-12, (familia_caso, i, orden)
            s = r.resumen()
            filas.append({"familia": familia_caso, "caso": i, "parametros_caso": json.dumps(params), "orden": orden,
                          "optimo": optimo, **{k: s[k] for k in (
                              "nodos_explorados", "nodos_peor_caso", "fraccion_nodos", "hojas_evaluadas",
                              "hojas_peor_caso", "fraccion_hojas", "cotas_calculadas", "consultas_cobradas",
                              "consultas_peor_caso", "fraccion_consultas", "segundos_cpu")},
                          "nodos_por_nivel": json.dumps(s["nodos_por_nivel"]),
                          "podados_por_nivel": json.dumps(s["podados_por_nivel"])})
        print(f"{familia_caso} {i} listo")

    grupos = {}
    for f in filas:
        clave = f["familia"] if not f["familia"].startswith("3sat") else \
            f"{f['familia']}_r{json.loads(f['parametros_caso'])['razon']}"
        grupos.setdefault((clave, f["orden"]), []).append(f)
    resumen = {}
    for (clave, orden), fs in grupos.items():
        resumen.setdefault(clave, {})[orden] = {
            "casos": len(fs), "nodos_peor_caso": fs[0]["nodos_peor_caso"], "hojas_peor_caso": fs[0]["hojas_peor_caso"],
            "consultas_peor_caso": fs[0]["consultas_peor_caso"],
            **{m: est([f[m] for f in fs]) for m in ("fraccion_nodos", "fraccion_hojas", "fraccion_consultas",
                                                    "nodos_explorados", "hojas_evaluadas", "consultas_cobradas",
                                                    "optimo", "segundos_cpu")},
            "nodos_por_nivel_medio": [statistics.fmean(json.loads(f["nodos_por_nivel"])[d] for f in fs)
                                      for d in range(len(json.loads(fs[0]["nodos_por_nivel"])))],
        }
    guardar_csv("fase3_backtracking", filas)
    guardar_resultado(
        "fase3_backtracking",
        descripcion="Fase 3: nodos explorados, hojas y consultas del Algoritmo 1 frente al peor caso sin poda "
                    "(métrica principal: consultas y nodos; segundos_cpu no es tiempo de GPU)",
        parametros={"ordenes": ORDENES, "sat": SAT, "semilla_consulta": 1,
                    "casos": "ver docstring de scripts/fase3_backtracking.py"},
        semilla={"sat": SAT["semillas"], "disyuntivo_y_sin_limpias": "1 a 30",
                 "calibrados": "lista_validos de la calibración"},
        datos={"resumen": resumen, "corridas": len(filas)},
    )
    for clave, por_orden in resumen.items():
        a, b = por_orden["indice"], por_orden["cota"]
        print(f"{clave:16s} |C|={a['hojas_peor_caso']:6d}  hojas evaluadas: índice {a['fraccion_hojas']['media']:.4f} "
              f"± {a['fraccion_hojas']['desviacion']:.4f}, cota {b['fraccion_hojas']['media']:.4f}  |  nodos: índice "
              f"{a['fraccion_nodos']['media']:.4f}, cota {b['fraccion_nodos']['media']:.4f}")


if __name__ == "__main__":
    main()
