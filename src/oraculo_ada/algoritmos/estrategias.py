"""Estrategias de búsqueda construidas con los algoritmos base (Fases 4 y 5).

- ``sh_muestra``: Successive Halving sobre M configuraciones sorteadas al azar del espacio.
- ``dos_ranuras_sh``: Algoritmo 3 original y, desde su resultado, Successive Halving
  sobre el vecindario completo de movimientos dobles (todas las configuraciones que
  cambian exactamente dos ranuras: C(m, 2) · (k − 1)² = 10 · 49 = 490 con m = 5,
  k = 8); si el ganador mejora en las n instancias, se adopta y se corre de nuevo el
  Algoritmo 3 desde él. A lo sumo ``rondas`` veces.

Todo sorteo usa ``random.Random`` con una semilla explícita (CLAUDE.md, regla 16).
"""

import itertools
import math
import random

from .coordenadas import ascenso_coordenadas
from .successive_halving import successive_halving


def muestra_configuraciones(oraculo, M, semilla, temperatura=None):
    """M configuraciones distintas, sorteadas sin reemplazo y de manera uniforme del espacio C."""
    tamanos = [len(oraculo.opciones[r]) for r in oraculo.ranuras]
    total = math.prod(tamanos)
    if not 1 <= M <= total:
        raise ValueError(f"M debe estar entre 1 y |C| = {total}")
    temperatura = oraculo.temperaturas[0] if temperatura is None else temperatura
    configs = []
    for indice in random.Random(semilla).sample(range(total), M):
        digitos = []
        for t in reversed(tamanos):                    # decodificación en base mixta
            indice, d = divmod(indice, t)
            digitos.append(d)
        idx = [oraculo.opciones[r][d] for r, d in zip(oraculo.ranuras, reversed(digitos))]
        configs.append(oraculo.config(idx, temperatura=temperatura))
    return configs


def vecindario_doble(oraculo, config):
    """Todas las configuraciones que difieren de ``config`` en exactamente dos ranuras."""
    vecinos = []
    for p, q in itertools.combinations(oraculo.ranuras, 2):
        for a in oraculo.opciones[p]:
            if a == config[p]:
                continue
            for b in oraculo.opciones[q]:
                if b != config[q]:
                    vecinos.append(dict(config, **{p: a, q: b}))
    return vecinos


def sh_muestra(oraculo, M, *, n0, semilla_muestra, semilla_instancias, semilla=1):
    """Successive Halving sobre una muestra al azar de M configuraciones."""
    candidatos = muestra_configuraciones(oraculo, M, semilla_muestra)
    return successive_halving(oraculo, candidatos, n0=n0, semilla_instancias=semilla_instancias, semilla=semilla)


def dos_ranuras_sh(oraculo, *, n0, rondas, semilla_instancias, inicial=None, **opciones_coordenadas):
    """Algoritmo 3 seguido de rondas de "dos ranuras con filtro por Successive Halving"."""
    consultas_antes, solicitadas_antes = oraculo.consultas, oraculo.consultas_solicitadas
    base = ascenso_coordenadas(oraculo, inicial, **opciones_coordenadas)
    actual, p = base.mejor_config, base.mejor_precision
    historia = [{"etapa": "coordenadas", "config": actual, "precision": p, "consultas_acumuladas": oraculo.consultas - consultas_antes}]
    for ronda in range(1, rondas + 1):
        vecinos = vecindario_doble(oraculo, actual)
        sh = successive_halving(oraculo, vecinos, n0=n0, semilla_instancias=f"{semilla_instancias}|{ronda}",
                                semilla=opciones_coordenadas.get("semilla", 1))
        mejora = sh.precision_ganador > p
        historia.append({"etapa": f"filtro SH {ronda}", "vecinos": len(vecinos), "ganador": sh.ganador,
                         "precision_ganador": sh.precision_ganador, "adoptado": mejora,
                         "rondas_sh": len(sh.rondas), "consultas_acumuladas": oraculo.consultas - consultas_antes})
        if not mejora:
            break
        siguiente = ascenso_coordenadas(oraculo, sh.ganador, **opciones_coordenadas)
        actual, p = siguiente.mejor_config, siguiente.mejor_precision
        historia.append({"etapa": f"coordenadas {ronda + 1}", "config": actual, "precision": p,
                         "consultas_acumuladas": oraculo.consultas - consultas_antes})
    return {"mejor_config": actual, "mejor_precision": p, "historia": historia,
            "consultas_cobradas": oraculo.consultas - consultas_antes,
            "consultas_solicitadas": oraculo.consultas_solicitadas - solicitadas_antes}
