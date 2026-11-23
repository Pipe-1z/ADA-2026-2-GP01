"""Fase 2: calibración del caso sintético que imita las estadísticas del problema real (sin GPU).

Objetivos y su fuente:

| Estadística | Objetivo | Fuente |
|---|---|---|
| Precisión de la configuración inicial (todas las ranuras en 0) | 9 % ± 1 punto | registro de la primera entrega: 9 % con los verificadores originales, 8 % con a4cd966 (resultados/registro_busqueda_recalificado_a4cd966.csv) |
| Óptimo | ≈ 24 % | documentación del curso (README_curso.md: "el techo está cerca del 24%") |
| Configuraciones al azar | promedio < 5 % | documentación del curso ("Una configuración al azar se queda debajo del 5%") |
| Instancias que ninguna configuración resuelve | fracción > 0 | consecuencia del techo de 24 % en el modelo conjuntivo |
| Algoritmo 3 desde la configuración inicial | termina en un óptimo local entre 13 % y 14 % | registro de la primera entrega (14 %; 13 % con a4cd966) |

Modelo fijo: conjuntivo, m = 5 ranuras, k = 8 opciones, n = 100 instancias, 14
familias (las que aparecen en las trazas reales), 2 o 3 familias por instancia,
una opción limpia por ranura (documentación del curso) y 76 instancias
insolubles. Con una opción limpia por ranura y los acoplamientos solo entre
opciones limpias, Acc* = 1 − 76/100 = 0,24 exactamente; se verifica por fuerza
bruta en el caso elegido.

Se recorre una rejilla de: probabilidad de que la opción 0 rompa cada familia
(``prob_rompe_opcion0``), probabilidad para las demás opciones no limpias
(``prob_rompe``), número de pares acoplados y semilla. Un candidato es válido si
cumple los cuatro primeros objetivos y el Algoritmo 3 termina en un óptimo local
dentro del rango; entre los válidos se elige el de precisión inicial más cercana
a 9 % y, en empate, el primero de la rejilla.

Escribe resultados/calibracion_sintetico.json y resultados/calibracion_sintetico_candidatos.csv.
"""

import itertools
import random
import statistics

from oraculo_ada.algoritmos import ascenso_coordenadas, fuerza_bruta
from oraculo_ada.medicion import Cronometro
from oraculo_ada.oraculos import generar_conjuntivo
from oraculo_ada.registro import guardar_csv, guardar_resultado

FIJOS = {"m": 5, "k": 8, "n": 100, "familias": 14, "familias_por_instancia": (2, 3),
         "limpias_por_ranura": 1, "fraccion_insoluble": 0.76}
REJILLA = {
    "prob_rompe_opcion0": [round(0.02 + 0.01 * i, 2) for i in range(11)],
    "prob_rompe": [0.15, 0.2, 0.25, 0.3, 0.35, 0.4],
    "pares_acoplados": [0, 1, 2],
    "semilla": list(range(1, 11)),
}
OBJETIVOS = {"precision_inicial": (0.08, 0.10), "precision_optima": (0.23, 0.25),
             "promedio_al_azar_menor_que": 0.05, "coordenadas": (0.13, 0.14)}
SEMILLA_MUESTRA = 2026           # muestra de configuraciones al azar
TAMANO_MUESTRA = 500
TAMANO_MUESTRA_FINAL = 5000
RANURAS = ["rol", "estrategia", "formato", "estilo", "cierre"]


def generar(params):
    return generar_conjuntivo(FIJOS["m"], FIJOS["k"], FIJOS["n"], params["semilla"],
                              familias=FIJOS["familias"], familias_por_instancia=FIJOS["familias_por_instancia"],
                              limpias_por_ranura=FIJOS["limpias_por_ranura"],
                              fraccion_insoluble=FIJOS["fraccion_insoluble"],
                              prob_rompe=params["prob_rompe"], prob_rompe_opcion0=params["prob_rompe_opcion0"],
                              pares_acoplados=params["pares_acoplados"], ranuras=RANURAS)


def muestra_al_azar(o, tamano):
    rng = random.Random(SEMILLA_MUESTRA)
    return [o.precision_exacta(o.config([rng.randrange(o.k) for _ in range(o.m)])) for _ in range(tamano)]


