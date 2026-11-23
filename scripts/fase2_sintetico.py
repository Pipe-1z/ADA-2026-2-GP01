"""Fase 2: fuerza bruta y Algoritmo 3 en casos sintéticos (sin GPU).

Casos:
- calibrado: ``generar_calibrado()`` (estadísticas del problema real).
- control: el mismo caso con la misma semilla pero sin el par acoplado (la
  estructura base es idéntica; solo faltan las interacciones dirigidas).
- independiente: cada ranura rompe solo su propia familia.

La métrica principal es el **número de consultas**. ``segundos_cpu`` es el tiempo
de CPU del oráculo sintético en esta máquina y **no es tiempo de GPU**.

Escribe resultados/fase2_sintetico.json.
"""

import random

from oraculo_ada.algoritmos import ascenso_coordenadas, cota_consultas_coordenadas, fuerza_bruta
from oraculo_ada.oraculos import OraculoSintetico, generar_calibrado, generar_conjuntivo
from oraculo_ada.oraculos.sintetico import CALIBRADO
from oraculo_ada.registro import guardar_resultado

RANURAS = ["rol", "estrategia", "formato", "estilo", "cierre"]
SEMILLA_INDEPENDIENTE = 7


def control_sin_acoplar():
    c = CALIBRADO
    return generar_conjuntivo(c["m"], c["k"], c["n"], c["semilla"], familias=c["familias"],
                              familias_por_instancia=c["familias_por_instancia"],
                              limpias_por_ranura=c["limpias_por_ranura"], fraccion_insoluble=c["fraccion_insoluble"],
                              prob_rompe=c["prob_rompe"], prob_rompe_opcion0=c["prob_rompe_opcion0"],
                              pares_acoplados=0, ranuras=RANURAS)


def independiente(n=100, k=8):
    rng = random.Random(SEMILLA_INDEPENDIENTE)
    limpia = {p: rng.randrange(k) for p in range(5)}
    rompe = {(p, a): (set() if a == limpia[p] else {f"f{p}"}) for p in range(5) for a in range(k)}
    familias = [f"f{p}" for p in range(5)]
    instancias = [(f,) for f in familias] + [tuple(rng.sample(familias, rng.choice([1, 2, 3])))
                                             for _ in range(n - 5)]
    o = OraculoSintetico("conjuntivo", 5, k, rompe=rompe, familias_instancia=instancias, ranuras=RANURAS,
                         parametros={"generador": "independiente", "semilla": SEMILLA_INDEPENDIENTE})
    return o


def caso(nombre, o):
    fb = fuerza_bruta(o, verdad_conocida=True)
    co = ascenso_coordenadas(o)
    cota = cota_consultas_coordenadas([o.k] * o.m, o.n, 3, len(o.temperaturas))
    fila = {
        "caso": nombre, "oraculo": o.descripcion(),
        "fuerza_bruta": fb.resumen(),
        "coordenadas": {
            "mejor_config": co.mejor_config, "mejor_precision": co.mejor_precision,
            "es_optimo": co.mejor_precision == fb.mejor_precision,
            "brecha_con_el_optimo": round(fb.mejor_precision - co.mejor_precision, 10),
            "evaluaciones": co.evaluaciones, "configuraciones_distintas": co.configuraciones_distintas(),
            "consultas_cobradas": co.consultas_cobradas, "consultas_solicitadas": co.consultas_solicitadas,
            "cota_consultas": cota, "pasadas": co.pasadas, "convergio": co.convergio,
            "movimientos": co.movimientos,
            "opciones_descartadas": sum(len(v) for v in co.descartadas.values()),
            "segundos_cpu": co.segundos,
        },
        "fraccion_de_consultas_frente_a_fuerza_bruta": co.consultas_cobradas / fb.consultas_oraculo_real,
    }
    print(f"{nombre:14s} Acc*={fb.mejor_precision:.2f} (fuerza bruta: {fb.consultas_oraculo_real} consultas) | "
          f"coordenadas {co.mejor_precision:.2f} con {co.consultas_cobradas} consultas (cota {cota})")
    return fila


def main():
    casos = [caso("calibrado", generar_calibrado()), caso("control", control_sin_acoplar()),
             caso("independiente", independiente())]
    guardar_resultado(
        "fase2_sintetico",
        descripcion="Fase 2: fuerza bruta (peor caso, consultas que cobraría el oráculo real) y Algoritmo 3 en "
                    "casos sintéticos. Métrica principal: consultas. segundos_cpu no es tiempo de GPU.",
        parametros={"max_pasadas": 3, "umbral_traza": 3, "semilla_consulta": 1,
                    "inicial": "primera opción de cada ranura"},
        semilla={"calibrado": CALIBRADO["semilla"], "independiente": SEMILLA_INDEPENDIENTE},
        datos=casos,
    )


if __name__ == "__main__":
    main()
