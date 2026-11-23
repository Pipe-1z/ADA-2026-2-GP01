"""Fase 1: demostración del oráculo sintético y del registro de experimentos (sin GPU).

Genera un caso de cada modelo, calcula su óptimo exacto por fuerza bruta, mide
el tiempo de la fuerza bruta y comprueba el contador de consultas. Escribe
resultados/fase1_demo_sintetico.json con parámetros, semillas, versión del
código y hardware.

Uso, desde la raíz del repositorio:  python scripts/fase1_demo_sintetico.py
"""

from oraculo_ada.medicion import Cronometro
from oraculo_ada.oraculos import desde_3sat, generar_3sat, generar_conjuntivo, generar_disyuntivo
from oraculo_ada.registro import guardar_resultado

SEMILLA = 1
RANURAS = ["rol", "estrategia", "formato", "estilo", "cierre"]


def resumir(nombre, oraculo):
    with Cronometro() as reloj:
        acc, optimas = oraculo.optimo_exacto()
    assert oraculo.consultas == 0, "la verdad conocida no debe cobrar consultas"
    x = optimas[0]
    r1 = oraculo.evaluar(x)
    r2 = oraculo.evaluar(x)
    fila = {
        "caso": nombre,
        "oraculo": oraculo.descripcion(),
        "tamano_espacio": oraculo.tamano_espacio(),
        "precision_optima": acc,
        "configuraciones_optimas": len(optimas),
        "primera_optima": {r: x[r] for r in oraculo.ranuras},
        "segundos_fuerza_bruta": round(reloj.segundos, 3),
        "contador": {"primera_evaluacion_nuevas": r1.consultas_nuevas, "segunda_evaluacion_nuevas": r2.consultas_nuevas,
                     "consultas": oraculo.consultas, "consultas_solicitadas": oraculo.consultas_solicitadas},
    }
    print(f"{nombre:45s} |C|={fila['tamano_espacio']:6d}  Acc*={acc:.3f}  óptimas={len(optimas):4d}  "
          f"fuerza bruta {reloj.segundos:6.2f} s  consultas {r1.consultas_nuevas}+{r2.consultas_nuevas}")
    return fila


def main():
    casos = [
        ("conjuntivo, 1 limpia por ranura, sin interacciones",
         generar_conjuntivo(5, 8, 100, SEMILLA, ranuras=RANURAS)),
        ("conjuntivo, 1 limpia por ranura, 10 interacciones",
         generar_conjuntivo(5, 8, 100, SEMILLA, ranuras=RANURAS, interacciones=10)),
        ("conjuntivo, sin limpias, 10 interacciones",
         generar_conjuntivo(5, 8, 100, SEMILLA, ranuras=RANURAS, limpias_por_ranura=0, interacciones=10)),
        ("disyuntivo, 3 pares por instancia, 10 interacciones",
         generar_disyuntivo(5, 8, 100, SEMILLA, ranuras=RANURAS, interacciones=10)),
        ("3-SAT del informe (Tabla 5)", desde_3sat([[1, -2, 3], [-1, 2, 3]], 3)),
        ("3-SAT aleatorio, 12 variables, razón 4,26", generar_3sat(12, 4.26, SEMILLA)),
    ]
    filas = [resumir(nombre, o) for nombre, o in casos]
    ruta = guardar_resultado(
        "fase1_demo_sintetico",
        descripcion="Fase 1: óptimo exacto por fuerza bruta y contador de consultas en casos sintéticos de los dos modelos",
        parametros={"m": 5, "k": 8, "n": 100, "ranuras": RANURAS},
        semilla=SEMILLA,
        datos=filas,
    )
    print(f"→ {ruta}")


if __name__ == "__main__":
    main()
