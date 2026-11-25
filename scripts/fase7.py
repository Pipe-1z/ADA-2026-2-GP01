"""Fase 7: experimentos con el modelo real en Colab T4, por pasos que se pueden retomar.

Uso (desde notebooks/lanzador_fase7.ipynb, con ORACULO_DIR_CACHE y ORACULO_DIR_RESULTADOS
apuntando a Google Drive):

    python scripts/fase7.py plan                       # (local) escribe resultados/fase7_plan.json
    python scripts/fase7.py preparar --cache-original RUTA   # sin GPU
    python scripts/fase7.py tiempo      [--confirmar]  # (a) costo por consulta y tiempo contra n
    python scripts/fase7.py pendiente   [--confirmar]  # (b) evaluación pendiente (0,0,0,6,1)
    python scripts/fase7.py estrategia  [--confirmar]  # (c) dos ranuras + SH, n0 = 2, 2 rondas
    python scripts/fase7.py subespacio  [--confirmar]  # (d) subespacio con óptimo exacto
    python scripts/fase7.py entrega     [--confirmar] [--semana N]   # regla de entrega.json
    python scripts/fase7.py estado                     # qué pasos están hechos

Sin ``--confirmar`` cada paso solo muestra cuántas consultas y cuánto tiempo gastaría. Con
``--confirmar`` corre con un **tope de consultas nuevas** (CLAUDE.md, regla 6): si una evaluación
lo superaría, se detiene antes de consultar al modelo. Lo ya evaluado está en el caché de Drive y
no se vuelve a cobrar, así que si la sesión se cae basta con volver a ejecutar el mismo paso; el
tope cuenta las consultas acumuladas entre sesiones (libro de consultas).

Caché: ``<ORACULO_DIR_CACHE>/cache_oraculo.json`` es el caché de la T4 **recalificado con
open-instruct a4cd966** (lo crea ``preparar`` a partir del caché original de Drive, que no se
modifica), de modo que las respuestas viejas y las nuevas tienen veredictos de la misma versión.
"""

import argparse
import json
import math
import random
import statistics
import sys
import time
from pathlib import Path

from oraculo_ada import rutas
from oraculo_ada.algoritmos import (
    ascenso_coordenadas,
    costo_sh,
    dos_ranuras_sh,
    fuerza_bruta,
    muestra_configuraciones,
    successive_halving,
)
from oraculo_ada.algoritmos.coordenadas import HIPOTESIS_PRIMERA_ENTREGA
from oraculo_ada.algoritmos.reparto import reparto_ucb1, reparto_uniforme
from oraculo_ada.analisis.ajuste import ajustar_combinacion, pendiente_loglog
from oraculo_ada.hardware import verificar_hardware
from oraculo_ada.oraculos.base import OraculoBase
from oraculo_ada.registro import cargar_resultado, guardar_resultado

