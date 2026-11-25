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
from contextlib import contextmanager
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


def mejor_evaluacion_completa(oraculo, desde=0, n=None):
    """(config, precisión) de la mejor evaluación sobre ``n`` instancias en ``oraculo.historial[desde:]``.

    Es la "mejor configuración encontrada" que devuelve un algoritmo cuando se le agota el
    presupuesto. (None, None) si no hubo ninguna evaluación completa.
    """
    n = oraculo.n if n is None else n
    completas = [h for h in oraculo.historial[desde:] if h["instancias"] == n and not h.get("validacion")]
    if not completas:
        return None, None
    h = max(completas, key=lambda x: x["aciertos"])          # en empate, la primera
    return dict(h["config"]), h["aciertos"] / n


def fallos_por_familia(resultado):
    """``Counter`` familia → número de instancias cuya primera restricción violada es de esa familia."""
    return Counter(familia(t["violo"]) for t in resultado.trazas)


class PresupuestoAgotado(RuntimeError):
    """Una evaluación superaría el presupuesto B: se lanza ANTES de consultar.

    ``tope_id`` identifica el presupuesto que se habría superado, para que cada
    algoritmo atrape solo el suyo (los presupuestos se pueden anidar).
    """

    def __init__(self, mensaje, tope_id=None, costo=0, restante=0):
        super().__init__(mensaje)
        self.tope_id, self.costo, self.restante = tope_id, costo, restante


class _Tope:
    """Un presupuesto abierto: B consultas en modo "nuevas" (desde ``inicio``) o "propias" (``vistas``)."""

    def __init__(self, id_, modo, B, inicio):
        self.id, self.modo, self.B, self.inicio, self.vistas = id_, modo, B, inicio, set()

    def usadas(self, oraculo):
        return oraculo.consultas - self.inicio if self.modo == "nuevas" else len(self.vistas)

    def restante(self, oraculo):
        return self.B - self.usadas(oraculo)


class OraculoBase:
    """Base de los oráculos: valida configuraciones, cuenta consultas, mide tiempo y controla presupuestos.

    Las subclases implementan ``_evaluar(config, instancias, semilla)``, que
    devuelve ``(aciertos, trazas, consultas_nuevas)``, y ``costo_evaluacion``,
    que dice cuántas consultas nuevas cobraría una evaluación **sin hacerla**.

    **Presupuesto B** (CLAUDE.md, ítem 7 de la retroalimentación): ``with
    oraculo.presupuesto(B) as tope:`` limita a B las consultas nuevas desde ese
    momento. Antes de cada evaluación se calcula su costo; si superaría el
    presupuesto restante (el más estricto de los abiertos), se lanza
    ``PresupuestoAgotado`` y no se consulta.
    """

    def __init__(self, ranuras, opciones, instancias, temperaturas=(0.0,)):
        self.ranuras = list(ranuras)
        self.opciones = {r: list(opciones[r]) for r in self.ranuras}
        self.instancias = list(instancias)
        self.temperaturas = tuple(float(t) for t in temperaturas)
        self._topes = []                       # pila de presupuestos abiertos (_Tope)
        self._siguiente_tope = 0
        self.reiniciar_contadores()

    # ---- presupuesto ---------------------------------------------------

    def costo_evaluacion(self, config, instancias=None, semilla=1):
        """Consultas nuevas que cobraría ``evaluar(config, instancias, semilla)``. Por defecto, todas."""
        return len(self.instancias if instancias is None else instancias)

    @contextmanager
    def presupuesto(self, B, modo="nuevas"):
        """Abre un presupuesto de B consultas. ``B = None``: sin presupuesto propio.

        ``modo``:
        - ``"nuevas"``: cuenta las consultas nuevas para el oráculo (las que no están en su
          caché). Es el costo real en GPU; se usa con el modelo real.
        - ``"propias"``: cuenta las consultas que la corrida pide por primera vez dentro de este
          presupuesto, como si empezara con el caché vacío (una consulta repetida dentro de la
          corrida no se vuelve a contar). Sirve para comparar algoritmos sobre configuraciones
          que ya están en el caché (por ejemplo, el subespacio de la Fase 7).
        """
        if B is None:
            yield None
            return
        if B < 0:
            raise ValueError("el presupuesto no puede ser negativo")
        if modo not in ("nuevas", "propias"):
            raise ValueError("modo debe ser 'nuevas' o 'propias'")
        self._siguiente_tope += 1
        tope = _Tope(self._siguiente_tope, modo, B, self.consultas)
        self._topes.append(tope)
        try:
            yield tope.id
        finally:
            self._topes.remove(tope)

    def fijar_tope_absoluto(self, limite):
        """Tope permanente de consultas nuevas para toda la vida del oráculo (None lo quita)."""
        self._topes = [t for t in self._topes if t.id != 0]
        if limite is not None:
            self._topes.insert(0, _Tope(0, "nuevas", limite, 0))

    def restante(self):
        """Consultas que quedan según el presupuesto más estricto abierto (None si no hay)."""
        return min((t.restante(self) for t in self._topes), default=None)

    def _claves_consulta(self, config, instancias, semilla):
        clave = self.clave(config)
        return [(clave, x["id"], semilla) for x in instancias]

    def _verificar_presupuesto(self, config, instancias, semilla):
        if not self._topes:
            return
        costo_nuevas = None
        claves = None
        # El más interno que se superaría es el que corta (cada algoritmo atrapa el suyo).
        for tope in reversed(self._topes):
            if tope.modo == "nuevas":
                if costo_nuevas is None:
                    costo_nuevas = self.costo_evaluacion(config, instancias, semilla)
                costo = costo_nuevas
            else:
                claves = claves or self._claves_consulta(config, instancias, semilla)
                costo = sum(1 for k in claves if k not in tope.vistas)
            if costo > tope.restante(self):
                raise PresupuestoAgotado(
                    f"la evaluación cuesta {costo} consultas ({tope.modo}) y quedan {tope.restante(self)}",
                    tope_id=tope.id, costo=costo, restante=tope.restante(self))

    def _anotar_presupuesto(self, config, instancias, semilla):
        propias = [t for t in self._topes if t.modo == "propias"]
        if propias:
            claves = self._claves_consulta(config, instancias, semilla)
            for t in propias:
                t.vistas.update(claves)

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
        self._verificar_presupuesto(config, instancias, semilla)
        with Cronometro() as reloj:
            aciertos, trazas, nuevas = self._evaluar(config, instancias, semilla)
        self._anotar_presupuesto(config, instancias, semilla)
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
