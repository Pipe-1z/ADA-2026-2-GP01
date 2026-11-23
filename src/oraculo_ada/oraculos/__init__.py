"""Oráculos con interfaz común: sintético (``sintetico``) y envoltura del oráculo del curso (``real``)."""

from .base import OraculoBase, Resultado, fallos_por_familia, familia
from .sintetico import (
    OraculoSintetico,
    desde_3sat,
    generar_3sat,
    generar_calibrado,
    generar_conjuntivo,
    generar_disyuntivo,
)

__all__ = [
    "OraculoBase",
    "OraculoSintetico",
    "Resultado",
    "desde_3sat",
    "fallos_por_familia",
    "familia",
    "generar_3sat",
    "generar_calibrado",
    "generar_conjuntivo",
    "generar_disyuntivo",
]
