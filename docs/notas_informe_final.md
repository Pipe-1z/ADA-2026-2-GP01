# Notas para el informe final (Fase 8)

Puntos que deben entrar en el informe final, anotados durante el desarrollo. Ningún número se copia de aquí al informe: cada uno se toma del archivo de `resultados/` indicado, mediante el script que genere la tabla o el texto.

## 1. Evidencia de que las ranuras reales interactúan (apoya los casos con pares acoplados)

- En el registro de la primera entrega, la opción `estilo = 5` dio una precisión con `cierre = 0` (paso 6, configuración (0,0,0,5,0)) y otra mayor con `cierre = 1` (paso 40, configuración (0,0,0,5,1)). El efecto de una opción depende de las demás: las ranuras no son independientes.
- Fuente: `resultados/registro_busqueda.csv` (veredictos originales) y `resultados/registro_busqueda_recalificado_a4cd966.csv` (verificadores de referencia). La diferencia se mantiene con los dos verificadores.
- Uso en el informe: justificar que el oráculo sintético incluya interacciones y pares acoplados (CLAUDE.md §7.1) y que el riesgo de óptimos locales del Algoritmo 3 no es solo teórico. Aclarar que esto prueba **dependencia** entre ranuras, no que el mecanismo real sea exactamente un par acoplado.

## 2. Etiqueta del diagnóstico de la Fase 2b: "descartada solo por cambio de familia"

- En `resultados/fase2b_estrategias.json` (`diagnostico_original`), la cuenta `acoplada_descartada_solo_por_cambio_de_familia` es alta. Es técnicamente correcta: los aumentos de 3 o más fallos en una familia que dispararon el descarte vienen de instancias que ya fallaban y cambiaron de primera restricción violada; las instancias que fallan por primera vez se reparten entre familias y ninguna llega al umbral.
- Pero esas opciones **sí empeoran la precisión** (una opción acoplada sola deja la configuración en 0), así que el descarte no causó el estancamiento: la opción se habría rechazado igual por precisión. El informe debe explicarlo para que la etiqueta no se lea como "la poda descartó opciones buenas".
- Dato que sí importa: la poda **nunca** descartó la opción limpia de una ranura libre (sin acoplar) en las variantes calibradas (`libre_descartada` no aparece en el diagnóstico).

## 3. Techo según el monitor

- Citar en el texto, en formato APA 7 de comunicación personal: "(JuManoel, comunicación personal, noviembre de 2026)", sin entrada en la lista de referencias (CLAUDE.md §1).

## 4. Algoritmo 1: dónde poda poco la cota, y la NP-dureza

- Destacar que en los casos **disyuntivos** (el modelo de la reducción desde 3-SAT) la cota casi no poda: en el disyuntivo genérico con k = 8 y tres pares por instancia, el backtracking evalúa prácticamente todas las hojas (`resultados/fase3_backtracking.json`, familia `disyuntivo`), mientras que en los casos conjuntivos (los del curso) evalúa una fracción mínima.
- Relacionarlo con la NP-dureza demostrada: en el modelo que contiene a 3-SAT ninguna cota sencilla puede garantizar poda (si siempre podara a un número polinomial de nodos, se resolvería 3-SAT en tiempo polinomial).
- **Matiz obligatorio para no exagerar:** en las fórmulas 3-SAT aleatorias medidas (k = 2) la cota sí poda una fracción grande del árbol, aunque los nodos explorados crecen de forma exponencial con el número de variables (familias `3sat_v*` del mismo archivo). La NP-dureza es una afirmación de peor caso.
- Presentar Q (consultas) y K (cómputo de cotas) por separado (`docs/derivaciones/algoritmo1_backtracking.md`, Sección 6), y la respuesta sobre el modelo de información de la cota (Sección 7).

## 5. Correcciones de la primera entrega

- Ver `docs/correcciones_primera_entrega.md` (Fases 8 y 9).
