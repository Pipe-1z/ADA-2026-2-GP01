"""Fase 2: el Algoritmo 3 extraído reproduce la búsqueda de la primera entrega (sin GPU).

1. Con el caché de la T4 y sus veredictos originales (verificadores de la primera
   entrega), ejecuta ``ascenso_coordenadas`` y compara cada evaluación con
   ``resultados/registro_busqueda.csv``: fase, ranura, configuración, precisión,
   fallos por familia y nota de descarte. También repite ``validar``.
2. Con el caché recalificado con open-instruct a4cd966 (Fase 0), ejecuta el mismo
   algoritmo y compara su camino de decisiones con el de la primera entrega. Si
   necesita una configuración que no está en el caché, se detiene (no usa GPU) y
   reporta dónde.

Escribe resultados/fase2_coordenadas_reproduccion.json y
resultados/fase2_coordenadas_a4cd966.csv.

Uso, desde la raíz del repositorio, con PYTHONUTF8=1:
    python scripts/fase2_reproducir_coordenadas.py
"""

import csv
import json
import tempfile
from pathlib import Path

from oraculo_ada import rutas
from oraculo_ada.algoritmos.coordenadas import (
    HIPOTESIS_PRIMERA_ENTREGA,
    ascenso_coordenadas,
    cota_consultas_coordenadas,
)
from oraculo_ada.oraculos.real import ConsultaFueraDeCache, OraculoReal, oraculo_curso_desde_cache
from oraculo_ada.registro import guardar_csv, guardar_resultado

PARAMETROS = {"semilla": 1, "max_pasadas": 3, "umbral_traza": 3, "probar_temperaturas": True,
              "hipotesis": HIPOTESIS_PRIMERA_ENTREGA}
CACHES = {
    "original": "cache_oraculo.json",
    "a4cd966": "cache_oraculo_recalificado_a4cd966.json",
}


def fila_registro(f, ranuras):
    """Una fila del registro de la primera entrega en el mismo formato que el algoritmo."""
    config = {r: int(f[r]) for r in ranuras}
    config["temperatura"] = float(f["temperatura"])
    return {"paso": int(f["paso"]), "fase": f["fase"], "ranura_probada": f["ranura_probada"], "config": config,
            "precision": float(f["precision"]), "fallos_por_familia": f["fallos_por_familia"], "nota": f["nota"]}


def comparar(filas_algoritmo, filas_registro, campos):
    diferencias = []
    for a, b in zip(filas_algoritmo, filas_registro):
        distintos = {c: {"algoritmo": a[c], "registro": b[c]} for c in campos if a[c] != b[c]}
        if distintos:
            diferencias.append({"paso": a["paso"], **distintos})
    return diferencias


def ejecutar(nombre_cache, busqueda, validacion, hipoteticos=None):
    """Ejecuta el Algoritmo 3 desde el caché.

    ``hipoteticos``: dict clave de configuración → función que devuelve un
    ``Resultado`` inventado para esa configuración (escenarios "qué pasaría si",
    sin GPU). Esas evaluaciones se marcan en la fila con ``hipotetica: True``.
    """
    hipoteticos = hipoteticos or {}
    curso = oraculo_curso_desde_cache(rutas.dir_cache() / nombre_cache, busqueda, validacion)
    with tempfile.TemporaryDirectory() as tmp:
        oraculo = OraculoReal(curso, busqueda, hardware="t4", ruta_libro=Path(tmp) / "libro.json")
        filas, pedido = [], {}
        evaluar_original = oraculo.evaluar

        def evaluar(config, *args, **kwargs):
            pedido["config"] = dict(config)
            clave = oraculo.clave(config)
            if clave in hipoteticos:
                return hipoteticos[clave](oraculo, config)
            return evaluar_original(config, *args, **kwargs)

        oraculo.evaluar = evaluar
        try:
            res = ascenso_coordenadas(oraculo, al_evaluar=filas.append, **PARAMETROS)
            fuera = None
        except ConsultaFueraDeCache:
            res = None
            fuera = {"paso": len(filas) + 1, "config": pedido["config"]}
        val = oraculo.validar(res.mejor_config, n=None) if res else None
        return res, filas, fuera, val, oraculo


def movs(res):
    """Movimientos sin las precisiones: (fase, ranura, de, a)."""
    return [(m["fase"], m["ranura"], m["de"], m["a"]) for m in res.movimientos]


