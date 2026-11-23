"""Fase 6: validación experimental de las funciones de eficiencia (sin GPU).

Para cada algoritmo y cada dimensión de tamaño (n, |C| o m, |S|, B) se mide, con 5
repeticiones (semillas 1 a 5) y al menos 5 tamaños:

- Q: consultas al oráculo (la métrica principal; el recurso caro con el modelo real);
- K: cotas calculadas (solo backtracking; cómputo en CPU);
- tiempo de CPU del algoritmo con el **oráculo sintético** (no es tiempo de GPU).

y se compara con su función teórica g: constante ajustada c (T ≈ c·g), pendiente en
escala log-log (observada y teórica sobre los mismos tamaños) y tabla de cocientes T/g.

Escribe resultados/fase6_validacion.csv (una fila por corrida) y
resultados/fase6_validacion.json (resumen). Las figuras las genera scripts/fase6_figuras.py.
"""

import math
import statistics
import time

from oraculo_ada.algoritmos import (
    ascenso_coordenadas,
    backtracking,
    costo_sh_cerrado,
    fuerza_bruta,
    muestra_configuraciones,
    successive_halving,
)
from oraculo_ada.algoritmos.reparto import reparto_ucb1, reparto_uniforme
from oraculo_ada.analisis.ajuste import ajustar_constante, pendiente_loglog, tabla_cocientes
from oraculo_ada.oraculos import generar_3sat, generar_conjuntivo, generar_peor_caso_backtracking
from oraculo_ada.registro import guardar_csv, guardar_resultado

REPETICIONES = [1, 2, 3, 4, 5]
NS = [25, 50, 100, 200, 400, 800]


def cronometrar(funcion):
    t0 = time.perf_counter()
    salida = funcion()
    return salida, time.perf_counter() - t0


# ---------------------------------------------------------------- un experimento por (algoritmo, dimensión)
# Cada uno devuelve: lista de tamaños, función (tamaño, semilla) → medidas, y funciones teóricas por medida.

def fb_n(n, s):
    r, t = cronometrar(lambda: fuerza_bruta(generar_conjuntivo(4, 4, n, s)))
    return {"Q": r.consultas_cobradas, "CPU": t}


def fb_m(m, s):
    r, t = cronometrar(lambda: fuerza_bruta(generar_conjuntivo(m, 4, 50, s)))
    return {"Q": r.consultas_cobradas, "CPU": t}


def bt_peor_n(n, s):
    r, t = cronometrar(lambda: backtracking(generar_peor_caso_backtracking(4, 4, n)))
    return {"Q": r.consultas_cobradas, "K": r.cotas_calculadas, "CPU": t}


def bt_peor_m(m, s):
    r, t = cronometrar(lambda: backtracking(generar_peor_caso_backtracking(m, 4, 50)))
    return {"Q": r.consultas_cobradas, "K": r.cotas_calculadas, "CPU": t}


def bt_3sat(v, s):
    o = generar_3sat(v, 4.26, s)
    r, t = cronometrar(lambda: backtracking(o))
    return {"Q": r.consultas_cobradas, "K": r.cotas_calculadas, "CPU": t, "n": o.n}


def sh_S(R, s):
    o = generar_conjuntivo(6, 8, 100, s)
    S = muestra_configuraciones(o, 2 ** R, s)
    r, t = cronometrar(lambda: successive_halving(o, S, n0=1, semilla_instancias=s, evaluar_ganador=False))
    return {"Q_con": r.consultas_cobradas, "Q_sin": r.consultas_solicitadas, "CPU": t}


def sh_n(n, s):
    o = generar_conjuntivo(6, 8, n, s)
    S = muestra_configuraciones(o, 1024, s)
    r, t = cronometrar(lambda: successive_halving(o, S, n0=1, semilla_instancias=s, evaluar_ganador=False))
    return {"Q_con": r.consultas_cobradas, "Q_sin": r.consultas_solicitadas, "CPU": t}


def coord_n(n, s):
    r, t = cronometrar(lambda: ascenso_coordenadas(generar_conjuntivo(5, 8, n, s, interacciones=10)))
    return {"Q": r.consultas_cobradas, "CPU": t}


def coord_m(m, s):
    r, t = cronometrar(lambda: ascenso_coordenadas(generar_conjuntivo(m, 8, 100, s, interacciones=10)))
    return {"Q": r.consultas_cobradas, "CPU": t}