PLAN = {
    "descripcion": "Plan de la Fase 7 (experimentos con el modelo real en Colab T4), escrito antes de correr",
    "hardware": "Google Colab, NVIDIA T4 (regla 14); se verifica el nombre de la GPU antes de cada paso con GPU",
    "verificadores": "open-instruct a4cd966 (regla 13)",
    "modelo": {"alias": "qwen17b", "lote": 16, "presupuesto": 32_000_000, "semilla_consulta": 1},
    "cache": "caché de la T4 de la primera entrega recalificado con a4cd966 en una carpeta nueva de Drive; el "
             "original no se modifica. preparar comprueba que la recalificación cambie los 31 veredictos de la Fase 0",
    "orden": ["preparar (sin GPU)", "a) tiempo", "b) pendiente", "c) estrategia", "d) subespacio",
              "entrega (solo si c mejora al menos 3 puntos)"],
    "prioridad": "si el tiempo de Colab no alcanza, (c) va antes que (d)",
    "pasos": {
        "tiempo": {
            "objetivo": "costo por consulta en la T4 (regla 15) y comprobación de que el tiempo real crece "
                        "linealmente con n",
            "configuraciones": "4 configuraciones al azar del espacio (temperatura 0,0), semilla 7101",
            "instancias": "las primeras n de una permutación al azar de las 100 de búsqueda, semilla 7102",
            "n": [10, 25, 50, 100],
            "sin_reutilizar": "cada medición usa un caché vacío propio (carpeta fase7_tiempo/), así que genera "
                              "todas sus respuestas; no se mezcla con el caché principal",
            "calentamiento": "una evaluación de 2 instancias antes de medir (se descarta)",
            "consultas": 4 * (10 + 25 + 50 + 100) + 2,
            "tope": 4 * (10 + 25 + 50 + 100) + 2,
            "analisis": "ajuste tiempo = a + b·n por mínimos cuadrados (b = segundos por consulta marginal); "
                        "pendiente log-log; efecto del lote de 16 (el tiempo sube por escalones: ⌈n/16⌉ lotes "
                        "nominales)",
        },
        "pendiente": {
            "objetivo": "completar el camino del Algoritmo 3 con a4cd966: la única configuración que falta es "
                        "(0,0,0,6,1) (resultados/fase2_coordenadas_reproduccion.json)",
            "consultas": 100, "tope": 100,
            "si_supera": "si (0,0,0,6,1) supera a la mejor (13 %), el camino cambia y puede necesitar hasta "
                         "4.400 consultas; el paso se detiene en el tope y se pide autorización",
        },
        "estrategia": {
            "objetivo": "aplicar la estrategia elegida en la Fase 5 (resultados/fase5_estrategias.json)",
            "estrategia": "dos ranuras + Successive Halving, n0 = 2, hasta 2 rondas, desde el resultado del "
                          "Algoritmo 3 (orden de ranuras por la hipótesis de la primera entrega)",
            "semilla_instancias": "7300 (en cada ronda, '7300|ronda')",
            "consultas_por_ronda_de_filtro": costo_sh(490, 2, 100)["con_reutilizar"] + costo_sh(490, 2, 100)["completar_ganador"],
            "consultas_estimadas": "media ≈ 7.600, percentil 90 ≈ 11.200 (Fase 5, casos calibrados)",
            "tope": 15000,
            "si_se_agota": "se reporta la mejor configuración evaluada sobre las 100 instancias hasta ese momento",
        },
        "subespacio": {
            "objetivo": "óptimo exacto en un subespacio real y comparación de los algoritmos con datos reales",
            "opciones": "2 opciones por ranura elegidas al azar con semilla 7400, sin ningún otro criterio "
                        "(2^5 = 32 configuraciones, temperatura 0,0)",
            "consultas": 3200, "tope": 3200,
            "algoritmos": {
                "exacto": "fuerza bruta (el backtracking no aplica: con el modelo real no hay cota admisible)",
                "coordenadas": "Algoritmo 3 dentro del subespacio (desde la primera opción de cada ranura)",
                "successive_halving": "n0 ∈ {1, 2, 4}, permutaciones 1 a 100",
                "reparto": "uniforme y UCB1 con B = b·32, b ∈ {2, 4, 8, 16, 32}, permutaciones 1 a 100",
            },
            "costo_extra": "0: después de la fuerza bruta todo sale del caché",
        },
        "entrega": {
            "regla": "entrega.json cambia solo si la mejor configuración nueva supera a la actual por al menos "
                     "3 puntos en búsqueda (regla 16), con los verificadores a4cd966 y las mismas 100 instancias",
            "si_cambia": "validar(n=None) sobre las 87 de validación (87 consultas), escribir entrega_propuesta.json "
                         "en los resultados de Drive, copiarlo al repositorio y comprobar el notebook de evaluación "
                         "en Colab",
            "consultas": 87, "tope": 87,
        },
    },
    "estimacion": {
        "segundos_por_consulta": "2,1 (primera entrega, sin respaldo) hasta que (a) lo mida",
        "horas_efectivas_por_sesion": 3,
    },
}

