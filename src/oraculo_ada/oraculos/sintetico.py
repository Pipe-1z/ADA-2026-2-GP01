"""Oráculo sintético con estructura conocida (CLAUDE.md §7.1).

Sirve para medir los algoritmos con n y |C| crecientes sin gastar GPU y para
tener casos con óptimo conocido. Tiene dos modelos:

**Conjuntivo** (descripción del curso). Hay un conjunto de familias de
restricciones. Cada opción ``a`` de la ranura ``p`` rompe un subconjunto
``R(p, a)`` de familias (vacío si la opción es "limpia"). Cada instancia trae
2 o 3 familias y pasa si **ninguna** de sus familias está rota.

**Disyuntivo** (el de la reducción desde 3-SAT). Cada instancia ``i`` trae un
conjunto ``L_i`` de pares ``(p, a)`` y pasa si la configuración contiene **al
menos uno**. Con ``k = 2`` y tres pares sobre ranuras distintas, cada instancia
es una cláusula de 3-SAT (opción 1 = verdadero, 0 = falso).

**Interacciones que solo rompen** (los dos modelos). Una interacción es un par de
opciones de ranuras distintas ``((p, a), (q, b))`` que, cuando aparecen juntas
en la configuración, hacen fallar instancias: en el conjuntivo rompen familias
adicionales; en el disyuntivo hacen fallar un conjunto fijo de instancias.
Nunca hacen pasar una instancia. Por eso, en los dos modelos, que una instancia
pase es una propiedad **monótona**: si falla con las ranuras ya fijadas, sigue
fallando al fijar las demás (la cota del Algoritmo 1 se apoya en esto).

**Ruido** (Parte 2). Con probabilidad ``ruido`` una consulta devuelve el
resultado contrario. El volteo depende de (configuración, instancia, semilla de
la consulta) de forma determinista, igual que el caché del oráculo real: la misma
consulta siempre da lo mismo, y repetir la medición exige otra semilla.

Todo se genera con un ``random.Random(semilla)`` propio, así que la misma semilla
da exactamente el mismo oráculo.
"""

import itertools
import math
import random

from .base import OraculoBase

MODELOS = ("conjuntivo", "disyuntivo")
LIMITE_FUERZA_BRUTA = 2 ** 20   # configuraciones; más allá, optimo_exacto se niega


