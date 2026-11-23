"""Casos sintéticos comunes a las comparaciones de estrategias (Fases 2b, 4 y 5).

Las cuatro variantes son las de la Fase 2b (``resultados/fase2b_plan.json``):

- ``calibrado_24``: los primeros 30 candidatos válidos de ``resultados/calibracion_sintetico.json``.
- ``calibrado_28``: los 25 candidatos válidos de ``resultados/calibracion_sintetico_28.json``.
- ``disyuntivo``: ``generar_disyuntivo(5, 8, 100, s, interacciones=10)``, s = 1..30.
- ``sin_limpias``: ``generar_conjuntivo(5, 8, 100, s, familias=14, limpias_por_ranura=0, interacciones=10)``, s = 1..30.
"""

from ..oraculos import generar_calibrado, generar_conjuntivo, generar_disyuntivo
from ..registro import cargar_resultado

RANURAS = ["rol", "estrategia", "formato", "estilo", "cierre"]

VARIANTES = {
    "calibrado_24": {"generador": "generar_calibrado", "techo": 24, "num_casos": 30,
                     "casos": "los primeros 30 candidatos válidos de resultados/calibracion_sintetico.json"},
    "calibrado_28": {"generador": "generar_calibrado", "techo": 28, "num_casos": 25,
                     "casos": "los 25 candidatos válidos de resultados/calibracion_sintetico_28.json"},
    "disyuntivo": {"generador": "generar_disyuntivo", "m": 5, "k": 8, "n": 100, "interacciones": 10,
                   "num_casos": 30, "casos": "semillas 1 a 30"},
    "sin_limpias": {"generador": "generar_conjuntivo", "m": 5, "k": 8, "n": 100, "familias": 14,
                    "limpias_por_ranura": 0, "interacciones": 10, "num_casos": 30, "casos": "semillas 1 a 30"},
}


def casos_de(var):
    """Lista de (número de caso, función que genera el oráculo, parámetros del caso)."""
    if var["generador"] == "generar_calibrado":
        archivo = "calibracion_sintetico" if var["techo"] == 24 else f"calibracion_sintetico_{var['techo']}"
        validos = cargar_resultado(archivo)["datos"]["lista_validos"][:var["num_casos"]]
        return [(i, (lambda c=c: generar_calibrado(var["techo"], candidato=c)), c) for i, c in enumerate(validos, 1)]
    if var["generador"] == "generar_disyuntivo":
        return [(s, (lambda s=s: generar_disyuntivo(var["m"], var["k"], var["n"], s,
                                                    interacciones=var["interacciones"], ranuras=RANURAS)),
                 {"semilla": s}) for s in range(1, var["num_casos"] + 1)]
    return [(s, (lambda s=s: generar_conjuntivo(var["m"], var["k"], var["n"], s, familias=var["familias"],
                                                limpias_por_ranura=var["limpias_por_ranura"],
                                                interacciones=var["interacciones"], ranuras=RANURAS)),
             {"semilla": s}) for s in range(1, var["num_casos"] + 1)]