SEMILLA_CONFIGS_TIEMPO, SEMILLA_PERMUTACION_TIEMPO = 7101, 7102
SEMILLA_SH, SEMILLA_SUBESPACIO = 7300, 7400
NS_TIEMPO = [10, 25, 50, 100]
MARGEN_ENTREGA = 0.03
CONFIG_ACTUAL = {"rol": 0, "estrategia": 0, "formato": 0, "estilo": 5, "cierre": 1, "temperatura": 0.0}


# ---------------------------------------------------------------- apoyo

def segundos_por_consulta():
    try:
        return cargar_resultado("fase7_tiempo")["datos"]["segundos_por_consulta_marginal"], "medido en (a)"
    except FileNotFoundError:
        return 2.1, "referencia sin respaldo (2,1 s)"


def mostrar_estimacion(paso, consultas):
    spc, fuente = segundos_por_consulta()
    horas = consultas * spc / 3600
    sesiones = math.ceil(horas / PLAN["estimacion"]["horas_efectivas_por_sesion"])
    print(f"[{paso}] consultas nuevas (a lo sumo): {consultas}  ·  tiempo estimado: {horas:.2f} h "
          f"({spc:.3g} s/consulta, {fuente})  ·  sesiones de 3 h: {sesiones}")


def datos():
    rutas.preparar_modulos_del_curso()
    from ayudas import cargar_datos, dividir

    return dividir(cargar_datos(str(rutas.RAIZ / "datos_visibles.json")))


def oraculo_solo_cache(busqueda, validacion):
    from oraculo_ada.oraculos.real import OraculoReal, oraculo_curso_desde_cache, ruta_libro_consultas

    curso = oraculo_curso_desde_cache(rutas.dir_cache() / "cache_oraculo.json", busqueda, validacion)
    return OraculoReal(curso, busqueda, hardware="t4", ruta_libro=ruta_libro_consultas("t4"))


def oraculo_t4(limite):
    from oraculo_ada.oraculos.real import crear_oraculo_real

    return crear_oraculo_real("t4", directorio_cache=rutas.dir_cache(), limite_consultas_nuevas=limite)


def limite_restante(nombre_paso, oraculo, tope):
    """Tope para esta sesión = tope del paso − consultas que el paso ya gastó en sesiones anteriores."""
    ruta = rutas.dir_resultados() / f"fase7_{nombre_paso}_contador.json"
    if ruta.exists():
        inicio = json.loads(ruta.read_text(encoding="utf-8"))["libro_al_empezar"]
    else:
        inicio = oraculo.total_registrado()
        ruta.write_text(json.dumps({"libro_al_empezar": inicio}), encoding="utf-8")
    gastadas = oraculo.total_registrado() - inicio
    return max(0, tope - gastadas), gastadas


def mejor_evaluada(oraculo):
    """Mejor configuración evaluada sobre todas las instancias (de la historia del oráculo)."""
    completas = [h for h in oraculo.historial if h["instancias"] == oraculo.n and not h.get("validacion")]
    if not completas:
        return None, None
    h = max(completas, key=lambda x: x["aciertos"])
    return h["config"], h["aciertos"] / oraculo.n


# ---------------------------------------------------------------- pasos

def paso_plan(_):
    from oraculo_ada.experimentos.plan import escribir_plan

    print("plan escrito en", escribir_plan("fase7_plan", PLAN))