def uni_S(tam, s):
    o = generar_conjuntivo(6, 8, 100, s)
    S = muestra_configuraciones(o, tam, s)
    r, t = cronometrar(lambda: reparto_uniforme(o, S, 10 * tam, semilla_instancias=s))
    return {"Q": r.consultas_cobradas, "CPU": t}


def uni_m(m, s):
    o = generar_conjuntivo(6, 8, 100, s)
    S = muestra_configuraciones(o, 128, s)
    r, t = cronometrar(lambda: reparto_uniforme(o, S, 128 * m, semilla_instancias=s))
    return {"Q": r.consultas_cobradas, "CPU": t}


def ucb_B(b, s):
    o = generar_conjuntivo(6, 8, 100, s)
    S = muestra_configuraciones(o, 128, s)
    r, t = cronometrar(lambda: reparto_ucb1(o, S, 128 * b, semilla_instancias=s))
    return {"Q": r.consultas_cobradas, "CPU": t}


def ucb_S(tam, s):
    o = generar_conjuntivo(6, 8, 100, s)
    S = muestra_configuraciones(o, tam, s)
    r, t = cronometrar(lambda: reparto_ucb1(o, S, 16 * tam, semilla_instancias=s))
    return {"Q": r.consultas_cobradas, "CPU": t}


