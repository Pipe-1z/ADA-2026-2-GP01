"""Oráculo restringido a un subespacio: solo algunas opciones por ranura (Fase 7).

Delega cada evaluación en el oráculo base (con su caché, su libro de consultas y su
contador), pero solo admite configuraciones cuyas opciones están en ``opciones``. Así los
algoritmos (fuerza bruta, coordenadas, SH, reparto) recorren el subespacio sin cambios.
"""

import random

from .base import OraculoBase


def sortear_subespacio(oraculo, opciones_por_ranura, semilla):
    """Para cada ranura, ``opciones_por_ranura`` opciones elegidas al azar (sin otro criterio)."""
    rng = random.Random(semilla)
    return {r: sorted(rng.sample(list(oraculo.opciones[r]), opciones_por_ranura)) for r in oraculo.ranuras}


class OraculoSubespacio(OraculoBase):
    def __init__(self, base, opciones):
        for r in base.ranuras:
            if not set(opciones[r]) <= set(base.opciones[r]):
                raise ValueError(f"opciones fuera del espacio en la ranura {r}")
        super().__init__(base.ranuras, opciones, base.instancias, base.temperaturas)
        self.base = base

    def costo_evaluacion(self, config, instancias=None, semilla=1):
        return self.base.costo_evaluacion(config, self.instancias if instancias is None else instancias, semilla)

    def _evaluar(self, config, instancias, semilla):
        r = self.base.evaluar(config, instancias, semilla=semilla)
        return r.aciertos, r.trazas, r.consultas_nuevas