def paso_preparar(args):
    from oraculo_ada.oraculos.real import registrar_primera_entrega
    from oraculo_ada.oraculos.verificacion import recalificar_cache

    busqueda, validacion = datos()
    destino = rutas.dir_cache() / "cache_oraculo.json"
    esperados = json.loads((rutas.RAIZ / "resultados" / "fase0_verificacion_cache.json").read_text(encoding="utf-8"))
    esperados = esperados["B_recalificacion"]["veredictos_distintos"]
    if destino.exists():
        print("el caché recalificado ya existe:", destino)
        try:                                    # conserva lo que midió la primera vez
            previos = cargar_resultado("fase7_preparar")["datos"]["veredictos_distintos"]
            cambios = None if previos is None else [None] * previos
        except FileNotFoundError:
            cambios = None
    else:
        if not args.cache_original or not Path(args.cache_original).exists():
            raise SystemExit("falta --cache-original con el caché de la T4 de la primera entrega")
        cambios = recalificar_cache(args.cache_original, destino, busqueda + validacion)
        if len(cambios) != esperados:
            destino.unlink()
            raise SystemExit(f"la recalificación cambió {len(cambios)} veredictos y en la Fase 0 fueron {esperados}: "
                             "los verificadores no son a4cd966")
    o = oraculo_solo_cache(busqueda, validacion)
    if o.total_registrado() == 0:
        registrar_primera_entrega(o, rutas.RAIZ / "resultados" / "registro_busqueda.csv", busqueda,
                                  config_validada=o.config([0, 0, 0, 5, 1]), n_validacion=len(validacion))
    actual = o.evaluar(o.config([0, 0, 0, 5, 1])).precision
    guardar_resultado("fase7_preparar", descripcion="Fase 7: caché de la T4 recalificado con a4cd966 y libro de "
                      "consultas de la primera entrega", parametros={"cache_original": args.cache_original},
                      semilla=None, datos={"veredictos_distintos": None if cambios is None else len(cambios),
                                           "esperados_fase0": esperados, "consultas_en_libro": o.total_registrado(),
                                           "precision_configuracion_actual": actual})
    print(f"listo: {o.total_registrado()} consultas en el libro; (0,0,0,5,1) = {actual:.0%} en búsqueda (a4cd966)")


def paso_tiempo(args):
    busqueda, validacion = datos()
    import oraculo as curso

    plan = PLAN["pasos"]["tiempo"]
    espacio_base = OraculoBase(list(curso.CATALOGO), {r: range(len(curso.CATALOGO[r])) for r in curso.CATALOGO}, [])
    configs = muestra_configuraciones(espacio_base, 4, SEMILLA_CONFIGS_TIEMPO)
    orden = random.Random(SEMILLA_PERMUTACION_TIEMPO).sample(busqueda, len(busqueda))
    ruta_progreso = rutas.dir_resultados() / "fase7_tiempo_progreso.json"
    progreso = json.loads(ruta_progreso.read_text(encoding="utf-8")) if ruta_progreso.exists() else []
    hechas = {(p["config_indice"], p["n"]) for p in progreso}
    faltan = sum(n for j in range(4) for n in NS_TIEMPO if (j, n) not in hechas)
    mostrar_estimacion("tiempo", faltan + (2 if faltan else 0))
    if not args.confirmar or not faltan:
        if not faltan:
            print("todas las mediciones están hechas")
        return
    import torch
    from ayudas import cargar_modelo

    verificar_hardware("t4")
    modelo = cargar_modelo("qwen17b")
    oficial = {tuple(c[r] for r in curso.RANURAS) + (c["temperatura"],): c for c in curso.espacio()}
    def config_oficial(c):
        return oficial[tuple(c[r] for r in curso.RANURAS) + (c["temperatura"],)]
    curso.Oraculo(modelo, busqueda, cache=None, lote=16, presupuesto=32_000_000).evaluar(
        config_oficial(configs[0]), orden[:2])                     # calentamiento (se descarta)
    carpeta = rutas.dir_cache() / "fase7_tiempo"
    carpeta.mkdir(exist_ok=True)
    for j, c in enumerate(configs):
        for n in NS_TIEMPO:
            if (j, n) in hechas:
                continue
            ruta = carpeta / f"c{j}_n{n}.json"
            ruta.unlink(missing_ok=True)                            # caché vacío: genera todas las respuestas
            o = curso.Oraculo(modelo, busqueda, validacion, cache=str(ruta), lote=16, presupuesto=32_000_000)
            torch.cuda.synchronize()
            t0 = time.perf_counter()
            r = o.evaluar(config_oficial(c), orden[:n], semilla=1)
            torch.cuda.synchronize()
            seg = time.perf_counter() - t0
            progreso.append({"config_indice": j, "config": c, "n": n, "segundos": seg, "segundos_por_consulta": seg / n,
                             "precision": r.precision, "lotes_nominales": math.ceil(n / 16)})
            ruta_progreso.write_text(json.dumps(progreso, indent=1), encoding="utf-8")
            print(f"config {j} n={n}: {seg:.1f} s ({seg / n:.2f} s/consulta)", flush=True)
    # análisis
    por_n = {n: [p["segundos"] for p in progreso if p["n"] == n] for n in NS_TIEMPO}
    medias = [statistics.fmean(por_n[n]) for n in NS_TIEMPO]
    a, b = ajustar_combinacion(medias, [[1] * len(NS_TIEMPO), NS_TIEMPO])
    guardar_resultado("fase7_tiempo", descripcion="Fase 7 (a): tiempo real en la T4 contra n, sin caché, y costo "
                      "por consulta", parametros=plan,
                      semilla={"configuraciones": SEMILLA_CONFIGS_TIEMPO, "instancias": SEMILLA_PERMUTACION_TIEMPO},
                      datos={"mediciones": progreso, "n": NS_TIEMPO, "segundos_medios": medias,
                             "ajuste_a_mas_b_n": {"a": a, "b": b}, "segundos_por_consulta_marginal": b,
                             "segundos_por_consulta_n100": statistics.fmean(p["segundos_por_consulta"]
                                                                           for p in progreso if p["n"] == 100),
                             "pendiente_loglog": pendiente_loglog(NS_TIEMPO, medias)})
    print(f"costo por consulta (marginal): {b:.3f} s; pendiente log-log {pendiente_loglog(NS_TIEMPO, medias):.3f}")


