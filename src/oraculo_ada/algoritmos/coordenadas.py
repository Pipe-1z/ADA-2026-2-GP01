"""Algoritmo 3: ascenso por coordenadas guiado por trazas, y sus variantes (Fase 2b).

**Comportamiento original** (los valores por defecto). Extraído sin cambios de
las secciones 5 a 8 del notebook de búsqueda (celdas 12, 14, 16 y 18):

1. Se evalúa la configuración inicial (por defecto, la primera opción de cada
   ranura y la primera temperatura).
2. El orden de las ranuras sale de las trazas: cada ranura suma los fallos de la
   configuración inicial en las familias que la hipótesis le asocia, y se
   recorren de mayor a menor (``sorted`` estable). Sin hipótesis, se usa el
   orden de ``oraculo.ranuras``.
3. Para cada ranura, con las demás fijas, se prueban sus opciones en orden
   creciente, salvo la actual y las descartadas. Se conserva la de mayor
   precisión; en empate se mantiene la actual (comparación estricta ``>``).
4. Poda por trazas: una opción queda descartada para siempre si, frente a la
   configuración al inicio del barrido de esa ranura, suma ``umbral_traza`` o más
   fallos en alguna familia y no mejora la precisión (``p <= base``).
5. Una pasada recorre todas las ranuras; se repite mientras alguna mejore, hasta
   ``max_pasadas``.
6. Con las ranuras fijas se prueban las demás temperaturas, en orden; se cambia
   si la precisión mejora estrictamente.

**Variantes** (parámetros; ninguna usa información interna del oráculo, solo
precisiones y trazas):

- ``poda``: ``"permanente"`` (original), ``"por_pasada"`` (las descartadas se
  olvidan al empezar cada pasada) o ``"ninguna"``.
- ``umbral_traza``: fallos adicionales en una familia para descartar (original: 3).
- ``criterio_poda``: ``"familias"`` (original: aumento del conteo de fallos de la
  familia, aunque se deba a instancias que ya fallaban y solo cambiaron de
  primera restricción violada) o ``"instancias"`` (solo cuentan las instancias
  que pasaban en la base y fallan con la opción: el cambio de familia de una
  instancia que ya fallaba no es un empeoramiento).
- ``desempate``: ``"actual"`` (original) o ``"trazas"``. Con ``"trazas"``, si
  ninguna opción mejora estrictamente la precisión, entre las opciones que
  **empatan** con la actual se prefiere la que tiene menos fallos en las familias
  de la ranura, si tiene estrictamente menos que la actual. Las familias de la
  ranura son las de la hipótesis si se da ``hipotesis``; si no, las que aparecen
  en las trazas de la configuración actual y desaparecen por completo con alguna
  opción de esa ranura. Desempates siguientes: menos familias distintas en las
  trazas y, por último, el índice menor. Un cambio por desempate cuenta como
  mejora de la pasada.
- ``movimientos_dobles``: dict con ``pares_muestra``, ``n_preliminar``, ``top``,
  ``rondas`` y ``semilla``. Cuando un bloque de pasadas termina, se sortean
  ``pares_muestra`` cambios simultáneos de dos ranuras, se evalúan primero sobre
  una submuestra de ``n_preliminar`` instancias (evaluación barata) y solo los
  ``top`` mejores que no quedan por debajo de la actual en esa submuestra se
  evalúan completos. Si alguno mejora, se adopta y se corre otro bloque de
  pasadas. A lo sumo ``rondas`` rondas.

Costo del original (operación básica: una consulta), con n instancias, k_p
opciones en la ranura p, I pasadas y |T| temperaturas:

    T ≤ n · [1 + I · Σ_p (k_p − 1) + (|T| − 1)] = O(I · m · k · n)

Las consultas cobradas pueden ser menos: la poda evita evaluaciones y el caché
no vuelve a cobrar una configuración ya evaluada.
"""

import json
import random
from collections import Counter
from dataclasses import dataclass, field

from ..oraculos.base import PresupuestoAgotado, familia, mejor_evaluacion_completa