def evaluar_candidato(params):
    o = generar(params)
    fila = dict(params)
    fila["precision_inicial"] = o.precision_exacta(o.config([0] * o.m))
    fila["precision_optima"] = 1 - o.parametros["instancias_insolubles"] / o.n
    azar = muestra_al_azar(o, TAMANO_MUESTRA)
    fila["promedio_al_azar"] = statistics.fmean(azar)
    lo, hi = OBJETIVOS["precision_inicial"]
    ok = (lo <= fila["precision_inicial"] <= hi and fila["promedio_al_azar"] < OBJETIVOS["promedio_al_azar_menor_que"]
          and OBJETIVOS["precision_optima"][0] <= fila["precision_optima"] <= OBJETIVOS["precision_optima"][1])
    fila["coordenadas"] = None
    if ok:   # el Algoritmo 3 solo se corre en los que ya cumplen lo demás
        fila["coordenadas"] = ascenso_coordenadas(o).mejor_precision
        lo, hi = OBJETIVOS["coordenadas"]
        ok = lo <= fila["coordenadas"] <= hi and fila["coordenadas"] < fila["precision_optima"]
    fila["valido"] = ok
    return fila


def main():
    with Cronometro() as reloj:
        candidatos = [evaluar_candidato(dict(zip(REJILLA, valores)))
                      for valores in itertools.product(*REJILLA.values())]
    validos = [c for c in candidatos if c["valido"]]
    print(f"{len(candidatos)} candidatos, {len(validos)} válidos ({reloj.segundos:.0f} s)")
    if not validos:
        raise SystemExit("ningún candidato cumple los objetivos")
    elegido = min(validos, key=lambda c: abs(c["precision_inicial"] - 0.09))
    params = {k: elegido[k] for k in REJILLA}

    # Verificación completa del elegido
    o = generar(params)
    fb = fuerza_bruta(o, verdad_conocida=True)
    azar = muestra_al_azar(o, TAMANO_MUESTRA_FINAL)
    coord = ascenso_coordenadas(o)
    azar_ordenado = sorted(azar)
    verificacion = {
        "precision_inicial": o.precision_exacta(o.config([0] * o.m)),
        "precision_optima_fuerza_bruta": fb.mejor_precision,
        "configuraciones_optimas": len(fb.optimas),
        "instancias_insolubles": o.parametros["instancias_insolubles"],
        "fraccion_insoluble": o.parametros["instancias_insolubles"] / o.n,
        "al_azar": {"muestra": TAMANO_MUESTRA_FINAL, "semilla_muestra": SEMILLA_MUESTRA,
                    "promedio": statistics.fmean(azar), "mediana": statistics.median(azar),
                    "percentil_95": azar_ordenado[int(0.95 * len(azar)) - 1], "maximo": azar_ordenado[-1],
                    "fraccion_bajo_5_por_ciento": sum(a < 0.05 for a in azar) / len(azar)},
        "coordenadas_desde_inicial": {"mejor_config": coord.mejor_config, "mejor_precision": coord.mejor_precision,
                                      "evaluaciones": coord.evaluaciones, "consultas_cobradas": coord.consultas_cobradas,
                                      "pasadas": coord.pasadas, "convergio": coord.convergio,
                                      "movimientos": coord.movimientos},
        "pares_acoplados": o.parametros["pares_acoplados"],
        "segundos_cpu_fuerza_bruta": fb.segundos_cpu,
    }
    print("elegido:", params)
    print({k: v for k, v in verificacion.items() if k not in ("coordenadas_desde_inicial",)})
    print("Algoritmo 3:", coord.mejor_precision, coord.movimientos)

    guardar_csv("calibracion_sintetico_candidatos", candidatos)
    guardar_resultado(
        "calibracion_sintetico",
        descripcion="Fase 2: calibración del caso sintético que imita las estadísticas del problema real",
        parametros={"fijos": {**FIJOS, "familias_por_instancia": list(FIJOS["familias_por_instancia"])},
                    "rejilla": REJILLA, "objetivos": OBJETIVOS, "tamano_muestra_rejilla": TAMANO_MUESTRA,
                    "regla_de_eleccion": "válido y con precisión inicial más cercana a 0,09; en empate, el primero de la rejilla"},
        semilla={"semilla_oraculo": params["semilla"], "semilla_muestra": SEMILLA_MUESTRA},
        datos={"candidatos": len(candidatos), "validos": len(validos), "elegido": params,
               "verificacion": verificacion, "segundos_cpu_rejilla": reloj.segundos,
               "fuentes": {
                   "precision_inicial": "resultados/registro_busqueda.csv (9 %) y "
                                        "resultados/registro_busqueda_recalificado_a4cd966.csv (8 %)",
                   "precision_optima": "README_curso.md (DanielMelo404, 2026): techo cercano al 24 %",
                   "al_azar": "README_curso.md (DanielMelo404, 2026): una configuración al azar queda debajo del 5 %",
                   "coordenadas": "resultados/fase2_coordenadas_reproduccion.json (14 % original; 13 % con a4cd966 "
                                  "si la evaluación faltante no supera a la mejor)",
               }},
    )


if __name__ == "__main__":
    main()