def paso_pendiente(args):

    mostrar_estimacion("pendiente", PLAN["pasos"]["pendiente"]["tope"])
    if not args.confirmar:
        return
    o, busqueda, _ = oraculo_t4(None)
    restante, gastadas = limite_restante("pendiente", o, PLAN["pasos"]["pendiente"]["tope"])
    o.limite_consultas_nuevas = restante                       # protección adicional del oráculo
    r = ascenso_coordenadas(o, hipotesis=HIPOTESIS_PRIMERA_ENTREGA, presupuesto=restante)
    completo = not r.presupuesto_agotado
    datos_r = {"mejor_config": r.mejor_config, "mejor_precision": r.mejor_precision,
               "movimientos": r.movimientos, "evaluaciones": r.evaluaciones, "pasadas": r.pasadas,
               "convergio": r.convergio, "registro": r.registro, "presupuesto": restante,
               "completo": completo, "consultas_nuevas_sesion": o.consultas,
               "consultas_nuevas_sesiones_previas": gastadas}
    guardar_resultado("fase7_pendiente", descripcion="Fase 7 (b): camino completo del Algoritmo 3 con a4cd966",
                      parametros=PLAN["pasos"]["pendiente"], semilla=1, datos=datos_r)
    print("completo" if completo else "DETENIDO EN EL TOPE: pedir autorización", datos_r.get("mejor_precision"))


def paso_estrategia(args):

    tope = PLAN["pasos"]["estrategia"]["tope"]
    mostrar_estimacion("estrategia", tope)
    if not args.confirmar:
        return
    o, _, _ = oraculo_t4(None)
    restante, gastadas = limite_restante("estrategia", o, tope)
    o.limite_consultas_nuevas = restante                       # protección adicional del oráculo
    t0 = time.perf_counter()
    r = dos_ranuras_sh(o, n0=2, rondas=2, semilla_instancias=SEMILLA_SH, hipotesis=HIPOTESIS_PRIMERA_ENTREGA,
                       presupuesto=restante)
    completo, historia = not r["presupuesto_agotado"], r["historia"]
    config, p = mejor_evaluada(o)
    guardar_resultado("fase7_estrategia", descripcion="Fase 7 (c): dos ranuras + SH (n0 = 2, 2 rondas) con el modelo "
                      "real", parametros=PLAN["pasos"]["estrategia"], semilla={"instancias": SEMILLA_SH},
                      datos={"completo": completo, "mejor_config": config, "mejor_precision": p, "historia": historia,
                             "consultas_nuevas_sesion": o.consultas, "consultas_nuevas_sesiones_previas": gastadas,
                             "segundos_sesion": time.perf_counter() - t0})
    print(("completa" if completo else "truncada en el tope"), "· mejor:", config, p)


