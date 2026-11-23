"""Recalificación de salidas guardadas con una versión dada de los verificadores (open-instruct).

Usa el procedimiento estándar de IFEval con la API pública de ``open_instruct.IFEvalG``, no el
contenido interno de ``oraculo.py`` (CLAUDE.md, regla 12). Se validó en la Fase 0: con
``a4cd966`` reproduce exactamente la calificación del oráculo en las 200 salidas de la GPU local.
"""

import json


def calificar(instancia, salida):
    """(1, None) si la salida cumple todas las restricciones; (0, id de la primera incumplida) si no."""
    from open_instruct.IFEvalG import instructions_registry as reg

    for iid, kw in zip(instancia["ids"], instancia["kwargs"]):
        verificador = reg.INSTRUCTION_DICT[iid](iid)
        verificador.build_description(**kw)
        args = verificador.get_instruction_args()
        if args and "prompt" in args:
            verificador.build_description(prompt=instancia["prompt"])
        if not verificador.check_following(salida):
            return 0, iid
    return 1, None


def recalificar_cache(ruta_entrada, ruta_salida, instancias):
    """Recalifica cada entrada ``[aprobada, violada, salida]`` del caché y escribe uno nuevo.

    La clave del caché contiene el id de la instancia (tercer campo separado por ``|``).
    Devuelve la lista de entradas cuyo veredicto cambió.
    """
    por_id = {str(x["id"]): x for x in instancias}
    entrada = json.loads(open(ruta_entrada, encoding="utf-8").read())
    salida, cambios = {}, []
    for clave, (r, violo, texto) in entrada.items():
        r2, violo2 = calificar(por_id[clave.split("|")[2]], texto)
        salida[clave] = [r2, violo2, texto]
        if (r2, violo2) != (r, violo):
            cambios.append({"clave": clave, "antes": [r, violo], "despues": [r2, violo2]})
    with open(ruta_salida, "w", encoding="utf-8") as f:
        json.dump(salida, f)
    return cambios
