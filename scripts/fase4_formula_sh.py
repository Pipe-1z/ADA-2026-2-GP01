"""Fase 4: fórmula exacta de Successive Halving con tope y corrección de las cifras del enunciado (sin GPU).

1. Verificación: para |C| = 2^R (R = 1..15), n₀ ∈ {1, 2, 3, 4, 5, 8, 16} y n ∈ {1, 2, 10, 50,
   100, 150, 1000} (con n₀ ≤ n), la fórmula cerrada coincide con el conteo ronda por ronda;
   y para R = 3..10, n₀ ∈ {1, 2, 3, 5, 8} y n = número de instancias del oráculo, el código
   del algoritmo cobra exactamente lo que dicen las fórmulas (oráculo sintético de 3-SAT, k = 2).
2. Cifras del enunciado y del proyecto: fórmula del enunciado |C|·n₀·log₂|C| frente al
   conteo exacto (⌈|S_r|/2⌉ sobrevivientes) sin tope, con el tope del enunciado (n = 150) y
   con el del repositorio (n = 100), sin reutilizar y con reutilización.

Escribe resultados/fase4_formula_sh.json.
"""

import itertools
import math

from oraculo_ada.algoritmos import costo_enunciado, costo_sh, costo_sh_cerrado, successive_halving
from oraculo_ada.oraculos import generar_3sat
from oraculo_ada.registro import guardar_resultado

N0S = [1, 2, 3, 4, 5, 8, 16]
NS = [1, 2, 10, 50, 100, 150, 1000]
SIN_TOPE = 10 ** 9


def verificar_formula():
    casos, diferencias = 0, []
    for R, n0, n in itertools.product(range(1, 16), N0S, NS):
        if n0 > n:
            continue
        casos += 1
        cerrada, conteo = costo_sh_cerrado(R, n0, n), costo_sh(2 ** R, n0, n)
        if (cerrada["sin_reutilizar"], cerrada["con_reutilizar"]) != (conteo["sin_reutilizar"], conteo["con_reutilizar"]):
            diferencias.append({"R": R, "n0": n0, "n": n})
    return {"casos": casos, "diferencias": diferencias}


def verificar_codigo():
    casos, diferencias = 0, []
    for R, n0 in itertools.product(range(3, 11), [1, 2, 3, 5, 8]):
        o = generar_3sat(R, 4.0, R)
        sh = successive_halving(o, list(o.espacio()), n0=n0, semilla_instancias=R * 100 + n0)
        esperado = costo_sh(2 ** R, n0, o.n)
        cerrada = costo_sh_cerrado(R, n0, o.n) if n0 <= o.n else None
        casos += 1
        ok = (sh.consultas_solicitadas == esperado["sin_reutilizar"] + o.n
              and sh.consultas_cobradas == esperado["con_reutilizar"] + esperado["completar_ganador"]
              and (cerrada is None or (cerrada["sin_reutilizar"], cerrada["con_reutilizar"])
                   == (esperado["sin_reutilizar"], esperado["con_reutilizar"])))
        if not ok:
            diferencias.append({"R": R, "n0": n0, "n": o.n})
    return {"casos": casos, "diferencias": diferencias}


def cifra(nombre, C, n0, fuente):
    fila = {"caso": nombre, "fuente": fuente, "C": C, "n0": n0, "log2_C": math.log2(C),
            "potencia_de_dos": C & (C - 1) == 0, "rondas": len(costo_sh(C, n0, SIN_TOPE)["por_ronda"]),
            "formula_enunciado": costo_enunciado(C, n0)}
    for etiqueta, n in (("sin_tope", SIN_TOPE), ("tope_150", 150), ("tope_100", 100)):
        c = costo_sh(C, n0, n)
        fila[etiqueta] = {"sin_reutilizar": c["sin_reutilizar"], "con_reutilizar": c["con_reutilizar"],
                          "completar_ganador": c["completar_ganador"],
                          "n_r": [nr for _, nr in c["por_ronda"]], "sobrevivientes": [s for s, _ in c["por_ronda"]]}
    return fila


def main():
    formula, codigo = verificar_formula(), verificar_codigo()
    print("fórmula:", formula["casos"], "casos,", len(formula["diferencias"]), "diferencias")
    print("código:", codigo["casos"], "casos,", len(codigo["diferencias"]), "diferencias")
    cifras = [
        cifra("enunciado: |C| = 3840, n0 = 2", 3840, 2, "enunciado, Algoritmo 2 (cifra declarada: 91.444)"),
        cifra("enunciado: |C| = 144, n0 = 2", 144, 2, "enunciado, Algoritmo 2 ('Para |C| = 144 y n0 = 2')"),
        cifra("enunciado: |C| = 432 (variante con temperatura), n0 = 2", 432, 2, "enunciado, variante de temperatura"),
        cifra("proyecto: |C| = 32768, n0 = 1", 32768, 1, "repositorio del curso (8^5)"),
        cifra("proyecto: |C| = 32768, n0 = 2", 32768, 2, "repositorio del curso (8^5)"),
        cifra("proyecto con temperatura: |C'| = 98304, n0 = 1", 98304, 1, "8^5 · 3"),
        cifra("proyecto con temperatura: |C'| = 98304, n0 = 2", 98304, 2, "8^5 · 3"),
    ]
    for f in cifras:
        print(f"{f['caso']:55s} enunciado {f['formula_enunciado']:12.3f} | exacto sin tope {f['sin_tope']['sin_reutilizar']:7d} "
              f"| n=150: {f['tope_150']['sin_reutilizar']:7d} / {f['tope_150']['con_reutilizar']:7d} "
              f"| n=100: {f['tope_100']['sin_reutilizar']:7d} / {f['tope_100']['con_reutilizar']:7d}")
    guardar_resultado(
        "fase4_formula_sh",
        descripcion="Fase 4: verificación de la fórmula exacta de Successive Halving con tope y corrección de las "
                    "cifras del enunciado",
        parametros={"rejilla_formula": {"R": [1, 15], "n0": N0S, "n": NS},
                    "rejilla_codigo": {"R": [3, 10], "n0": [1, 2, 3, 5, 8], "oraculo": "generar_3sat(R, 4.0, R)"},
                    "sin_tope_equivale_a_n": SIN_TOPE},
        semilla={"instancias_codigo": "R * 100 + n0", "oraculo_codigo": "R"},
        datos={"verificacion_formula": formula, "verificacion_codigo": codigo, "cifras": cifras},
    )


if __name__ == "__main__":
    main()