def escenarios(fuera, filas, res_original, busqueda, validacion):
    """Qué falta para completar el camino con a4cd966 cuando una configuración no está en el caché.

    La configuración que falta solo puede (a) no superar a la mejor actual, o
    (b) superarla. En (a) se simulan sus dos variantes posibles (la poda la
    descarta o no) con un resultado inventado y se comprueba si todo lo demás
    sale del caché. En (b) el camino cambia y solo se puede acotar lo que falta.
    """
    from oraculo_ada.oraculos.base import Resultado

    faltante = fuera["config"]
    fase = filas[-1]["fase"] if filas else None
    mejor_actual = max((f for f in filas if f["fase"] != "temperatura"), key=lambda f: f["precision"])
    clave = tuple(faltante[r] for r in faltante if r != "temperatura") + (faltante["temperatura"],)

    def falla_todo(oraculo, config):
        trazas = [{"id": x["id"], "violo": "hipotetica:falla", "salida": None} for x in busqueda]
        return Resultado(aciertos=0, n=len(busqueda), trazas=trazas)

    def empata_con_la_mejor(oraculo, config):
        r = oraculo.oraculo.evaluar(oraculo.oficial(mejor_actual["config"]), busqueda, semilla=1)
        trazas = [{"id": t["id"], "violo": t["violo"], "salida": None} for t in r.trazas]
        return Resultado(aciertos=r.n - len(trazas), n=r.n, trazas=trazas)

    salida = {"configuracion_faltante": faltante, "paso": fuera["paso"], "fase": fase,
              "mejor_precision_en_ese_momento": mejor_actual["precision"], "casos": {}}
    for nombre, funcion in (("no_mejora_y_la_poda_la_descarta", falla_todo),
                            ("no_mejora_y_la_poda_no_la_descarta", empata_con_la_mejor)):
        res, filas_e, fuera_e, _, _ = ejecutar(CACHES["a4cd966"], busqueda, validacion, {clave: funcion})
        salida["casos"][nombre] = {
            "completa_desde_cache": fuera_e is None,
            "otra_consulta_fuera_de_cache": fuera_e,
            "evaluaciones": len(filas_e),
            "evaluaciones_nuevas_en_gpu": 1 if fuera_e is None else None,
            "consultas_nuevas_en_gpu": len(busqueda) if fuera_e is None else None,
            "mejor_config": res.mejor_config if res else None,
            "mejor_precision": res.mejor_precision if res else None,
            "decisiones": res.decisiones if res else None,
            "movimientos_iguales_a_la_primera_entrega": (movs(res) == movs(res_original)) if res else None,
        }

    # (b) la configuración faltante mejora: cota de evaluaciones restantes desde ese punto.
    descartadas = {}
    for f in filas:
        if f["nota"].startswith("descartada"):
            descartadas.setdefault(f["ranura_probada"], set()).add(f["config"][f["ranura_probada"]])
    orden = res_original.orden
    ranura_actual = next(f["ranura_probada"] for f in reversed(filas) if f["fase"] == fase)
    pasada = int(fase.split()[-1])
    k = 8
    vivas = lambda r: k - 1 - len(descartadas.get(r, ()))
    resto_pasada = sum(vivas(r) for r in orden[orden.index(ranura_actual) + 1:])
    pasadas_siguientes = (3 - pasada) * sum(vivas(r) for r in orden)
    cota = 1 + resto_pasada + pasadas_siguientes + 2
    salida["si_mejora"] = {
        "descripcion": "El camino cambia desde ese paso; cota superior de evaluaciones nuevas en GPU: la "
                       "faltante + las opciones no descartadas del resto de la pasada + las pasadas "
                       "siguientes + 2 temperaturas (la poda solo puede reducirla)",
        "descartadas_en_ese_momento": {r: sorted(v) for r, v in descartadas.items()},
        "cota_evaluaciones_nuevas": cota,
        "cota_consultas_nuevas": cota * len(busqueda),
    }
    return salida


