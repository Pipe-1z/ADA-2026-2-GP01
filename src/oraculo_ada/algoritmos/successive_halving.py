"""Algoritmo 2: Successive Halving (divide y vencerás por rondas).

Entrada: un conjunto S de configuraciones candidatas, el tamaño inicial de
muestra n₀ y el tope n de instancias (las de búsqueda). En la ronda r = 0, 1, …
cada sobreviviente se evalúa sobre las primeras

    n_r = min(n₀ · 2^r, n)

instancias de una permutación al azar de las instancias (semilla fija); se
conserva la mitad mejor, ⌈|S_r| / 2⌉, y se repite hasta que queda una sola. Con
|S| = 2^R hay exactamente R rondas y |S_r| = 2^{R−r}.

Las muestras están **anidadas** (la de la ronda r contiene a la de la r − 1), así
que hay dos formas de contar consultas:

- ``sin reutilizar`` (la del enunciado): cada ronda paga |S_r| · n_r.
- ``con reutilización``: con caché, una configuración solo paga las instancias
  nuevas de cada ronda; en total paga el n_r de la última ronda en que se evaluó.

Fórmulas cerradas para |S| = 2^R y 1 ≤ n₀ ≤ n, con ρ = número de rondas sin tope
(ρ = #{r < R : n₀ · 2^r < n} = min(R, ⌈log₂(n/n₀)⌉)):

    Q_sin = |S| · n₀ · ρ + n · (2^{R−ρ+1} − 2)
    Q_con = (|S|/2) · n₀ · ρ + n · (2^{R−ρ} − 1) + n_{R−1}

Sin tope (ρ = R): Q_sin = |S| · n₀ · log₂|S|, la fórmula del enunciado.
Ver la deducción en docs/derivaciones/algoritmo2_successive_halving.md.

Empates en una ronda: se ordena por precisión descendente y, en empate, por la
posición en la lista de la ronda anterior (orden estable), así que el resultado
es determinista dadas la lista inicial y la semilla de las instancias.
"""

import math
import random
from dataclasses import dataclass, field

from ..medicion import Cronometro


# ---------------------------------------------------------------- conteo

def rondas_sh(num_candidatos, n0, n):
    """[(sobrevivientes al empezar la ronda, n_r), ...] hasta que queda uno."""
    if num_candidatos < 1 or n0 < 1 or n < 1:
        raise ValueError("num_candidatos, n0 y n deben ser positivos")
    rondas, s, r = [], num_candidatos, 0
    while s > 1:
        rondas.append((s, min(n0 * 2 ** r, n)))
        s = math.ceil(s / 2)
        r += 1
    return rondas


def costo_sh(num_candidatos, n0, n):
    """Consultas de Successive Halving contadas ronda por ronda (válido para todo |S|).

    Devuelve ``sin_reutilizar`` (Σ |S_r| · n_r), ``con_reutilizar`` (cada candidato
    paga el n_r de la última ronda en que se evaluó) y ``completar_ganador`` (las
    que faltan para evaluar al ganador sobre las n instancias).
    """
    rondas = rondas_sh(num_candidatos, n0, n)
    sin = sum(s * nr for s, nr in rondas)
    con = 0
    for j, (s, nr) in enumerate(rondas):
        siguientes = rondas[j + 1][0] if j + 1 < len(rondas) else 1
        con += (s - siguientes) * nr                   # eliminados en esta ronda
    ultimo = rondas[-1][1] if rondas else 0
    con += ultimo                                      # el ganador se evaluó en la última ronda
    return {"rondas": len(rondas), "por_ronda": rondas, "sin_reutilizar": sin, "con_reutilizar": con,
            "completar_ganador": n - ultimo if rondas else n}


def rondas_sin_tope(R, n0, n):
    """ρ = #{r < R : n₀ · 2^r < n} (aritmética entera, sin redondeos de log₂)."""
    rho = 0
    while rho < R and n0 * 2 ** rho < n:
        rho += 1
    return rho


def costo_sh_cerrado(R, n0, n):
    """Fórmulas cerradas para |S| = 2^R (R ≥ 1) y 1 ≤ n₀ ≤ n."""
    if R < 1 or not 1 <= n0 <= n:
        raise ValueError("se requiere R >= 1 y 1 <= n0 <= n")
    rho = rondas_sin_tope(R, n0, n)
    sin = 2 ** R * n0 * rho + n * (2 ** (R - rho + 1) - 2)
    con = 2 ** (R - 1) * n0 * rho + n * (2 ** (R - rho) - 1) + min(n0 * 2 ** (R - 1), n)
    return {"rho": rho, "sin_reutilizar": sin, "con_reutilizar": con}


def costo_enunciado(num_candidatos, n0):
    """La fórmula del enunciado, |C| · n₀ · log₂|C| (sin tope; real si |C| no es potencia de 2)."""
    return num_candidatos * n0 * math.log2(num_candidatos)


# ---------------------------------------------------------------- algoritmo