# Hipótesis ranura → familias de la primera entrega (celda 14 del notebook de búsqueda).
HIPOTESIS_PRIMERA_ENTREGA = {
    "rol": ["first_word", "copy", "new"],
    "estrategia": ["length_constraints"],
    "formato": ["detectable_format", "paragraphs", "combination"],
    "estilo": ["change_case", "letters", "punctuation", "keywords", "language"],
    "cierre": ["last_word", "startend", "detectable_content"],
}
PODAS = ("permanente", "por_pasada", "ninguna")
CRITERIOS_PODA = ("familias", "instancias")
DESEMPATES = ("actual", "trazas")


def cota_consultas_coordenadas(opciones_por_ranura, n, max_pasadas, num_temperaturas=1):
    """n · [1 + I · Σ (k_p − 1) + (|T| − 1)]."""
    return n * (1 + max_pasadas * sum(k - 1 for k in opciones_por_ranura) + (num_temperaturas - 1))


@dataclass
class ResultadoCoordenadas:
    mejor_config: dict
    mejor_precision: float
    pasadas: int
    convergio: bool
    orden: list
    decisiones: list = field(default_factory=list)
    movimientos: list = field(default_factory=list)   # [{fase, ranura, de, a, precision_antes, precision_despues, motivo}]
    descartadas: dict = field(default_factory=dict)
    registro: list = field(default_factory=list)
    consultas_cobradas: int = 0
    consultas_solicitadas: int = 0
    segundos: float = 0.0
    presupuesto: int = None
    presupuesto_agotado: bool = False

    @property
    def evaluaciones(self):
        return len(self.registro)

    def configuraciones_distintas(self):
        return len({tuple(f["config"].items()) for f in self.registro})


@dataclass
class _Evaluada:
    precision: float
    fallos: Counter
    fallidas: dict            # id de instancia → restricción violada


def _fallos(trazas):
    # Igual que el notebook: se cuentan solo las trazas con `violo`.
    return Counter(familia(t["violo"]) for t in trazas if t.get("violo"))


