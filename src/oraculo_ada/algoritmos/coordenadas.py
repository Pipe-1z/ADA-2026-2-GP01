"""Algoritmo 3: ascenso por coordenadas guiado por trazas.

Extraído **sin cambiar el comportamiento** de las secciones 5 a 8 del notebook de
búsqueda (``notebooks/notebook_busqueda.ipynb``, celdas 12, 14, 16 y 18):

1. Se evalúa la configuración inicial (por defecto, la primera opción de cada
   ranura y la primera temperatura).
2. El orden de las ranuras sale de las trazas: cada ranura suma los fallos de la
   configuración inicial en las familias que la hipótesis le asocia, y se
   recorren de mayor a menor (``sorted`` estable: en empate, el orden original).
   Sin hipótesis, se usa el orden de ``oraculo.ranuras``.
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

Costo (operación básica: una consulta), con n instancias, k_p opciones en la
ranura p, I pasadas y |T| temperaturas:

    T ≤ n · [1 + I · Σ_p (k_p − 1) + (|T| − 1)] = O(I · m · k · n)

Las consultas cobradas pueden ser menos: la poda evita evaluaciones y el caché
no vuelve a cobrar una configuración ya evaluada.
"""

import json
from collections import Counter
from dataclasses import dataclass, field

from ..oraculos.base import familia

# Hipótesis ranura → familias de la primera entrega (celda 14 del notebook de búsqueda).
HIPOTESIS_PRIMERA_ENTREGA = {
    "rol": ["first_word", "copy", "new"],
    "estrategia": ["length_constraints"],
    "formato": ["detectable_format", "paragraphs", "combination"],
    "estilo": ["change_case", "letters", "punctuation", "keywords", "language"],
    "cierre": ["last_word", "startend", "detectable_content"],
}


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
    movimientos: list = field(default_factory=list)   # [{fase, ranura, de, a, precision_antes, precision_despues}]
    descartadas: dict = field(default_factory=dict)
    registro: list = field(default_factory=list)
    consultas_cobradas: int = 0
    consultas_solicitadas: int = 0
    segundos: float = 0.0

    @property
    def evaluaciones(self):
        return len(self.registro)

    def configuraciones_distintas(self):
        return len({tuple(f["config"].items()) for f in self.registro})


def _fallos(resultado):
    # Igual que el notebook: se cuentan solo las trazas con `violo`.
    return Counter(familia(t["violo"]) for t in resultado.trazas if t.get("violo"))


def ascenso_coordenadas(oraculo, inicial=None, *, instancias=None, semilla=1, max_pasadas=3,
                        umbral_traza=3, hipotesis=None, orden=None, probar_temperaturas=True,
                        al_evaluar=None):
    """Ejecuta el Algoritmo 3 y devuelve un ``ResultadoCoordenadas``.

    ``al_evaluar(fila)``, si se da, se llama después de cada evaluación (sirve
    para guardar el progreso).
    """
    instancias = oraculo.instancias if instancias is None else list(instancias)
    consultas_antes, solicitadas_antes, segundos_antes = (
        oraculo.consultas, oraculo.consultas_solicitadas, oraculo.segundos)
    registro = []

    def evaluar_registrar(c, fase, ranura="-", nota=""):
        r = oraculo.evaluar(c, instancias, semilla=semilla)
        fallos = _fallos(r)
        fila = {
            "paso": len(registro) + 1, "fase": fase, "ranura_probada": ranura,
            "config": dict(c), "precision": round(r.precision, 4), "consultas": r.n,
            "consultas_nuevas": r.consultas_nuevas, "segundos": r.segundos,
            "fallos_por_familia": json.dumps(dict(fallos.most_common())), "nota": nota,
        }
        registro.append(fila)
        if al_evaluar:
            al_evaluar(fila)
        return r.precision, fallos

    if inicial is None:
        inicial = oraculo.config([oraculo.opciones[r][0] for r in oraculo.ranuras],
                                 temperatura=oraculo.temperaturas[0])
    actual = dict(inicial)
    p_actual, fallos_actual = evaluar_registrar(actual, "inicial", nota="configuración inicial")

    if orden is None:
        if hipotesis:
            hip = {r: hipotesis.get(r, []) for r in oraculo.ranuras}
            peso = {r: sum(fallos_actual.get(f, 0) for f in hip[r]) for r in oraculo.ranuras}
            orden = sorted(oraculo.ranuras, key=lambda r: -peso[r])
        else:
            orden = list(oraculo.ranuras)

    descartadas = {r: {} for r in oraculo.ranuras}
    decisiones, movimientos = [], []
    pasadas, convergio = 0, False
    for pasada in range(1, max_pasadas + 1):
        pasadas = pasada
        mejoro_pasada = False
        for ranura in orden:
            base_p, base_fallos = p_actual, fallos_actual
            mejor_op, mejor_p, mejor_fallos = actual[ranura], p_actual, fallos_actual
            for op in oraculo.opciones[ranura]:
                if op == actual[ranura] or op in descartadas[ranura]:
                    continue
                cand = dict(actual, **{ranura: op})
                p, fallos = evaluar_registrar(cand, f"pasada {pasada}", ranura)
                empeora = {f: fallos[f] - base_fallos.get(f, 0) for f in fallos
                           if fallos[f] - base_fallos.get(f, 0) >= umbral_traza}
                if empeora and p <= base_p:
                    motivo = ", ".join(f"{f} +{d}" for f, d in sorted(empeora.items(), key=lambda x: -x[1]))
                    descartadas[ranura][op] = motivo
                    registro[-1]["nota"] = f"descartada por trazas: {motivo}"
                if p > mejor_p:
                    mejor_op, mejor_p, mejor_fallos = op, p, fallos
            if mejor_op != actual[ranura]:
                decisiones.append(f"Pasada {pasada}: {ranura} {actual[ranura]} → {mejor_op} "
                                  f"({p_actual:.1%} → {mejor_p:.1%})")
                movimientos.append({"fase": f"pasada {pasada}", "ranura": ranura, "de": actual[ranura],
                                    "a": mejor_op, "precision_antes": p_actual, "precision_despues": mejor_p})
                actual = dict(actual, **{ranura: mejor_op})
                p_actual, fallos_actual = mejor_p, mejor_fallos
                mejoro_pasada = True
        if not mejoro_pasada:
            convergio = True
            break

    if probar_temperaturas:
        for temp in oraculo.temperaturas:
            if temp == actual.get("temperatura", 0.0):
                continue
            cand = dict(actual, temperatura=temp)
            p, fallos = evaluar_registrar(cand, "temperatura", "temperatura")
            if p > p_actual:
                decisiones.append(f"Temperatura {actual.get('temperatura', 0.0)} → {temp} "
                                  f"({p_actual:.1%} → {p:.1%})")
                movimientos.append({"fase": "temperatura", "ranura": "temperatura",
                                    "de": actual.get("temperatura", 0.0), "a": temp,
                                    "precision_antes": p_actual, "precision_despues": p})
                actual, p_actual, fallos_actual = cand, p, fallos

    return ResultadoCoordenadas(
        mejor_config=actual, mejor_precision=p_actual, pasadas=pasadas, convergio=convergio,
        orden=list(orden), decisiones=decisiones, movimientos=movimientos, descartadas=descartadas,
        registro=registro,
        consultas_cobradas=oraculo.consultas - consultas_antes,
        consultas_solicitadas=oraculo.consultas_solicitadas - solicitadas_antes,
        segundos=oraculo.segundos - segundos_antes,
    )