class OraculoSintetico(OraculoBase):
    """Oráculo sintético. Se construye con ``generar_conjuntivo``, ``generar_disyuntivo``,
    ``generar_3sat`` o ``desde_3sat``; el constructor recibe la estructura ya armada.

    Parámetros
    ----------
    modelo : "conjuntivo" o "disyuntivo".
    m, k : ranuras y opciones por ranura (opciones 0..k-1).
    rompe : (conjuntivo) dict ``(p, a) → frozenset`` de familias que rompe la opción.
    familias_instancia : (conjuntivo) lista, por instancia, de la tupla ordenada de sus familias.
    literales : (disyuntivo) lista, por instancia, de la tupla de pares ``(p, a)`` que la hacen pasar.
    interacciones : lista de ``((p, a), (q, b), conjunto)``; el conjunto son familias
        (conjuntivo) o ids de instancia (disyuntivo).
    ruido : probabilidad de que una consulta devuelva el resultado contrario.
    semilla_ruido : semilla del ruido.
    cache : si es ``True``, una consulta repetida no se vuelve a cobrar.
    ranuras : nombres de las ranuras (por defecto ``r0``, ``r1``, ...).
    temperaturas : niveles de temperatura admitidos (no afectan el resultado).
    parametros : diccionario con los parámetros de generación (para el registro).
    """

    def __init__(self, modelo, m, k, *, rompe=None, familias_instancia=None, literales=None,
                 interacciones=(), ruido=0.0, semilla_ruido=0, cache=True, ranuras=None,
                 temperaturas=(0.0,), parametros=None):
        if modelo not in MODELOS:
            raise ValueError(f"modelo debe ser uno de {MODELOS}")
        if m < 1 or k < 1:
            raise ValueError("m y k deben ser positivos")
        if not 0.0 <= ruido <= 1.0:
            raise ValueError("ruido debe estar en [0, 1]")
        self.modelo = modelo
        self.k = k
        self.ruido = float(ruido)
        self.semilla_ruido = semilla_ruido
        self.usa_cache = cache
        self.parametros = dict(parametros or {})
        self._vistas = set()

        if modelo == "conjuntivo":
            if rompe is None or familias_instancia is None:
                raise ValueError("el modelo conjuntivo necesita rompe y familias_instancia")
            faltan = [(p, a) for p in range(m) for a in range(k) if (p, a) not in rompe]
            if faltan:
                raise ValueError(f"faltan opciones en rompe: {faltan[:5]}")
            self.rompe = {pa: frozenset(f) for pa, f in rompe.items()}
            self.familias_instancia = [tuple(f) for f in familias_instancia]
            n = len(self.familias_instancia)
        else:
            if literales is None:
                raise ValueError("el modelo disyuntivo necesita literales")
            self.literales = [tuple((int(p), int(a)) for p, a in L) for L in literales]
            for L in self.literales:
                for p, a in L:
                    if not (0 <= p < m and 0 <= a < k):
                        raise ValueError(f"par fuera de rango: {(p, a)}")
            n = len(self.literales)
        if n == 0:
            raise ValueError("no hay instancias")

        self.interacciones = []
        for (p, a), (q, b), conjunto in interacciones:
            if p == q:
                raise ValueError("una interacción une opciones de ranuras distintas")
            if not (0 <= p < m and 0 <= q < m and 0 <= a < k and 0 <= b < k):
                raise ValueError(f"interacción fuera de rango: {((p, a), (q, b))}")
            self.interacciones.append(((p, a), (q, b), frozenset(conjunto)))

        nombres = list(ranuras) if ranuras else [f"r{p}" for p in range(m)]
        if len(nombres) != m:
            raise ValueError("ranuras debe tener m nombres")
        instancias = [{"id": i} for i in range(n)]
        super().__init__(nombres, {r: range(k) for r in nombres}, instancias, temperaturas)

    # ---- veredicto exacto ----------------------------------------------

    def _indices(self, config):
        return tuple(config[r] for r in self.ranuras)

    def _interacciones_activas(self, idx):
        return [conj for (p, a), (q, b), conj in self.interacciones if idx[p] == a and idx[q] == b]

    def _estado(self, idx):
        """Lo que depende solo de la configuración: familias rotas o instancias anuladas."""
        activas = self._interacciones_activas(idx)
        if self.modelo == "conjuntivo":
            rotas = set()
            for p, a in enumerate(idx):
                rotas |= self.rompe[(p, a)]
            for conj in activas:
                rotas |= conj
            return rotas
        anuladas = set()
        for conj in activas:
            anuladas |= conj
        return anuladas

    def _veredicto(self, idx, i, estado):
        """(1, None) si la instancia i pasa; (0, restricción violada) si no. Sin ruido."""
        if self.modelo == "conjuntivo":
            for f in self.familias_instancia[i]:
                if f in estado:
                    return 0, f
            return 1, None
        if not any(idx[p] == a for p, a in self.literales[i]):
            return 0, "clausula:insatisfecha"
        if i in estado:
            return 0, "interaccion:rota"
        return 1, None

    def _volteo(self, idx, temperatura, i, semilla):
        if self.ruido == 0.0:
            return False
        if self.ruido == 1.0:
            return True
        rng = random.Random(f"{self.semilla_ruido}|{idx}|{temperatura}|{i}|{semilla}")
        return rng.random() < self.ruido

    def _evaluar(self, config, instancias, semilla):
        idx = self._indices(config)
        temperatura = float(config.get("temperatura", 0.0))
        estado = self._estado(idx)
        aciertos, trazas, nuevas = 0, [], 0
        for x in instancias:
            i = x["id"]
            clave = (idx, temperatura, i, semilla)
            if not self.usa_cache or clave not in self._vistas:
                nuevas += 1
                self._vistas.add(clave)
            ok, violo = self._veredicto(idx, i, estado)
            if self._volteo(idx, temperatura, i, semilla):
                ok, violo = (0, "ruido:volteo") if ok else (1, None)
            if ok:
                aciertos += 1
            else:
                trazas.append({"id": i, "violo": violo, "salida": None})
        return aciertos, trazas, nuevas

    # ---- verdad conocida (no cuenta consultas) --------------------------

    def precision_exacta(self, config, instancias=None):
        """Acc(c) sin ruido y sin cobrar consultas: la verdad del oráculo."""
        self.validar_config(config)
        instancias = self.instancias if instancias is None else instancias
        idx = self._indices(config)
        estado = self._estado(idx)
        return sum(self._veredicto(idx, x["id"], estado)[0] for x in instancias) / len(instancias)

    def optimo_exacto(self):
        """(Acc*, lista de configuraciones óptimas) por fuerza bruta sobre C, sin cobrar consultas."""
        tamano = self.tamano_espacio()
        if tamano > LIMITE_FUERZA_BRUTA:
            raise ValueError(f"|C| = {tamano} supera el límite de fuerza bruta ({LIMITE_FUERZA_BRUTA})")
        mejor, optimas = -1, []
        t0 = self.temperaturas[0]
        for idx in itertools.product(range(self.k), repeat=self.m):
            estado = self._estado(idx)
            aciertos = sum(self._veredicto(idx, i, estado)[0] for i in range(self.n))
            if aciertos > mejor:
                mejor, optimas = aciertos, [idx]
            elif aciertos == mejor:
                optimas.append(idx)
        return mejor / self.n, [self.config(idx, temperatura=t0) for idx in optimas]

    def descripcion(self):
        """Parámetros del oráculo, para guardarlos junto a cada resultado."""
        return {"modelo": self.modelo, "m": self.m, "k": self.k, "n": self.n,
                "interacciones": len(self.interacciones), "ruido": self.ruido,
                "semilla_ruido": self.semilla_ruido, **self.parametros}