EXPERIMENTOS = [
    # (algoritmo, dimensión, etiqueta del tamaño, tamaños, función, eje x(tamaño), {medida: (g, descripción)})
    ("fuerza_bruta", "n", "n", NS, fb_n, lambda n: n,
     {"Q": (lambda n: 256 * n, "|C|·n con |C| = 4^4"), "CPU": (lambda n: 256 * n, "∝ |C|·n")}),
    ("fuerza_bruta", "C", "|C| = 4^m", [2, 3, 4, 5, 6], fb_m, lambda m: 4 ** m,
     {"Q": (lambda m: 4 ** m * 50, "|C|·n con n = 50"), "CPU": (lambda m: 4 ** m * 50, "∝ |C|·n")}),
    ("backtracking_peor_caso", "n", "n", NS, bt_peor_n, lambda n: n,
     {"Q": (lambda n: 256 * n, "|C|·n"), "K": (lambda n: (256 - 1) // 3, "(|C| − 1)/(k − 1)"),
      "CPU": (lambda n: 256 * n, "∝ |C|·n")}),
    ("backtracking_peor_caso", "C", "|C| = 4^m", [2, 3, 4, 5, 6, 7], bt_peor_m, lambda m: 4 ** m,
     {"Q": (lambda m: 4 ** m * 50, "|C|·n"), "K": (lambda m: (4 ** m - 1) // 3, "(|C| − 1)/(k − 1)"),
      "CPU": (lambda m: 4 ** m * 50, "∝ |C|·n")}),
    ("backtracking_3sat", "C", "|C| = 2^v (razón 4,26)", [10, 12, 14, 16, 18, 20], bt_3sat, lambda v: 2 ** v,
     {"Q": (lambda v: 2 ** v * round(4.26 * v), "peor caso |C|·n"),
      "K": (lambda v: 2 ** v - 1, "peor caso (|C| − 1)/(k − 1)"),
      "CPU": (lambda v: 2 ** v * round(4.26 * v), "peor caso ∝ |C|·n")}),
    ("successive_halving", "S", "|S| = 2^R", [6, 7, 8, 9, 10, 11, 12], sh_S, lambda R: 2 ** R,
     {"Q_sin": (lambda R: costo_sh_cerrado(R, 1, 100)["sin_reutilizar"], "fórmula exacta sin reutilizar"),
      "Q_con": (lambda R: costo_sh_cerrado(R, 1, 100)["con_reutilizar"], "fórmula exacta con reutilización"),
      "CPU": (lambda R: costo_sh_cerrado(R, 1, 100)["sin_reutilizar"], "∝ Q_sin")}),
    ("successive_halving", "n", "n", NS, sh_n, lambda n: n,
     {"Q_sin": (lambda n: costo_sh_cerrado(10, 1, n)["sin_reutilizar"], "fórmula exacta sin reutilizar"),
      "Q_con": (lambda n: costo_sh_cerrado(10, 1, n)["con_reutilizar"], "fórmula exacta con reutilización"),
      "CPU": (lambda n: costo_sh_cerrado(10, 1, n)["sin_reutilizar"], "∝ Q_sin")}),
    ("coordenadas", "n", "n", NS, coord_n, lambda n: n,
     {"Q": (lambda n: n * (1 + 3 * 5 * 7), "cota n·[1 + I·Σ(k_p − 1)]"),
      "CPU": (lambda n: n * (1 + 3 * 5 * 7), "∝ cota")}),
    ("coordenadas", "m", "m", [3, 4, 5, 6, 7, 8], coord_m, lambda m: m,
     {"Q": (lambda m: 100 * (1 + 3 * m * 7), "cota n·[1 + I·Σ(k_p − 1)]"),
      "CPU": (lambda m: 100 * (1 + 3 * m * 7), "∝ cota")}),
    ("uniforme", "S", "|S|", [32, 64, 128, 256, 512, 1024], uni_S, lambda x: x,
     {"Q": (lambda x: 10 * x, "|S|·m con m = 10"), "CPU": (lambda x: 10 * x, "∝ |S|·m")}),
    ("uniforme", "m", "m", [5, 10, 20, 40, 80], uni_m, lambda x: x,
     {"Q": (lambda x: 128 * x, "|S|·m con |S| = 128"), "CPU": (lambda x: 128 * x, "∝ |S|·m")}),
    ("ucb1", "B", "B/|S| (|S| = 128)", [2, 4, 8, 16, 32, 64], ucb_B, lambda b: 128 * b,
     {"Q": (lambda b: 128 * b, "B"), "CPU": (lambda b: 128 * b * 128, "∝ B·|S| (índice de todos los brazos por jugada)")}),
    ("ucb1", "S", "|S| (B = 16·|S|)", [32, 64, 128, 256, 512, 1024], ucb_S, lambda x: x,
     {"Q": (lambda x: 16 * x, "B = 16·|S|"), "CPU": (lambda x: 16 * x * x, "∝ B·|S| = 16·|S|²")}),
]


def main():
    filas, resumen = [], []
    for algoritmo, dimension, etiqueta, tamanos, funcion, eje, teoria in EXPERIMENTOS:
        medidas = {}
        for x in tamanos:
            for s in REPETICIONES:
                m = funcion(x, s)
                filas.append({"algoritmo": algoritmo, "dimension": dimension, "tamano": x, "eje_x": eje(x),
                              "semilla": s, **{k: v for k, v in m.items()}})
                for k, v in m.items():
                    if k in teoria:
                        medidas.setdefault(k, {}).setdefault(x, []).append(v)
        for medida, (g, descripcion) in teoria.items():
            xs = [eje(x) for x in tamanos]
            obs = [statistics.fmean(medidas[medida][x]) for x in tamanos]
            des = [statistics.stdev(medidas[medida][x]) if len(medidas[medida][x]) > 1 else 0.0 for x in tamanos]
            teo = [g(x) for x in tamanos]
            c = ajustar_constante(obs, teo)
            pend_teo = pendiente_loglog(xs, teo) if len(set(teo)) > 1 else 0.0
            resumen.append({
                "algoritmo": algoritmo, "dimension": dimension, "etiqueta_tamano": etiqueta, "medida": medida,
                "teoria": descripcion, "tamanos": tamanos, "eje_x": xs, "observado_medio": obs,
                "observado_desviacion": des, "teorico": teo, "constante_ajustada": c,
                "pendiente_loglog_observada": pendiente_loglog(xs, obs), "pendiente_loglog_teorica": pend_teo,
                "cocientes": tabla_cocientes(xs, obs, teo),
                "es_cpu": medida == "CPU",
            })
            print(f"{algoritmo:24s} {dimension:2s} {medida:6s} c={c:10.4g}  pendiente obs {resumen[-1]['pendiente_loglog_observada']:.3f}"
                  f" / teórica {pend_teo:.3f}  cociente [{resumen[-1]['cocientes']['c1']:.4g}, {resumen[-1]['cocientes']['c2']:.4g}]",
                  flush=True)
    guardar_csv("fase6_validacion", filas)
    guardar_resultado(
        "fase6_validacion",
        descripcion="Fase 6: validación experimental de Q (consultas), K (cotas) y tiempo de CPU con el oráculo "
                    "sintético (no es tiempo de GPU) contra las funciones teóricas",
        parametros={"repeticiones": REPETICIONES, "experimentos": [
            {"algoritmo": a, "dimension": d, "tamanos": t, "medidas": {k: v[1] for k, v in te.items()}}
            for a, d, _, t, _, _, te in EXPERIMENTOS]},
        semilla={"oraculos_y_muestras": REPETICIONES},
        datos={"resumen": resumen, "corridas": len(filas)},
    )


if __name__ == "__main__":
    main()
