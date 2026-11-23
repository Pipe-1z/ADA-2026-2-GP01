"""Algoritmos del proyecto: fuerza bruta (exacto de referencia) y Algoritmos 1 a 4."""

from .backtracking import ResultadoBacktracking, backtracking, nodos_por_nivel_peor_caso
from .coordenadas import ResultadoCoordenadas, ascenso_coordenadas, cota_consultas_coordenadas
from .estrategias import dos_ranuras_sh, muestra_configuraciones, sh_muestra, vecindario_doble
from .fuerza_bruta import ResultadoFuerzaBruta, fuerza_bruta
from .successive_halving import (
    ResultadoSH,
    costo_enunciado,
    costo_sh,
    costo_sh_cerrado,
    cota_eliminar_mejor,
    successive_halving,
)

__all__ = [
    "ResultadoBacktracking",
    "backtracking",
    "nodos_por_nivel_peor_caso",
    "ResultadoCoordenadas",
    "ResultadoFuerzaBruta",
    "ascenso_coordenadas",
    "cota_consultas_coordenadas",
    "fuerza_bruta",
    "ResultadoSH",
    "costo_enunciado",
    "costo_sh",
    "costo_sh_cerrado",
    "cota_eliminar_mejor",
    "dos_ranuras_sh",
    "muestra_configuraciones",
    "sh_muestra",
    "successive_halving",
    "vecindario_doble",
]