# ---------------------------------------------------------------- generadores

def _interacciones_aleatorias(rng, m, k, cantidad, universo, tamano):
    if cantidad and m < 2:
        raise ValueError("las interacciones necesitan al menos 2 ranuras")
    universo = list(universo)
    tamano = min(tamano, len(universo))
    salida = []
    for _ in range(cantidad):
        p, q = sorted(rng.sample(range(m), 2))
        salida.append(((p, rng.randrange(k)), (q, rng.randrange(k)), frozenset(rng.sample(universo, tamano))))
    return salida


def generar_conjuntivo(m, k, n, semilla, *, familias=10, limpias_por_ranura=1, prob_rompe=0.2,
                       familias_por_instancia=(2, 3), interacciones=0, familias_por_interaccion=1,
                       ruido=0.0, cache=True, ranuras=None, temperaturas=(0.0,)):
    """Oráculo conjuntivo aleatorio.

    Cada ranura tiene ``limpias_por_ranura`` opciones que no rompen nada; cada
    opción no limpia rompe cada familia con probabilidad ``prob_rompe`` (al
    menos una). Cada instancia trae entre 2 y 3 familias distintas. Las
    interacciones se generan al final, así que con la misma semilla la estructura
    base es la misma con o sin interacciones.
    """
    if not 0 <= limpias_por_ranura <= k:
        raise ValueError("limpias_por_ranura debe estar entre 0 y k")
    if max(familias_por_instancia) > familias:
        raise ValueError("una instancia no puede traer más familias de las que existen")
    rng = random.Random(semilla)
    nombres = [f"f{j}" for j in range(familias)]
    rompe = {}
    for p in range(m):
        limpias = set(rng.sample(range(k), limpias_por_ranura))
        for a in range(k):
            if a in limpias:
                rompe[(p, a)] = frozenset()
            else:
                rotas = {f for f in nombres if rng.random() < prob_rompe} or {rng.choice(nombres)}
                rompe[(p, a)] = frozenset(rotas)
    familias_instancia = [tuple(rng.sample(nombres, rng.choice(familias_por_instancia))) for _ in range(n)]
    inter = _interacciones_aleatorias(rng, m, k, interacciones, nombres, familias_por_interaccion)
    parametros = {"generador": "generar_conjuntivo", "semilla": semilla, "familias": familias,
                  "limpias_por_ranura": limpias_por_ranura, "prob_rompe": prob_rompe,
                  "familias_por_instancia": list(familias_por_instancia),
                  "familias_por_interaccion": familias_por_interaccion}
    return OraculoSintetico("conjuntivo", m, k, rompe=rompe, familias_instancia=familias_instancia,
                            interacciones=inter, ruido=ruido, semilla_ruido=semilla, cache=cache,
                            ranuras=ranuras, temperaturas=temperaturas, parametros=parametros)


