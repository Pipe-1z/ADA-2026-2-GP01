"""Fase 6: figuras de la validación experimental, generadas desde resultados/fase6_validacion.json.

Una figura por algoritmo (figuras/fase6_<algoritmo>.png): una fila por dimensión de tamaño
y una columna por medida (Q, K, tiempo de CPU), en escala log-log, con lo observado (media
± desviación de 5 repeticiones) y la curva teórica c·g con su constante ajustada.
El tiempo es de CPU con el oráculo sintético, no de GPU (se indica en cada figura).
"""

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from oraculo_ada import rutas
from oraculo_ada.registro import cargar_resultado

SUPERFICIE, TEXTO, TEXTO2, REJILLA = "#fcfcfb", "#0b0b0b", "#52514e", "#e4e3df"
OBSERVADO, TEORICO = "#2a78d6", "#eb6834"
TITULOS = {
    "fuerza_bruta": "Fuerza bruta", "backtracking_peor_caso": "Algoritmo 1: backtracking (peor caso construido)",
    "backtracking_3sat": "Algoritmo 1: backtracking en 3-SAT aleatorio (razón 4,26) frente al peor caso",
    "successive_halving": "Algoritmo 2: Successive Halving (n₀ = 1)",
    "coordenadas": "Algoritmo 3: ascenso por coordenadas (cota teórica)",
    "uniforme": "Algoritmo 4: reparto uniforme", "ucb1": "Algoritmo 4: UCB1",
}
MEDIDAS = {"Q": "Q (consultas)", "Q_sin": "Q sin reutilizar", "Q_con": "Q con reutilización",
           "K": "K (cotas calculadas)", "CPU": "Tiempo de CPU (s)"}
NOTA = "Tiempo de CPU con el oráculo sintético en esta máquina; no es tiempo de GPU."


def estilo(ax):
    ax.set_facecolor(SUPERFICIE)
    for lado in ("top", "right"):
        ax.spines[lado].set_visible(False)
    for lado in ("left", "bottom"):
        ax.spines[lado].set_color(REJILLA)
    ax.tick_params(colors=TEXTO2, labelsize=8)
    ax.grid(True, which="major", color=REJILLA, linewidth=0.6)
    ax.set_axisbelow(True)


def figura(algoritmo, filas):
    dimensiones = list(dict.fromkeys(f["dimension"] for f in filas))
    medidas = list(dict.fromkeys(f["medida"] for f in filas))
    fig, ejes = plt.subplots(len(dimensiones), len(medidas), figsize=(4.3 * len(medidas), 3.4 * len(dimensiones)),
                             facecolor=SUPERFICIE, squeeze=False)
    for i, dim in enumerate(dimensiones):
        for j, med in enumerate(medidas):
            ax = ejes[i][j]
            estilo(ax)
            f = next((x for x in filas if x["dimension"] == dim and x["medida"] == med), None)
            if f is None:
                ax.set_visible(False)
                continue
            xs, obs, des = f["eje_x"], f["observado_medio"], f["observado_desviacion"]
            teo = f["teorico_ajustado"]
            coef = ", ".join(f"{c:.3g}" for c in f["coeficientes"])
            ax.plot(xs, teo, color=TEORICO, linestyle="--", linewidth=2,
                    label=f"teórica ajustada ({f['teoria']}); coef. {coef}")
            ax.errorbar(xs, obs, yerr=des, color=OBSERVADO, marker="o", markersize=5, linewidth=0, elinewidth=1.2,
                        capsize=3, label="observado (media ± desv.)")
            ax.set_xscale("log")
            if min(obs) > 0:
                ax.set_yscale("log")
            ax.set_xlabel(f["etiqueta_tamano"], fontsize=9, color=TEXTO)
            ax.set_ylabel(MEDIDAS.get(med, med), fontsize=9, color=TEXTO)
            ax.set_title(f"pendiente log-log: observada {f['pendiente_loglog_observada']:.2f}, ajuste "
                         f"{f['pendiente_loglog_ajuste']:.2f}, término dominante "
                         f"{f['pendiente_loglog_termino_dominante']:.2f}", fontsize=7.5, color=TEXTO2)
            ax.legend(fontsize=6.5, frameon=False, loc="upper left")
    hay_cpu = "CPU" in medidas
    fig.suptitle(TITULOS.get(algoritmo, algoritmo), fontsize=11, color=TEXTO, y=0.995)
    if hay_cpu:
        fig.text(0.5, 0.005, NOTA, ha="center", fontsize=8.5, color=TEXTO2)
    fig.tight_layout(rect=(0, 0.03 if hay_cpu else 0, 1, 0.96))
    ruta = rutas.dir_figuras() / f"fase6_{algoritmo}.png"
    fig.savefig(ruta, dpi=150, facecolor=SUPERFICIE)
    plt.close(fig)
    return ruta


def main():
    resumen = cargar_resultado("fase6_validacion")["datos"]["resumen"]
    for algoritmo in dict.fromkeys(f["algoritmo"] for f in resumen):
        print("→", figura(algoritmo, [f for f in resumen if f["algoritmo"] == algoritmo]))


if __name__ == "__main__":
    main()
