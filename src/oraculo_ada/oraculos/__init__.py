"""Oráculos con interfaz común: sintético (``sintetico``) y envoltura del oráculo del curso (``real``)."""

from .base import (
    OraculoBase,
    PresupuestoAgotado,
    Resultado,
    fallos_por_familia,
    familia,
    mejor_evaluacion_completa,
)
from .sintetico import (
    OraculoSintetico,
    desde_3sat,
    generar_3sat,
    generar_calibrado,
    generar_conjuntivo,
    generar_disyuntivo,
    generar_peor_caso_backtracking,
)

__all__ = [
    "OraculoBase",
    "OraculoSintetico",
    "PresupuestoAgotado",
    "Resultado",
    "desde_3sat",
    "fallos_por_familia",
    "familia",
    "generar_3sat",
    "generar_calibrado",
    "generar_conjuntivo",
    "generar_disyuntivo",
    "generar_peor_caso_backtracking",
    "mejor_evaluacion_completa",
]
