"""Algoritmo 4: reparto de un presupuesto B de consultas entre las configuraciones de un conjunto S.

Los tres esquemas reciben el mismo conjunto S, el mismo presupuesto B (consultas
**nuevas**, con caché) y la misma permutación de las n instancias (semilla fija), y
devuelven la configuración elegida. Ninguno usa la verdad del oráculo.

- **Uniforme:** m = min(⌊B / |S|⌋, n) instancias por configuración (las primeras m de
  la permutación); elige la de mayor precisión observada (en empate, la primera en S).
  Costo: |S| · m ≤ B. Limitación (enunciado): con m pequeño y evaluación todo o nada,
  muchas configuraciones buenas aparecen con 0 % por puro ruido.
- **Successive Halving con presupuesto:** el mayor n₀ entero tal que el costo con
  reutilización Q_con(|S|, n₀, n) ≤ B (Fase 4); elige al ganador del torneo. Si ni con
  n₀ = 1 alcanza, no es factible con ese B.
- **UCB1** (Auer, Cesa-Bianchi y Fischer, 2002, Figura 1): jugar un brazo es evaluar
  la configuración en su siguiente instancia de la permutación (recompensa 0 o 1).
  Primero juega cada brazo una vez; después juega el que maximiza
  x̄_j + √(2 ln t / n_j), donde t es el número total de jugadas. Un brazo que ya usó
  las n instancias se conoce con exactitud y no se vuelve a jugar. Al agotar B
  recomienda el brazo **más jugado** (en empate, el de mayor media y después el
  primero en S). Necesita B ≥ |S|.
"""

import math
import random
from dataclasses import dataclass, field

from ..oraculos.base import PresupuestoAgotado
from .successive_halving import costo_sh, successive_halving


@dataclass
class ResultadoReparto:
    esquema: str
    elegido: dict = None
    factible: bool = True
    consultas_cobradas: int = 0
    parametro: dict = field(default_factory=dict)   # m (uniforme), n0 (SH) o jugadas por brazo (UCB1)
    presupuesto_agotado: bool = False


def _orden(oraculo, semilla_instancias, n):
    instancias = oraculo.instancias
    n = len(instancias) if n is None else n
    return random.Random(semilla_instancias).sample(instancias, len(instancias))[:n]


def reparto_uniforme(oraculo, candidatos, B, *, semilla_instancias, n=None, semilla=1, modo_presupuesto="nuevas"):
    orden = _orden(oraculo, semilla_instancias, n)
    m = min(B // len(candidatos), len(orden))
    if m < 1:
        return ResultadoReparto("uniforme", factible=False, parametro={"m": 0})
    antes = oraculo.consultas
    puntajes, agotado = [], False
    with oraculo.presupuesto(B, modo_presupuesto) as tope:
        try:
            for c in candidatos:
                puntajes.append(oraculo.evaluar(c, orden[:m], semilla=semilla).precision)
        except PresupuestoAgotado as e:
            if e.tope_id != tope:
                raise
            agotado = True
    if not puntajes:
        return ResultadoReparto("uniforme", None, True, oraculo.consultas - antes, {"m": m}, True)
    j = max(range(len(puntajes)), key=lambda i: (puntajes[i], -i))
    return ResultadoReparto("uniforme", candidatos[j], True, oraculo.consultas - antes, {"m": m}, agotado)


def n0_para_presupuesto(num_candidatos, B, n):
    """Mayor n₀ con Q_con(|S|, n₀, n) ≤ B, o None si ni n₀ = 1 alcanza."""
    mejor = None
    for n0 in range(1, n + 1):
        if costo_sh(num_candidatos, n0, n)["con_reutilizar"] <= B:
            mejor = n0
        else:
            break
    return mejor


def reparto_sh(oraculo, candidatos, B, *, semilla_instancias, n=None, semilla=1, modo_presupuesto="nuevas"):
    n = len(oraculo.instancias) if n is None else n
    n0 = n0_para_presupuesto(len(candidatos), B, n)
    if n0 is None:
        return ResultadoReparto("successive_halving", factible=False, parametro={"n0": None})
    antes = oraculo.consultas
    sh = successive_halving(oraculo, candidatos, n0=n0, n=n, semilla_instancias=semilla_instancias,
                            semilla=semilla, evaluar_ganador=False, presupuesto=B, modo_presupuesto=modo_presupuesto)
    return ResultadoReparto("successive_halving", sh.ganador, True, oraculo.consultas - antes, {"n0": n0},
                            sh.presupuesto_agotado)


def reparto_ucb1(oraculo, candidatos, B, *, semilla_instancias, n=None, semilla=1, modo_presupuesto="nuevas"):
    orden = _orden(oraculo, semilla_instancias, n)
    K = len(candidatos)
    if B < K:
        return ResultadoReparto("ucb1", factible=False, parametro={})
    import numpy as np

    antes = oraculo.consultas
    jugadas, sumas = np.zeros(K), np.zeros(K)

    def jugar(j):
        x = orden[int(jugadas[j])]
        sumas[j] += oraculo.evaluar(candidatos[j], [x], semilla=semilla).aciertos
        jugadas[j] += 1

    t, agotado = 0, False
    with oraculo.presupuesto(B, modo_presupuesto) as tope:
        try:
            for j in range(K):                                   # inicialización: cada brazo una vez
                jugar(j)
                t += 1
            while t < B:
                indice = sumas / jugadas + np.sqrt(2 * math.log(t) / jugadas)
                indice[jugadas >= len(orden)] = -np.inf          # brazo agotado: ya se conoce con exactitud
                j = int(np.argmax(indice))                       # en empate, el primero en S
                if indice[j] == -np.inf:
                    break
                jugar(j)
                t += 1
        except PresupuestoAgotado as e:
            if e.tope_id != tope:
                raise
            agotado = True
    jugadas, sumas = jugadas.astype(int).tolist(), sumas.astype(int).tolist()
    jugados = [i for i in range(K) if jugadas[i] > 0]
    if not jugados:
        return ResultadoReparto("ucb1", None, True, oraculo.consultas - antes, {}, True)
    elegido = max(jugados, key=lambda i: (jugadas[i], sumas[i] / jugadas[i], -i))
    return ResultadoReparto("ucb1", candidatos[elegido], True, oraculo.consultas - antes,
                            {"jugadas_max": max(jugadas), "jugadas_min": min(jugadas), "jugadas_totales": t},
                            agotado)


ESQUEMAS = {"uniforme": reparto_uniforme, "successive_halving": reparto_sh, "ucb1": reparto_ucb1}
