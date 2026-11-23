"""Fase 6: validación experimental de las funciones de eficiencia (sin GPU).

Para cada algoritmo y cada dimensión de tamaño (n, |C| o m, |S|, B) se mide, con 5
repeticiones (semillas 1 a 5) y al menos 5 tamaños:

- Q: consultas al oráculo (la métrica principal; el recurso caro con el modelo real);
- K: cotas calculadas (solo backtracking; cómputo en CPU);
- tiempo de CPU del algoritmo con el **oráculo sintético** (no es tiempo de GPU).

y se compara con su función teórica: para Q (y K), la fórmula exacta o la cota (una base g,
T ≈ c·g); para el tiempo de CPU, un modelo de uno o dos términos (costo fijo por
evaluación + costo por consulta, o el término asintótico) ajustado por mínimos cuadrados no
negativos. Se reportan los coeficientes, la pendiente log-log observada, la del ajuste y la
del término dominante, y las tablas de cocientes observado/ajuste (≈ 1) y observado/término
dominante (→ constante, como en las presentaciones del curso). Antes de medir cada
experimento se hace una corrida de calentamiento que se descarta.

Escribe resultados/fase6_validacion.csv (una fila por corrida) y
resultados/fase6_validacion.json (resumen). Las figuras las genera scripts/fase6_figuras.py.
"""

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
from oraculo_ada.analisis.ajuste import ajustar_combinacion, pendiente_loglog, tabla_cocientes
from oraculo_ada.oraculos import generar_3sat, generar_conjuntivo, generar_peor_caso_backtracking
from oraculo_ada.registro import guardar_csv, guardar_resultado

REPETICIONES = [1, 2, 3, 4, 5]
NS = [25, 50, 100, 200, 400, 800]
SIN_AJUSTE = {"backtracking_3sat"}     # se compara con el peor caso sin escalar


def cronometrar(funcion):
    t0 = time.perf_counter()
    salida = funcion()
    return salida, time.perf_counter() - t0


# ---------------------------------------------------------------- un experimento por (algoritmo, dimensión)

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


def q_sin(R, n):
    return costo_sh_cerrado(R, 1, n)["sin_reutilizar"]


def q_con(R, n):
    return costo_sh_cerrado(R, 1, n)["con_reutilizar"]