def main():
    rutas.preparar_modulos_del_curso()
    from ayudas import cargar_datos, dividir

    busqueda, validacion = dividir(cargar_datos(str(rutas.RAIZ / "datos_visibles.json")))
    ranuras = ["rol", "estrategia", "formato", "estilo", "cierre"]
    with open(rutas.RAIZ / "resultados" / "registro_busqueda.csv", encoding="utf-8") as f:
        registro = [fila_registro(x, ranuras) for x in csv.DictReader(f)]
    campos = ["fase", "ranura_probada", "config", "precision", "fallos_por_familia", "nota"]

    # 1. veredictos originales
    res, filas, fuera, val, oraculo = ejecutar(CACHES["original"], busqueda, validacion)
    assert fuera is None, f"el registro original debería estar completo en el caché: {fuera}"
    diferencias = comparar(filas, registro, campos)
    original = {
        "evaluaciones": len(filas), "evaluaciones_registro": len(registro),
        "filas_con_diferencias": diferencias,
        "reproduce_exactamente": not diferencias and len(filas) == len(registro),
        "configuraciones_distintas": res.configuraciones_distintas(),
        "consultas_cobradas": res.consultas_cobradas, "consultas_solicitadas": res.consultas_solicitadas,
        "pasadas": res.pasadas, "convergio": res.convergio, "orden": res.orden,
        "decisiones": res.decisiones, "mejor_config": res.mejor_config, "mejor_precision": res.mejor_precision,
        "descartadas": res.descartadas,
        "opciones_descartadas": sum(len(v) for v in res.descartadas.values()),
        "validacion": {"aciertos": val.aciertos, "instancias": val.n, "precision": val.precision},
        "cota_consultas": cota_consultas_coordenadas([8] * 5, len(busqueda), 3, 3),
    }
    print(f"original: {len(filas)} evaluaciones, {len(diferencias)} filas distintas del registro, "
          f"{res.consultas_cobradas} consultas nuevas, mejor {res.mejor_config} {res.mejor_precision:.0%}, "
          f"validación {val.aciertos}/{val.n}")

    # 2. veredictos recalificados con a4cd966
    res2, filas2, fuera2, val2, _ = ejecutar(CACHES["a4cd966"], busqueda, validacion)
    camino = lambda fs: [(f["fase"], f["ranura_probada"], tuple(f["config"].values())) for f in fs]
    c_reg, c_nuevo = camino(registro), camino(filas2)
    primera = next((i for i, (a, b) in enumerate(zip(c_nuevo, c_reg)) if a != b), None)
    if primera is None and len(c_nuevo) != len(c_reg):
        primera = min(len(c_nuevo), len(c_reg))
    recal = {
        "evaluaciones_hechas": len(filas2),
        "camino_igual_al_registro": primera is None and fuera2 is None,
        "primera_evaluacion_distinta": None if primera is None else {
            "paso": primera + 1,
            "registro": registro[primera] if primera < len(registro) else None,
            "a4cd966": filas2[primera] if primera < len(filas2) else None,
        },
        "consulta_fuera_de_cache": fuera2,
        "precisiones_distintas_en_el_mismo_camino": [
            {"paso": a["paso"], "registro": b["precision"], "a4cd966": a["precision"]}
            for a, b in zip(filas2[:primera] if primera is not None else filas2, registro)
            if a["precision"] != b["precision"]],
    }
    if res2:
        recal.update({"pasadas": res2.pasadas, "convergio": res2.convergio, "orden": res2.orden,
                      "decisiones": res2.decisiones, "movimientos_iguales": movs(res2) == movs(res),
                      "mejor_config": res2.mejor_config, "mejor_precision": res2.mejor_precision,
                      "configuraciones_distintas": res2.configuraciones_distintas(),
                      "consultas_cobradas": res2.consultas_cobradas,
                      "evaluaciones_fuera_de_cache": 0,
                      "validacion": {"aciertos": val2.aciertos, "instancias": val2.n, "precision": val2.precision}})
    print(f"a4cd966: {len(filas2)} evaluaciones; primera distinta: {recal['primera_evaluacion_distinta'] and recal['primera_evaluacion_distinta']['paso']}; "
          f"fuera de caché: {fuera2}")
    if res2:
        print("  decisiones:", res2.decisiones, "| iguales:", recal["movimientos_iguales"],
              "| mejor", res2.mejor_config, f"{res2.mejor_precision:.0%}")

    if fuera2:
        recal["escenarios_sin_gpu"] = escenarios(fuera2, filas2, res, busqueda, validacion)

    guardar_csv("fase2_coordenadas_a4cd966", [
        {"paso": f["paso"], "fase": f["fase"], "ranura_probada": f["ranura_probada"], **f["config"],
         "precision": f["precision"], "consultas_nuevas": f["consultas_nuevas"],
         "fallos_por_familia": f["fallos_por_familia"], "nota": f["nota"]} for f in filas2])
    ruta = guardar_resultado(
        "fase2_coordenadas_reproduccion",
        descripcion="Fase 2: Algoritmo 3 extraído frente al registro de la primera entrega, con veredictos "
                    "originales y recalificados con open-instruct a4cd966 (desde el caché de la T4, sin GPU)",
        parametros={**PARAMETROS, "caches": CACHES, "instancias": len(busqueda)},
        semilla=PARAMETROS["semilla"],
        datos={"veredictos_originales": original, "veredictos_a4cd966": recal},
    )
    print("→", ruta)


if __name__ == "__main__":
    main()
