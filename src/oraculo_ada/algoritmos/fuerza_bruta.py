"""Fuerza bruta: evalúa todas las configuraciones sobre todas las instancias.

Es el algoritmo exacto de referencia y el **peor caso** contra el que se comparan
los demás. Su costo en consultas es exactamente

    T(|C|, n) = |C| · n

(cada una de las |C| configuraciones se evalúa sobre las n instancias). Ese es
el número de consultas que **cobraría con el oráculo real**, y se reporta
siempre en ``consultas_oraculo_real``, también cuando se usa la verdad conocida
del oráculo sintético (``verdad_conocida=True``), que no cobra consultas.

Empates: gana la primera configuración en orden lexicográfico de índices; se
devuelven además todas las óptimas.
"""

from dataclasses import dataclass, field

from ..medicion import Cronometro
from ..oraculos.base import PresupuestoAgotado


@dataclass
class ResultadoFuerzaBruta:
    mejor_config: dict
    mejor_precision: float
    optimas: list = field(default_factory=list)
    configuraciones_evaluadas: int = 0
    instancias: int = 0
    consultas_oraculo_real: int = 0       # |C| · n: lo que cobraría el oráculo real
    consultas_cobradas: int = 0           # consultas nuevas que cobró este oráculo
    consultas_solicitadas: int = 0
    segundos_cpu: float = 0.0             # tiempo de pared de esta ejecución (no es tiempo de GPU)
    presupuesto: int = None
    presupuesto_agotado: bool = False

    def resumen(self):
        return {
            "mejor_config": self.mejor_config, "mejor_precision": self.mejor_precision,
            "num_optimas": len(self.optimas), "configuraciones_evaluadas": self.configuraciones_evaluadas,
            "instancias": self.instancias, "consultas_oraculo_real": self.consultas_oraculo_real,
            "consultas_cobradas": self.consultas_cobradas, "consultas_solicitadas": self.consultas_solicitadas,
            "segundos_cpu": self.segundos_cpu,
        }


def fuerza_bruta(oraculo, instancias=None, *, semilla=1, con_temperatura=False, verdad_conocida=False,
                 presupuesto=None, modo_presupuesto="nuevas"):
    """Recorre todo el espacio y devuelve la mejor configuración.

    ``verdad_conocida=True`` (solo oráculo sintético) usa ``precision_exacta``: no
    cobra consultas ni tiene ruido, pero ``consultas_oraculo_real`` sigue siendo |C| · n.

    ``presupuesto`` (B): si una evaluación lo superaría, se detiene antes de hacerla y devuelve
    la mejor de las evaluadas (``None`` si no alcanzó para ninguna). Ya no es exacta.
    """
    instancias = oraculo.instancias if instancias is None else list(instancias)
    if verdad_conocida and not hasattr(oraculo, "precision_exacta"):
        raise ValueError("verdad_conocida solo existe en el oráculo sintético")
    consultas_antes = oraculo.consultas
    solicitadas_antes = oraculo.consultas_solicitadas
    mejor_p, optimas, evaluadas, agotado = -1.0, [], 0, False
    with Cronometro() as reloj, oraculo.presupuesto(presupuesto, modo_presupuesto) as tope:
        try:
            for config in oraculo.espacio(con_temperatura=con_temperatura):
                if verdad_conocida:
                    p = oraculo.precision_exacta(config, instancias)
                else:
                    p = oraculo.evaluar(config, instancias, semilla=semilla).precision
                evaluadas += 1
                if p > mejor_p:
                    mejor_p, optimas = p, [config]
                elif p == mejor_p:
                    optimas.append(config)
        except PresupuestoAgotado as e:
            if tope is None or e.tope_id != tope:
                raise
            agotado = True
    return ResultadoFuerzaBruta(
        mejor_config=optimas[0] if optimas else None, mejor_precision=mejor_p if optimas else None,
        optimas=optimas, presupuesto=presupuesto, presupuesto_agotado=agotado,
        configuraciones_evaluadas=evaluadas, instancias=len(instancias),
        consultas_oraculo_real=evaluadas * len(instancias),
        consultas_cobradas=oraculo.consultas - consultas_antes,
        consultas_solicitadas=oraculo.consultas_solicitadas - solicitadas_antes,
        segundos_cpu=reloj.segundos,
    )