# (algoritmo, dimensión, etiqueta del tamaño, tamaños, función, eje x(tamaño),
#  {medida: ([bases de la función teórica], descripción)}); la última base es el término dominante.
EXPERIMENTOS = [
    ("fuerza_bruta", "n", "n", NS, fb_n, lambda n: n,
     {"Q": ([lambda n: 256 * n], "|C|·n con |C| = 4^4"),
      "CPU": ([lambda n: 256, lambda n: 256 * n], "a·|C| (por evaluación) + b·|C|·n (por consulta)")}),
    ("fuerza_bruta", "C", "|C| = 4^m", [2, 3, 4, 5, 6], fb_m, lambda m: 4 ** m,
     {"Q": ([lambda m: 4 ** m * 50], "|C|·n con n = 50"), "CPU": ([lambda m: 4 ** m * 50], "∝ |C|·n")}),
    ("backtracking_peor_caso", "n", "n", NS, bt_peor_n, lambda n: n,
     {"Q": ([lambda n: 256 * n], "|C|·n"), "K": ([lambda n: (256 - 1) // 3], "(|C| − 1)/(k − 1)"),
      "CPU": ([lambda n: 256 + 85, lambda n: (256 + 85) * n], "a·(hojas + cotas) + b·(hojas + cotas)·n")}),
    ("backtracking_peor_caso", "C", "|C| = 4^m", [2, 3, 4, 5, 6, 7], bt_peor_m, lambda m: 4 ** m,
     {"Q": ([lambda m: 4 ** m * 50], "|C|·n"), "K": ([lambda m: (4 ** m - 1) // 3], "(|C| − 1)/(k − 1)"),
      "CPU": ([lambda m: 4 ** m * 50], "∝ |C|·n")}),
    ("backtracking_3sat", "C", "|C| = 2^v (razón 4,26)", [10, 12, 14, 16, 18, 20], bt_3sat, lambda v: 2 ** v,
     {"Q": ([lambda v: 2 ** v * round(4.26 * v)], "peor caso |C|·n"),
      "K": ([lambda v: 2 ** v - 1], "peor caso (|C| − 1)/(k − 1)"),
      "CPU": ([lambda v: 2 ** v * round(4.26 * v)], "peor caso ∝ |C|·n")}),
    ("successive_halving", "S", "|S| = 2^R", [6, 7, 8, 9, 10, 11, 12], sh_S, lambda R: 2 ** R,
     {"Q_sin": ([lambda R: q_sin(R, 100)], "fórmula exacta sin reutilizar"),
      "Q_con": ([lambda R: q_con(R, 100)], "fórmula exacta con reutilización"),
      "CPU": ([lambda R: 2 * 2 ** R, lambda R: q_sin(R, 100)], "a·Σ|S_r| (evaluaciones) + b·Q_sin")}),
    ("successive_halving", "n", "n", NS, sh_n, lambda n: n,
     {"Q_sin": ([lambda n: q_sin(10, n)], "fórmula exacta sin reutilizar"),
      "Q_con": ([lambda n: q_con(10, n)], "fórmula exacta con reutilización"),
      "CPU": ([lambda n: 2 * 1024, lambda n: q_sin(10, n)], "a·Σ|S_r| (evaluaciones) + b·Q_sin")}),
    ("coordenadas", "n", "n", NS, coord_n, lambda n: n,
     {"Q": ([lambda n: n * (1 + 3 * 5 * 7)], "cota n·[1 + I·Σ(k_p − 1)]"),
      "CPU": ([lambda n: 1 + 3 * 5 * 7, lambda n: n * (1 + 3 * 5 * 7)], "a·(evaluaciones) + b·cota")}),
    ("coordenadas", "m", "m", [3, 4, 5, 6, 7, 8], coord_m, lambda m: m,
     {"Q": ([lambda m: 100 * (1 + 3 * m * 7)], "cota n·[1 + I·Σ(k_p − 1)]"),
      "CPU": ([lambda m: 100 * (1 + 3 * m * 7)], "∝ cota")}),
    ("uniforme", "S", "|S|", [32, 64, 128, 256, 512, 1024], uni_S, lambda x: x,
     {"Q": ([lambda x: 10 * x], "|S|·m con m = 10"), "CPU": ([lambda x: 10 * x], "∝ |S|·m")}),
    ("uniforme", "m", "m", [5, 10, 20, 40, 80], uni_m, lambda x: x,
     {"Q": ([lambda x: 128 * x], "|S|·m con |S| = 128"),
      "CPU": ([lambda x: 128, lambda x: 128 * x], "a·|S| (evaluaciones) + b·|S|·m")}),
    ("ucb1", "B", "B/|S| (|S| = 128)", [2, 4, 8, 16, 32, 64], ucb_B, lambda b: 128 * b,
     {"Q": ([lambda b: 128 * b], "B"),
      "CPU": ([lambda b: 1, lambda b: 128 * b],
              "a (fijo por corrida) + b·B (cada jugada: una consulta y el índice de los |S| brazos)")}),
    ("ucb1", "S", "|S| (B = 16·|S|)", [32, 64, 128, 256, 512, 1024], ucb_S, lambda x: x,
     {"Q": ([lambda x: 16 * x], "B = 16·|S|"),
      "CPU": ([lambda x: 16 * x, lambda x: 16 * x * x], "a·B (consulta por jugada) + b·B·|S| (índice), B = 16·|S|")}),
]


def main():
    filas, resumen = [], []
    constantes_cpu_peor_caso = []
    for algoritmo, dimension, etiqueta, tamanos, funcion, eje, teoria in EXPERIMENTOS:
        funcion(tamanos[0], REPETICIONES[0])           # calentamiento (importaciones, cachés de Python): se descarta
        medidas = {}
        for x in tamanos:
            for s in REPETICIONES:
                m = funcion(x, s)
                filas.append({"algoritmo": algoritmo, "dimension": dimension, "tamano": x, "eje_x": eje(x),
                              "semilla": s, **m})
                for k, v in m.items():
                    if k in teoria:
                        medidas.setdefault(k, {}).setdefault(x, []).append(v)
        for medida, (bases, descripcion) in teoria.items():
            xs = [eje(x) for x in tamanos]
            obs = [statistics.fmean(medidas[medida][x]) for x in tamanos]
            des = [statistics.stdev(medidas[medida][x]) for x in tamanos]
            valores_bases = [[g(x) for x in tamanos] for g in bases]
            # En 3-SAT la curva teórica es el peor caso: se muestra sin escalar (coeficiente 1),
            # porque no es un modelo de los casos típicos; el cociente da la fracción explorada.
            if algoritmo in SIN_AJUSTE:
                # Q y K: el peor caso tal cual. CPU: el peor caso con la constante (segundos por unidad de
                # |C|·n) medida en el peor caso construido, para que las unidades sean segundos.
                coef = [constantes_cpu_peor_caso[0]] if medida == "CPU" else [1.0]
            else:
                coef = ajustar_combinacion(obs, valores_bases)
            if (algoritmo, dimension, medida) == ("backtracking_peor_caso", "C", "CPU"):
                constantes_cpu_peor_caso[:] = coef
            ajuste = [sum(c * v[i] for c, v in zip(coef, valores_bases)) for i in range(len(tamanos))]
            dominante = valores_bases[-1]
            pend_ajuste = pendiente_loglog(xs, ajuste) if len(set(ajuste)) > 1 and min(ajuste) > 0 else 0.0
            pend_dom = pendiente_loglog(xs, dominante) if len(set(dominante)) > 1 else 0.0
            r = {
                "algoritmo": algoritmo, "dimension": dimension, "etiqueta_tamano": etiqueta, "medida": medida,
                "teoria": descripcion, "tamanos": tamanos, "eje_x": xs, "observado_medio": obs,
                "observado_desviacion": des,
                "observado_minimo": [min(medidas[medida][x]) for x in tamanos],
                "observado_maximo": [max(medidas[medida][x]) for x in tamanos],
                "curva_sin_ajuste": algoritmo in SIN_AJUSTE, "bases": valores_bases, "coeficientes": coef, "teorico_ajustado": ajuste,
                "pendiente_loglog_observada": pendiente_loglog(xs, obs),
                "pendiente_loglog_ajuste": pend_ajuste, "pendiente_loglog_termino_dominante": pend_dom,
                "cocientes_frente_al_ajuste": tabla_cocientes(xs, obs, ajuste),
                "cocientes_frente_al_termino_dominante": tabla_cocientes(xs, obs, dominante),
                "es_cpu": medida == "CPU",
            }
            resumen.append(r)
            print(f"{algoritmo:24s} {dimension:2s} {medida:6s} coef={[float(f'{c:.3g}') for c in coef]}  pendiente obs "
                  f"{r['pendiente_loglog_observada']:.3f} / ajuste {pend_ajuste:.3f} / dominante {pend_dom:.3f}  "
                  f"obs/ajuste [{r['cocientes_frente_al_ajuste']['c1']:.3f}, {r['cocientes_frente_al_ajuste']['c2']:.3f}]",
                  flush=True)
    guardar_csv("fase6_validacion", filas)
    guardar_resultado(
        "fase6_validacion",
        descripcion="Fase 6: validación experimental de Q (consultas), K (cotas) y tiempo de CPU con el oráculo "
                    "sintético (no es tiempo de GPU) contra las funciones teóricas",
        parametros={"repeticiones": REPETICIONES, "calentamiento": "una corrida descartada por experimento",
                    "experimentos": [{"algoritmo": a, "dimension": d, "tamanos": t,
                                      "medidas": {k: v[1] for k, v in te.items()}}
                                     for a, d, _, t, _, _, te in EXPERIMENTOS]},
        semilla={"oraculos_y_muestras": REPETICIONES},
        datos={"resumen": resumen, "corridas": len(filas)},
    )


if __name__ == "__main__":
    main()