def ascenso_coordenadas(oraculo, inicial=None, *, instancias=None, semilla=1, max_pasadas=3,
                        umbral_traza=3, hipotesis=None, orden=None, probar_temperaturas=True,
                        al_evaluar=None, poda="permanente", criterio_poda="familias", desempate="actual",
                        movimientos_dobles=None, presupuesto=None, modo_presupuesto="nuevas"):
    """Ejecuta el Algoritmo 3 (o una variante) y devuelve un ``ResultadoCoordenadas``.

    ``al_evaluar(fila)``, si se da, se llama después de cada evaluación.

    ``presupuesto`` (B): antes de cada evaluación se comprueba que su costo no supere lo que
    queda de B (``modo_presupuesto``: ``"nuevas"`` o ``"propias"``, ver
    ``OraculoBase.presupuesto``). Si no alcanza, el algoritmo se detiene sin hacer esa
    evaluación y devuelve la mejor configuración evaluada sobre todas las instancias hasta ese
    momento (``None`` si B no alcanzó ni para la primera), con ``presupuesto_agotado = True``.
    """
    if poda not in PODAS or criterio_poda not in CRITERIOS_PODA or desempate not in DESEMPATES:
        raise ValueError("variante desconocida")
    instancias = oraculo.instancias if instancias is None else list(instancias)
    consultas_antes, solicitadas_antes, segundos_antes = (
        oraculo.consultas, oraculo.consultas_solicitadas, oraculo.segundos)
    registro = []

    def evaluar_registrar(c, fase, ranura="-", nota="", sobre=None, base=None):
        r = oraculo.evaluar(c, instancias if sobre is None else sobre, semilla=semilla)
        fallos = _fallos(r.trazas)
        fila = {
            "paso": len(registro) + 1, "fase": fase, "ranura_probada": ranura,
            "config": dict(c), "precision": round(r.precision, 4), "consultas": r.n,
            "consultas_nuevas": r.consultas_nuevas, "segundos": r.segundos,
            "fallos_por_familia": json.dumps(dict(fallos.most_common())), "nota": nota,
            "precision_base": None if base is None else base[0], "opcion_base": None if base is None else base[1],
        }
        registro.append(fila)
        if al_evaluar:
            al_evaluar(fila)
        return _Evaluada(r.precision, fallos, {t["id"]: t["violo"] for t in r.trazas})

    if inicial is None:
        inicial = oraculo.config([oraculo.opciones[r][0] for r in oraculo.ranuras],
                                 temperatura=oraculo.temperaturas[0])
    actual = dict(inicial)
    ev_actual = None
    estado = {"pasada": 0}
    inicio_historial = len(oraculo.historial)

    descartadas = {r: {} for r in oraculo.ranuras}
    historial_descartes = {r: {} for r in oraculo.ranuras}
    decisiones, movimientos = [], []

    def mover(fase, ranura, nueva, ev, motivo):
        nonlocal actual, ev_actual
        de = "+".join(str(actual[r]) for r in ranura.split("+"))
        a = "+".join(str(nueva[r]) for r in ranura.split("+"))
        decisiones.append(f"{fase.capitalize()}: {ranura} {de} → {a} ({ev_actual.precision:.1%} → {ev.precision:.1%})"
                          + ("" if motivo == "mejora" else f" [{motivo}]"))
        movimientos.append({"fase": fase, "ranura": ranura, "de": actual[ranura] if "+" not in ranura else de,
                            "a": nueva[ranura] if "+" not in ranura else a,
                            "precision_antes": ev_actual.precision, "precision_despues": ev.precision,
                            "motivo": motivo})
        actual, ev_actual = dict(nueva), ev

    def familias_de_la_ranura(ranura, evaluadas):
        if hipotesis:
            return set(hipotesis.get(ranura, []))
        presentes = {f for f, c in ev_actual.fallos.items() if c > 0}
        return {f for f in presentes if any(ev.fallos.get(f, 0) == 0 for ev in evaluadas.values())}

    def barrido(pasada, ranura):
        base = ev_actual
        base_opcion = actual[ranura]
        mejor_op, mejor_ev = actual[ranura], ev_actual
        evaluadas = {}
        for op in oraculo.opciones[ranura]:
            if op == actual[ranura] or (poda != "ninguna" and op in descartadas[ranura]):
                continue
            cand = dict(actual, **{ranura: op})
            ev = evaluar_registrar(cand, f"pasada {pasada}", ranura, base=(base.precision, base_opcion))
            evaluadas[op] = ev
            if criterio_poda == "familias":
                delta = {f: ev.fallos[f] - base.fallos.get(f, 0) for f in ev.fallos}
            else:
                delta = Counter(familia(v) for i, v in ev.fallidas.items() if i not in base.fallidas)
            empeora = {f: d for f, d in delta.items() if d >= umbral_traza}
            if poda != "ninguna" and empeora and ev.precision <= base.precision:
                motivo = ", ".join(f"{f} +{d}" for f, d in sorted(empeora.items(), key=lambda x: -x[1]))
                descartadas[ranura][op] = motivo
                historial_descartes[ranura].setdefault(op, motivo)
                registro[-1]["nota"] = f"descartada por trazas: {motivo}"
            if ev.precision > mejor_ev.precision:
                mejor_op, mejor_ev = op, ev
        motivo = "mejora"
        if desempate == "trazas" and mejor_op == actual[ranura] and evaluadas:
            fams = familias_de_la_ranura(ranura, evaluadas)
            medida = lambda ev: (sum(ev.fallos.get(f, 0) for f in fams), len(ev.fallos))
            empatadas = [op for op, ev in evaluadas.items()
                         if ev.precision == ev_actual.precision and medida(ev) < medida(ev_actual)]
            if empatadas:
                mejor_op = min(empatadas, key=lambda op: (medida(evaluadas[op]), op))
                mejor_ev = evaluadas[mejor_op]
                descartadas[ranura].pop(mejor_op, None)
                motivo = "desempate por trazas"
        if mejor_op != actual[ranura]:
            mover(f"pasada {pasada}", ranura, dict(actual, **{ranura: mejor_op}), mejor_ev, motivo)
            return True
        return False

    def bloque_de_pasadas(primera):
        """Corre hasta ``max_pasadas`` pasadas; devuelve (última pasada, convergió)."""
        pasada = primera - 1
        for pasada in range(primera, primera + max_pasadas):
            estado["pasada"] = pasada
            if poda == "por_pasada":
                for r in descartadas:
                    descartadas[r].clear()
            mejoro = False
            for ranura in orden:
                mejoro |= barrido(pasada, ranura)
            if not mejoro:
                return pasada, True
        return pasada, False

    def ronda_doble(numero):
        md = movimientos_dobles
        rng = random.Random(f"{md['semilla']}|{numero}")
        candidatos = [(p, q, a, b) for i, p in enumerate(oraculo.ranuras) for q in oraculo.ranuras[i + 1:]
                      for a in oraculo.opciones[p] if a != actual[p]
                      for b in oraculo.opciones[q] if b != actual[q]]
        muestra = rng.sample(candidatos, min(md["pares_muestra"], len(candidatos)))
        sub = rng.sample(instancias, min(md["n_preliminar"], len(instancias)))
        p_sub_actual = sum(1 for x in sub if x["id"] not in ev_actual.fallidas) / len(sub)
        preliminar = []
        for j, (p, q, a, b) in enumerate(muestra):
            cand = dict(actual, **{p: a, q: b})
            ev = evaluar_registrar(cand, f"dobles {numero} (preliminar)", f"{p}+{q}", sobre=sub)
            preliminar.append((ev.precision, j, (p, q), cand))
        elegibles = sorted((x for x in preliminar if x[0] >= p_sub_actual), key=lambda x: (-x[0], x[1]))[:md["top"]]
        mejor = None
        for _, _, (p, q), cand in elegibles:
            ev = evaluar_registrar(cand, f"dobles {numero}", f"{p}+{q}")
            if ev.precision > ev_actual.precision and (mejor is None or ev.precision > mejor[1].precision):
                mejor = (f"{p}+{q}", ev, cand)
        if mejor:
            mover(f"dobles {numero}", mejor[0], mejor[2], mejor[1], "movimiento doble")
            return True
        return False

    pasadas, convergio, agotado = 0, False, False
    with oraculo.presupuesto(presupuesto, modo_presupuesto) as tope:
        try:
            ev_actual = evaluar_registrar(actual, "inicial", nota="configuración inicial")
            if orden is None:
                if hipotesis:
                    hip = {r: hipotesis.get(r, []) for r in oraculo.ranuras}
                    peso = {r: sum(ev_actual.fallos.get(f, 0) for f in hip[r]) for r in oraculo.ranuras}
                    orden = sorted(oraculo.ranuras, key=lambda r: -peso[r])
                else:
                    orden = list(oraculo.ranuras)

            pasadas, convergio = bloque_de_pasadas(1)
            rondas = movimientos_dobles["rondas"] if movimientos_dobles else 0
            for numero in range(1, rondas + 1):
                if not ronda_doble(numero):
                    break
                pasadas, convergio = bloque_de_pasadas(pasadas + 1)

            if probar_temperaturas:
                for temp in oraculo.temperaturas:
                    if temp == actual.get("temperatura", 0.0):
                        continue
                    cand = dict(actual, temperatura=temp)
                    ev = evaluar_registrar(cand, "temperatura", "temperatura")
                    if ev.precision > ev_actual.precision:
                        decisiones.append(f"Temperatura {actual.get('temperatura', 0.0)} → {temp} "
                                          f"({ev_actual.precision:.1%} → {ev.precision:.1%})")
                        movimientos.append({"fase": "temperatura", "ranura": "temperatura",
                                            "de": actual.get("temperatura", 0.0), "a": temp,
                                            "precision_antes": ev_actual.precision, "precision_despues": ev.precision,
                                            "motivo": "mejora"})
                        actual, ev_actual = cand, ev
        except PresupuestoAgotado as e:
            if tope is None or e.tope_id != tope:
                raise
            agotado, pasadas, convergio = True, estado["pasada"], False

    if agotado:
        # Mejor configuración encontrada: la mejor evaluación completa hecha antes de agotar B.
        mejor_config, mejor_precision = mejor_evaluacion_completa(oraculo, inicio_historial, len(instancias))
    else:
        mejor_config, mejor_precision = actual, ev_actual.precision
    return ResultadoCoordenadas(
        mejor_config=mejor_config, mejor_precision=mejor_precision, pasadas=pasadas, convergio=convergio,
        orden=list(orden or oraculo.ranuras), decisiones=decisiones, movimientos=movimientos,
        descartadas=historial_descartes if poda == "por_pasada" else descartadas, registro=registro,
        consultas_cobradas=oraculo.consultas - consultas_antes,
        consultas_solicitadas=oraculo.consultas_solicitadas - solicitadas_antes,
        segundos=oraculo.segundos - segundos_antes,
        presupuesto=presupuesto, presupuesto_agotado=agotado,
    )