@dataclass
class ResultadoSH:
    ganador: dict
    precision_ganador: float            # sobre las n instancias
    rondas: list = field(default_factory=list)
    consultas_cobradas: int = 0         # nuevas (con caché)
    consultas_solicitadas: int = 0      # sin reutilizar (incluye completar al ganador)
    segundos_cpu: float = 0.0
    orden_instancias: list = field(default_factory=list)


def successive_halving(oraculo, candidatos, *, n0, n=None, semilla_instancias, semilla=1,
                       instancias=None, evaluar_ganador=True):
    """Algoritmo 2 sobre la lista ``candidatos``. Devuelve un ``ResultadoSH``.

    ``semilla_instancias`` fija la permutación de las instancias (muestras anidadas).
    Si ``evaluar_ganador``, el ganador se evalúa al final sobre las n instancias.
    """
    instancias = oraculo.instancias if instancias is None else list(instancias)
    n = len(instancias) if n is None else n
    if not 1 <= n <= len(instancias):
        raise ValueError("n debe estar entre 1 y el número de instancias")
    candidatos = list(candidatos)
    if not candidatos:
        raise ValueError("no hay candidatos")
    orden = random.Random(semilla_instancias).sample(instancias, len(instancias))[:n]
    consultas_antes, solicitadas_antes = oraculo.consultas, oraculo.consultas_solicitadas
    vivos, rondas, r = candidatos, [], 0
    with Cronometro() as reloj:
        while len(vivos) > 1:
            n_r = min(n0 * 2 ** r, n)
            muestra = orden[:n_r]
            antes = oraculo.consultas
            puntajes = [oraculo.evaluar(c, muestra, semilla=semilla).precision for c in vivos]
            orden_ronda = sorted(range(len(vivos)), key=lambda j: (-puntajes[j], j))
            quedan = math.ceil(len(vivos) / 2)
            rondas.append({"ronda": r, "candidatos": len(vivos), "n_r": n_r,
                           "consultas_nuevas": oraculo.consultas - antes,
                           "mejor_puntaje": puntajes[orden_ronda[0]], "corte": puntajes[orden_ronda[quedan - 1]]})
            vivos = [vivos[j] for j in sorted(orden_ronda[:quedan])]       # conserva el orden relativo
            r += 1
        ganador = vivos[0]
        p = oraculo.evaluar(ganador, orden, semilla=semilla).precision if evaluar_ganador else None
    return ResultadoSH(ganador=ganador, precision_ganador=p, rondas=rondas,
                       consultas_cobradas=oraculo.consultas - consultas_antes,
                       consultas_solicitadas=oraculo.consultas_solicitadas - solicitadas_antes,
                       segundos_cpu=reloj.segundos, orden_instancias=[x["id"] for x in orden])


# ---------------------------------------------------------------- probabilidad de eliminar a la mejor

def cota_eliminar_mejor(precisiones, n0, n, poblacion=None):
    """Cota superior de la probabilidad de que Successive Halving elimine a la mejor configuración.

    ``precisiones``: precisión verdadera de cada candidato sobre la población de
    ``poblacion`` instancias (por defecto n: las instancias de búsqueda). Argumento
    (Karnin, Koren y Somekh, 2013), ronda por ronda, con muestras sin reemplazo de
    la población (Hoeffding, 1963, que vale también sin reemplazo):

    - Para un competidor j con brecha Δ_j = μ* − μ_j ≥ 0, evaluados los dos sobre las
      mismas n_r instancias, P(μ̂_j ≥ μ̂*) ≤ exp(−n_r Δ_j² / 2), porque la diferencia
      por instancia está en [−1, 1].
    - La mejor sale en la ronda r solo si al menos ⌈|S_r|/2⌉ de los otros la igualan o
      superan. Por la desigualdad de Markov y tomando como competidores, en el peor
      caso, los |S_r| − 1 de menor brecha:
      P_r ≤ min(1, Σ_{j=1}^{|S_r|−1} exp(−n_r Δ_(j)² / 2) / ⌈|S_r|/2⌉).
    - Si n_r es toda la población, la medición es exacta: sobrevive siempre una
      configuración de precisión máxima y P_r = 0.
    - Unión sobre las rondas: P(el ganador no es óptimo) ≤ Σ_r P_r. En las rondas con
      muestra, los competidores empatados con la mejor (Δ = 0) aportan 1 cada uno
      (en el peor caso se cuentan en contra), lo que hace la cota conservadora.

    Devuelve la cota total (sin recortar a 1) y la de cada ronda.
    """
    poblacion = n if poblacion is None else poblacion
    mejor = max(precisiones)
    brechas = sorted(mejor - p for p in precisiones)[1:]       # sin la mejor (la primera brecha 0)
    por_ronda = []
    for s, n_r in rondas_sh(len(precisiones), n0, n):
        if n_r >= poblacion:
            por_ronda.append(0.0)
            continue
        suma = sum(math.exp(-n_r * b * b / 2) for b in brechas[: s - 1])
        por_ronda.append(min(1.0, suma / math.ceil(s / 2)))
    return {"cota": sum(por_ronda), "por_ronda": por_ronda}
