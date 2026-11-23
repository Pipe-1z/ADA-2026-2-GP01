"""Algoritmo 1: backtracking con poda por cota superior (exacto).

Recorre en profundidad el árbol de decisiones de las ranuras: el nodo de nivel d
es una asignación parcial de las primeras d ranuras; la raíz (d = 0) no tiene
ninguna fija y las hojas (d = m) son las configuraciones completas.

- En cada **nodo interno** (d < m) calcula una cota superior optimista
  ``UB(σ)`` de la precisión de cualquier configuración que extienda σ. Si
  ``UB(σ) <= mejor`` (la mejor precisión ya encontrada), descarta todo el
  subárbol: ninguna de sus hojas puede **superar** a la mejor.
- En cada **hoja** consulta al oráculo sobre las n instancias (n consultas) y
  actualiza la mejor si la supera estrictamente.

Los hijos se generan en orden creciente de índice (``orden_hijos="indice"``) o
de mayor a menor cota (``orden_hijos="cota"``). Con ``"indice"`` las hojas se
visitan en orden lexicográfico y el resultado es la **primera** configuración
óptima en ese orden, la misma que devuelve la fuerza bruta.

La cota la da el oráculo (``oraculo.cota_superior(parcial)``). En el sintético es
la fracción de instancias vivas, que es admisible en los dos modelos porque
fijar más ranuras solo puede hacer fallar más instancias (ver
``docs/derivaciones/algoritmo1_backtracking.md``). El oráculo real no tiene una
cota exacta conocida.

Costo en el peor caso (ninguna poda): el árbol tiene N_d = k^d nodos en el nivel
d, k^m = |C| hojas que cuestan n consultas cada una y (k^m − 1)/(k − 1) nodos
internos que cuestan una cota cada uno, O(n) cada una:

    T(|C|, n) = n·|C| + c·n·(|C| − 1)/(k − 1) = Θ(|C| · n)
"""

from dataclasses import dataclass, field

from ..medicion import Cronometro


def nodos_por_nivel_peor_caso(opciones_por_ranura):
    """[N_0, ..., N_m] con N_d = ∏_{p<d} k_p (número de nodos del nivel d sin poda)."""
    niveles = [1]
    for k in opciones_por_ranura:
        niveles.append(niveles[-1] * k)
    return niveles


@dataclass
class ResultadoBacktracking:
    mejor_config: dict
    mejor_precision: float
    nodos_por_nivel: list = field(default_factory=list)       # nodos explorados (sacados de la pila) por nivel
    podados_por_nivel: list = field(default_factory=list)     # nodos internos cuyo subárbol se descartó
    nodos_por_nivel_peor_caso: list = field(default_factory=list)
    hojas_evaluadas: int = 0
    cotas_calculadas: int = 0
    instancias: int = 0
    consultas_cobradas: int = 0
    consultas_solicitadas: int = 0
    segundos_cpu: float = 0.0

    @property
    def nodos_explorados(self):
        return sum(self.nodos_por_nivel)

    @property
    def nodos_peor_caso(self):
        return sum(self.nodos_por_nivel_peor_caso)

    @property
    def consultas_peor_caso(self):
        return self.nodos_por_nivel_peor_caso[-1] * self.instancias

    def resumen(self):
        return {
            "mejor_config": self.mejor_config, "mejor_precision": self.mejor_precision,
            "nodos_explorados": self.nodos_explorados, "nodos_peor_caso": self.nodos_peor_caso,
            "fraccion_nodos": self.nodos_explorados / self.nodos_peor_caso,
            "hojas_evaluadas": self.hojas_evaluadas, "hojas_peor_caso": self.nodos_por_nivel_peor_caso[-1],
            "fraccion_hojas": self.hojas_evaluadas / self.nodos_por_nivel_peor_caso[-1],
            "cotas_calculadas": self.cotas_calculadas,
            "consultas_cobradas": self.consultas_cobradas, "consultas_solicitadas": self.consultas_solicitadas,
            "consultas_peor_caso": self.consultas_peor_caso,
            "fraccion_consultas": self.consultas_solicitadas / self.consultas_peor_caso,
            "nodos_por_nivel": self.nodos_por_nivel, "podados_por_nivel": self.podados_por_nivel,
            "nodos_por_nivel_peor_caso": self.nodos_por_nivel_peor_caso,
            "segundos_cpu": self.segundos_cpu,
        }