@dataclass
class ResultadoReinicios:
    mejor: ResultadoCoordenadas            # mejor corrida terminada (None si ninguna terminó)
    corridas: list
    inicios: list
    consultas_cobradas: int
    consultas_solicitadas: int
    mejor_config: dict = None              # mejor configuración encontrada en todas las corridas
    mejor_precision: float = None
    presupuesto: int = None
    presupuesto_agotado: bool = False


def reinicios(oraculo, num_inicios, semilla_inicios, *, incluir_inicial=True, presupuesto=None,
              modo_presupuesto="nuevas", **opciones):
    """Reinicios múltiples: ``num_inicios`` corridas del Algoritmo 3 (o una variante).

    La primera parte de la configuración inicial por defecto (si ``incluir_inicial``)
    y las demás de configuraciones al azar sorteadas con ``random.Random(semilla_inicios)``.
    El caché del oráculo es compartido: una configuración que dos corridas evalúan
    se cobra una sola vez. Gana la corrida con mayor precisión (en empate, la primera).

    ``presupuesto`` (B) vale para todas las corridas juntas: si una evaluación lo superaría,
    se detiene y devuelve la mejor configuración evaluada sobre todas las instancias.
    """
    rng = random.Random(semilla_inicios)
    t0 = oraculo.temperaturas[0]
    inicios = [oraculo.config([oraculo.opciones[r][0] for r in oraculo.ranuras], temperatura=t0)] \
        if incluir_inicial else []
    while len(inicios) < num_inicios:
        inicios.append(oraculo.config([rng.choice(oraculo.opciones[r]) for r in oraculo.ranuras], temperatura=t0))
    consultas_antes, solicitadas_antes = oraculo.consultas, oraculo.consultas_solicitadas
    inicio_historial = len(oraculo.historial)
    n = len(opciones.get("instancias") or oraculo.instancias)
    corridas, agotado = [], False
    with oraculo.presupuesto(presupuesto, modo_presupuesto) as tope:
        try:
            for x in inicios:
                corridas.append(ascenso_coordenadas(oraculo, x, **opciones))
        except PresupuestoAgotado as e:
            if tope is None or e.tope_id != tope:
                raise
            agotado = True
    mejor = max(corridas, key=lambda r: r.mejor_precision) if corridas else None
    if agotado:
        config, precision = mejor_evaluacion_completa(oraculo, inicio_historial, n)
    else:
        config, precision = mejor.mejor_config, mejor.mejor_precision
    return ResultadoReinicios(mejor=mejor, corridas=corridas, inicios=inicios,
                              consultas_cobradas=oraculo.consultas - consultas_antes,
                              consultas_solicitadas=oraculo.consultas_solicitadas - solicitadas_antes,
                              mejor_config=config, mejor_precision=precision,
                              presupuesto=presupuesto, presupuesto_agotado=agotado)