def generar_disyuntivo(m, k, n, semilla, *, literales_por_instancia=3, interacciones=0,
                       instancias_por_interaccion=None, ruido=0.0, cache=True, ranuras=None,
                       temperaturas=(0.0,)):
    """Oráculo disyuntivo aleatorio: cada instancia trae pares (p, a) sobre ranuras distintas."""
    if not 1 <= literales_por_instancia <= m:
        raise ValueError("literales_por_instancia debe estar entre 1 y m")
    rng = random.Random(semilla)
    literales = [tuple((p, rng.randrange(k)) for p in sorted(rng.sample(range(m), literales_por_instancia)))
                 for _ in range(n)]
    tamano = instancias_por_interaccion or max(1, n // 10)
    inter = _interacciones_aleatorias(rng, m, k, interacciones, range(n), tamano)
    parametros = {"generador": "generar_disyuntivo", "semilla": semilla,
                  "literales_por_instancia": literales_por_instancia, "instancias_por_interaccion": tamano}
    return OraculoSintetico("disyuntivo", m, k, literales=literales, interacciones=inter, ruido=ruido,
                            semilla_ruido=semilla, cache=cache, ranuras=ranuras, temperaturas=temperaturas,
                            parametros=parametros)


def desde_3sat(clausulas, num_variables, *, interacciones=(), ruido=0.0, semilla_ruido=0, cache=True):
    """Construye el caso de CONFIG-EXACTA de la reducción desde 3-SAT.

    ``clausulas`` usa la notación DIMACS: el literal ``v`` es x_v y ``-v`` es ¬x_v,
    con variables numeradas desde 1. Una ranura por variable (opciones 0 = falso,
    1 = verdadero), una instancia por cláusula, y L_j contiene (v-1, 1) por cada
    literal x_v y (v-1, 0) por cada ¬x_v.
    """
    literales = []
    for c in clausulas:
        if not c or any(l == 0 or abs(l) > num_variables for l in c):
            raise ValueError(f"cláusula inválida: {c}")
        literales.append(tuple((abs(l) - 1, 1 if l > 0 else 0) for l in c))
    parametros = {"generador": "desde_3sat", "num_variables": num_variables, "clausulas": len(clausulas)}
    oraculo = OraculoSintetico("disyuntivo", num_variables, 2, literales=literales, interacciones=interacciones,
                               ruido=ruido, semilla_ruido=semilla_ruido, cache=cache, parametros=parametros)
    oraculo.clausulas = [list(c) for c in clausulas]
    return oraculo


def generar_3sat(num_variables, razon, semilla, *, ruido=0.0, cache=True):
    """Fórmula 3-SAT aleatoria con round(razon · num_variables) cláusulas sobre variables distintas."""
    if num_variables < 3:
        raise ValueError("3-SAT necesita al menos 3 variables")
    rng = random.Random(semilla)
    num_clausulas = max(1, math.floor(razon * num_variables + 0.5))
    clausulas = [[v if rng.random() < 0.5 else -v for v in sorted(rng.sample(range(1, num_variables + 1), 3))]
                 for _ in range(num_clausulas)]
    oraculo = desde_3sat(clausulas, num_variables, ruido=ruido, semilla_ruido=semilla, cache=cache)
    oraculo.parametros.update({"generador": "generar_3sat", "semilla": semilla, "razon": razon})
    return oraculo