def backtracking(oraculo, *, instancias=None, semilla=1, orden_hijos="indice", podar=True, temperatura=None):
    """Algoritmo 1. Devuelve un ``ResultadoBacktracking``.

    ``podar=False`` desactiva la poda (recorre el árbol completo: sirve para
    comprobar el conteo del peor caso).
    """
    if orden_hijos not in ("indice", "cota"):
        raise ValueError("orden_hijos debe ser 'indice' o 'cota'")
    if not hasattr(oraculo, "cota_superior"):
        raise ValueError("este oráculo no ofrece una cota superior (solo el sintético la tiene)")
    instancias = oraculo.instancias if instancias is None else list(instancias)
    if len(instancias) != oraculo.n and podar:
        raise ValueError("la cota se calcula sobre todas las instancias del oráculo")
    ranuras = oraculo.ranuras
    m = len(ranuras)
    opciones = [oraculo.opciones[r] for r in ranuras]
    temperatura = oraculo.temperaturas[0] if temperatura is None else temperatura

    nodos = [0] * (m + 1)
    podados = [0] * (m + 1)
    hojas = cotas = 0
    mejor_p, mejor_c = -1.0, None
    consultas_antes, solicitadas_antes = oraculo.consultas, oraculo.consultas_solicitadas

    with Cronometro() as reloj:
        # Invariante del ciclo (ver la derivación): los nodos de la pila y los subárboles ya
        # visitados o descartados particionan el espacio C; mejor_p es la mayor precisión entre
        # las hojas visitadas, y ninguna hoja de un subárbol descartado la supera.
        pila = [((), 1.0)]                       # (asignación parcial, cota del padre)
        while pila:
            parcial, cota_padre = pila.pop()
            d = len(parcial)
            nodos[d] += 1
            if d == m:
                # Una hoja no tiene cota propia: se usa la de su padre (la mejor pudo subir
                # después de que el padre se expandió).
                if podar and cota_padre <= mejor_p:
                    podados[d] += 1
                    continue
                config = oraculo.config(parcial, temperatura=temperatura)
                p = oraculo.evaluar(config, instancias, semilla=semilla).precision
                hojas += 1
                if p > mejor_p:
                    mejor_p, mejor_c = p, config
                continue
            ub = 1.0
            if podar:
                ub = oraculo.cota_superior(parcial)
                cotas += 1
                if ub <= mejor_p:
                    podados[d] += 1
                    continue
            hijos = [parcial + (a,) for a in opciones[d]]
            if orden_hijos == "cota" and d + 1 < m:
                valores = {h: oraculo.cota_superior(h) for h in hijos}
                cotas += len(hijos)
                hijos.sort(key=lambda h: -valores[h])          # estable: en empate, el índice menor
            pila.extend((h, ub) for h in reversed(hijos))      # el primero de la lista sale primero

    return ResultadoBacktracking(
        mejor_config=mejor_c, mejor_precision=mejor_p, nodos_por_nivel=nodos, podados_por_nivel=podados,
        nodos_por_nivel_peor_caso=nodos_por_nivel_peor_caso([len(o) for o in opciones]),
        hojas_evaluadas=hojas, cotas_calculadas=cotas, instancias=len(instancias),
        consultas_cobradas=oraculo.consultas - consultas_antes,
        consultas_solicitadas=oraculo.consultas_solicitadas - solicitadas_antes,
        segundos_cpu=reloj.segundos,
    )
