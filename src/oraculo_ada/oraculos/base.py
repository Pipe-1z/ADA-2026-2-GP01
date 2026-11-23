"""Interfaz común de los oráculos.

Todos los algoritmos reciben un objeto de esta clase, de modo que corren igual
con el oráculo sintético y con el oráculo real del curso (CLAUDE.md §7).

Una **configuración** es un diccionario ``{ranura: índice, ..., "temperatura": t}``,
con la misma forma que las del oráculo del curso. Una **instancia** es un
diccionario con al menos la llave ``"id"``.

La operación básica que se cuenta es la **consulta**: evaluar una configuración
sobre una instancia. Cada oráculo lleva dos contadores:

- ``consultas``: consultas **nuevas**, las que de verdad cuestan (generación en
  GPU en el real). Una consulta ya hecha (misma configuración, instancia y
  semilla) la responde el caché y no se vuelve a cobrar.
- ``consultas_solicitadas``: todas las consultas pedidas, nuevas o repetidas.
"""

import itertools
import math
from collections import Counter
from dataclasses import dataclass, field

from ..medicion import Cronometro


@dataclass
class Resultado:
    """Lo que devuelve ``evaluar``.

    ``trazas`` trae solo los fallos, como el oráculo del curso: una entrada por
    instancia fallida con ``id``, ``violo`` (primera restricción incumplida) y
    ``salida`` (texto generado; ``None`` en el sintético).
    """

    aciertos: int
    n: int
    trazas: list = field(default_factory=list)
    consultas_nuevas: int = 0
    segundos: float = 0.0

    @property
    def precision(self):
        return self.aciertos / self.n if self.n else 0.0


def familia(violo):
    """Familia de una restricción: el prefijo antes de ``:`` (``startend:end_checker`` → ``startend``)."""
    return str(violo).split(":")[0]


def fallos_por_familia(resultado):
    """``Counter`` familia → número de instancias cuya primera restricción violada es de esa familia."""
    return Counter(familia(t["violo"]) for t in resultado.trazas)


class OraculoBase:
    """Base de los oráculos: valida configuraciones, cuenta consultas y mide tiempo.

    Las subclases implementan ``_evaluar(config, instancias, semilla)``, que
    devuelve ``(aciertos, trazas, consultas_nuevas)``.
    """

    def __init__(self, ranuras, opciones, instancias, temperaturas=(0.0,)):
        self.ranuras = list(ranuras)
        self.opciones = {r: list(opciones[r]) for r in self.ranuras}
        self.instancias = list(instancias)
        self.temperaturas = tuple(float(t) for t in temperaturas)
        self.reiniciar_contadores()

    # ---- espacio de configuraciones -----------------------------------

    @property
    def m(self):
        """Número de ranuras."""
        return len(self.ranuras)

    @property
    def n(self):
        """Número de instancias del conjunto por defecto."""
        return len(self.instancias)

    def tamano_espacio(self, con_temperatura=False):
        """|C| = ∏ k_p (por |T| si se incluye la temperatura)."""
        t = len(self.temperaturas) if con_temperatura else 1
        return math.prod(len(self.opciones[r]) for r in self.ranuras) * t

    def config(self, indices=None, temperatura=0.0, **por_nombre):
        """Construye una configuración válida.

        ``config([0, 0, 0, 5, 1])`` o ``config(rol=0, ..., cierre=1)``; las ranuras
        no indicadas toman su primera opción.
        """
        if indices is not None:
            if len(indices) != self.m:
                raise ValueError(f"se esperaban {self.m} índices y llegaron {len(indices)}")
            por_nombre = dict(zip(self.ranuras, indices))
        c = {r: int(por_nombre.get(r, self.opciones[r][0])) for r in self.ranuras}
        c["temperatura"] = float(temperatura)
        self.validar_config(c)
        return c

    def validar_config(self, config):
        for r in self.ranuras:
            if r not in config:
                raise ValueError(f"falta la ranura {r!r}")
            if config[r] not in self.opciones[r]:
                raise ValueError(f"{r} = {config[r]!r} no es una opción válida {self.opciones[r]}")
        extra = set(config) - set(self.ranuras) - {"temperatura"}
        if extra:
            raise ValueError(f"llaves desconocidas: {sorted(extra)}")
        if float(config.get("temperatura", 0.0)) not in self.temperaturas:
            raise ValueError(f"temperatura {config.get('temperatura')!r} no está en {self.temperaturas}")

    def clave(self, config):
        """Tupla (índices..., temperatura) que identifica una configuración."""
        return tuple(config[r] for r in self.ranuras) + (float(config.get("temperatura", 0.0)),)

    def espacio(self, con_temperatura=False):
        """Itera todas las configuraciones (en orden lexicográfico de índices)."""
        temps = self.temperaturas if con_temperatura else (self.temperaturas[0],)
        for combo in itertools.product(*(self.opciones[r] for r in self.ranuras)):
            for t in temps:
                yield self.config(combo, temperatura=t)

    # ---- consulta -----------------------------------------------------

    def evaluar(self, config, instancias=None, semilla=1):
        """Evalúa ``config`` sobre ``instancias`` (por defecto, ``self.instancias``)."""
        self.validar_config(config)
        instancias = self.instancias if instancias is None else list(instancias)
        if not instancias:
            raise ValueError("no hay instancias que evaluar")
        with Cronometro() as reloj:
            aciertos, trazas, nuevas = self._evaluar(config, instancias, semilla)
        self.consultas += nuevas
        self.consultas_solicitadas += len(instancias)
        self.evaluaciones += 1
        self.segundos += reloj.segundos
        self.historial.append({
            "config": dict(config), "semilla": semilla, "instancias": len(instancias),
            "aciertos": aciertos, "consultas_nuevas": nuevas, "segundos": reloj.segundos,
        })
        return Resultado(aciertos=aciertos, n=len(instancias), trazas=trazas,
                         consultas_nuevas=nuevas, segundos=reloj.segundos)

    def _evaluar(self, config, instancias, semilla):  # pragma: no cover - abstracto
        raise NotImplementedError

    # ---- contadores ---------------------------------------------------

    def reiniciar_contadores(self):
        """Pone a cero los contadores (el caché, si existe, se conserva)."""
        self.consultas = 0
        self.consultas_solicitadas = 0
        self.evaluaciones = 0
        self.segundos = 0.0
        self.historial = []

    def contadores(self):
        return {
            "consultas": self.consultas,
            "consultas_solicitadas": self.consultas_solicitadas,
            "evaluaciones": self.evaluaciones,
            "segundos": self.segundos,
        }