def paso_subespacio(args):
    from oraculo_ada.oraculos.subespacio import OraculoSubespacio, sortear_subespacio

    tope = PLAN["pasos"]["subespacio"]["tope"]
    busqueda, validacion = datos()
    previo = oraculo_solo_cache(busqueda, validacion)            # sin modelo: solo para contar lo ya evaluado
    opciones_previas = sortear_subespacio(previo, 2, SEMILLA_SUBESPACIO)
    faltan = sum(previo.n - len(previo.consultas_hechas(c))
                 for c in OraculoSubespacio(previo, opciones_previas).espacio())
    print("opciones del subespacio (semilla 7400):", opciones_previas)
    mostrar_estimacion("subespacio", faltan)
    if not args.confirmar:
        return
    o, _, _ = oraculo_t4(None)
    restante, gastadas = limite_restante("subespacio", o, tope)
    o.limite_consultas_nuevas = restante                       # protección adicional del oráculo
    opciones = sortear_subespacio(o, 2, SEMILLA_SUBESPACIO)
    sub = OraculoSubespacio(o, opciones)
    fb = fuerza_bruta(sub, presupuesto=restante)
    if fb.presupuesto_agotado:
        guardar_resultado("fase7_subespacio", descripcion="Fase 7 (d): detenido en el tope", parametros={},
                          semilla=SEMILLA_SUBESPACIO, datos={"completo": False,
                                                             "configuraciones_evaluadas": fb.configuraciones_evaluadas})
        print("DETENIDO EN EL TOPE")
        return
    verdad = {sub.clave(c): sub.evaluar(c).precision for c in sub.espacio()}       # todo en caché
    mejor = max(verdad.values())
    # Comparaciones sobre configuraciones ya evaluadas: el presupuesto de cada algoritmo cuenta
    # sus consultas propias (como si empezara con el caché vacío), no las nuevas para el caché.
    coord = ascenso_coordenadas(sub, hipotesis=HIPOTESIS_PRIMERA_ENTREGA)
    comparacion = {"coordenadas": {"config": coord.mejor_config, "precision": coord.mejor_precision,
                                   "regret": mejor - coord.mejor_precision,
                                   "consultas_si_fuera_nuevo": coord.configuraciones_distintas() * sub.n}}
    candidatos = list(sub.espacio())
    for n0 in (1, 2, 4):
        B_sh = costo_sh(32, n0, sub.n)["con_reutilizar"]
        regrets = [mejor - verdad[sub.clave(successive_halving(sub, candidatos, n0=n0, semilla_instancias=s,
                                                                evaluar_ganador=False, presupuesto=B_sh,
                                                                modo_presupuesto="propias").ganador)]
                   for s in range(1, 101)]
        comparacion[f"successive_halving_n0_{n0}"] = {"prob_elegir_mejor": sum(r <= 1e-12 for r in regrets) / 100,
                                                      "regret_medio": statistics.fmean(regrets),
                                                      "consultas": costo_sh(32, n0, sub.n)["con_reutilizar"]}
    for nombre, funcion in (("uniforme", reparto_uniforme), ("ucb1", reparto_ucb1)):
        for b in (2, 4, 8, 16, 32):
            regrets = [mejor - verdad[sub.clave(funcion(sub, candidatos, 32 * b, semilla_instancias=s,
                                                        modo_presupuesto="propias").elegido)]
                       for s in range(1, 101)]
            comparacion[f"{nombre}_B{32 * b}"] = {"prob_elegir_mejor": sum(r <= 1e-12 for r in regrets) / 100,
                                                  "regret_medio": statistics.fmean(regrets), "presupuesto": 32 * b}
    guardar_resultado("fase7_subespacio", descripcion="Fase 7 (d): subespacio real con óptimo exacto y comparación "
                      "de algoritmos", parametros=PLAN["pasos"]["subespacio"],
                      semilla={"subespacio": SEMILLA_SUBESPACIO, "permutaciones": "1 a 100"},
                      datos={"completo": True, "opciones": opciones, "optimo": mejor, "optimas": fb.optimas,
                             "precision_por_configuracion": {",".join(map(str, k)): v for k, v in verdad.items()},
                             "comparacion": comparacion, "consultas_fuerza_bruta_nuevas": fb.consultas_cobradas,
                             "consultas_nuevas_sesiones_previas": gastadas})
    print(f"óptimo exacto del subespacio: {mejor:.0%}; consultas nuevas: {fb.consultas_cobradas}")


