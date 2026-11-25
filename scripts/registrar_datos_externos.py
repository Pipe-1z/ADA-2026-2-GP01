"""Registra en resultados/ datos externos que no produce el repositorio (CLAUDE.md, regla 4).

Cada dato se transcribe aquí una sola vez, con su fuente; los documentos lo toman de
resultados/datos_externos.json, nunca de este archivo ni a mano.

Uso: python scripts/registrar_datos_externos.py
"""

from oraculo_ada.registro import guardar_resultado

ENTREGA_PRIMERA = {"rol": 0, "estrategia": 0, "formato": 0, "estilo": 5, "cierre": 1, "temperatura": 0.0}

DATOS = {
    "test_privado_primera_entrega": {
        "descripcion": "Puntaje de la configuración de la primera entrega en el test privado de la docente",
        "configuracion": ENTREGA_PRIMERA,
        "puntaje": 0.1259,
        "maximo_teorico": 0.2007,
        "fuente": "Retroalimentación de la docente a la primera entrega, transmitida por el autor el 24 de "
                  "noviembre de 2026 (archivo previsto: docs/referencia/retroalimentacion_primera_entrega.txt, "
                  "todavía no presente en el repositorio)",
        "tipo": "dato externo: no lo genera el código del repositorio y no se puede reproducir (test privado)",
        "uso": "evidencia de que la configuración entregada está lejos del máximo del test privado, lo que "
               "justifica la estrategia de mejora de la Fase 7",
    },
}

if __name__ == "__main__":
    ruta = guardar_resultado("datos_externos",
                             descripcion="Datos externos al repositorio, transcritos con su fuente",
                             parametros={}, semilla=None, datos=DATOS)
    print("→", ruta)