def paso_entrega(args):
    est = cargar_resultado("fase7_estrategia")["datos"]
    o_actual = cargar_resultado("fase7_preparar")["datos"]["precision_configuracion_actual"]
    nueva, p = est["mejor_config"], est["mejor_precision"]
    cambia = p is not None and p >= o_actual + MARGEN_ENTREGA - 1e-12
    print(f"actual {o_actual:.0%} · nueva {p:.0%} {nueva} · ¿cambia? {cambia} (margen {MARGEN_ENTREGA:.0%})")
    if not cambia:
        guardar_resultado("fase7_entrega", descripcion="Fase 7: regla de entrega.json", parametros=PLAN["pasos"]["entrega"],
                          semilla=None, datos={"cambia": False, "actual": o_actual, "nueva": nueva, "precision_nueva": p})
        return
    mostrar_estimacion("entrega", PLAN["pasos"]["entrega"]["tope"])
    if not args.confirmar:
        return
    if args.semana is None:
        raise SystemExit("indique --semana para entrega.json")
    o, _, validacion = oraculo_t4(PLAN["pasos"]["entrega"]["tope"])    # tope de 87 consultas nuevas
    val = o.validar(o.config([nueva[r] for r in o.ranuras], temperatura=nueva["temperatura"]), n=None)
    propuesta = {"grupo": "G01", "config": {r: nueva[r] for r in o.ranuras} | {"temperatura": nueva["temperatura"]},
                 "semana": args.semana}
    (rutas.dir_resultados() / "entrega_propuesta.json").write_text(json.dumps(propuesta, indent=1), encoding="utf-8")
    guardar_resultado("fase7_entrega", descripcion="Fase 7: regla de entrega.json", parametros=PLAN["pasos"]["entrega"],
                      semilla=1, datos={"cambia": True, "actual": o_actual, "nueva": nueva, "precision_nueva": p,
                                        "validacion": {"aciertos": val.aciertos, "instancias": val.n,
                                                       "precision": val.precision}, "propuesta": propuesta})
    print("entrega_propuesta.json escrito; validación:", f"{val.precision:.1%}")


def paso_estado(_):
    for nombre in ("preparar", "tiempo", "pendiente", "estrategia", "subespacio", "entrega"):
        try:
            d = cargar_resultado(f"fase7_{nombre}")["datos"]
            print(f"{nombre:11s} hecho" + ("" if d.get("completo", True) else " (INCOMPLETO)"))
        except FileNotFoundError:
            print(f"{nombre:11s} pendiente")


PASOS = {"plan": paso_plan, "preparar": paso_preparar, "tiempo": paso_tiempo, "pendiente": paso_pendiente,
         "estrategia": paso_estrategia, "subespacio": paso_subespacio, "entrega": paso_entrega, "estado": paso_estado}

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("paso", choices=list(PASOS))
    ap.add_argument("--confirmar", action="store_true", help="autoriza el gasto de GPU del paso")
    ap.add_argument("--cache-original", help="(preparar) caché de la T4 de la primera entrega")
    ap.add_argument("--semana", type=int, help="(entrega) semana para entrega.json")
    PASOS[ap.parse_args().paso](ap.parse_args())
