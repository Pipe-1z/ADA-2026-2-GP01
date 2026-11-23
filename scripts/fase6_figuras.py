"""Fase 6: figuras de la validación experimental, generadas desde resultados/fase6_validacion.json.

Una figura por algoritmo (figuras/fase6_<algoritmo>.png): una fila por dimensión de tamaño
y una columna por medida (Q, K, tiempo de CPU), en escala log-log, con lo observado (media
de 5 repeticiones; barras: mínimo y máximo) y la curva teórica con sus coeficientes ajustados
(en 3-SAT, el peor caso sin escalar). El tiempo es de CPU con el oráculo sintético, no de GPU
(se indica en cada figura que lo contiene).
"""

import textwrap

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import FixedLocator, FuncFormatter, NullFormatter, NullLocator

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


def numero(v, _=None):
    if v >= 1e4 or v < 1e-2:
        return f"{v:.0e}".replace("e+0", "e").replace("e-0", "e-")
    return f"{v:g}"


def estilo(ax):
    ax.set_facecolor(SUPERFICIE)
    for lado in ("top", "right"):
        ax.spines[lado].set_visible(False)
    for lado in ("left", "bottom"):
        ax.spines[lado].set_color(REJILLA)
    ax.tick_params(colors=TEXTO2, labelsize=7.5)
    ax.grid(True, which="major", color=REJILLA, linewidth=0.6)
    ax.set_axisbelow(True)


def figura(algoritmo, filas):
    dimensiones = list(dict.fromkeys(f["dimension"] for f in filas))
    medidas = list(dict.fromkeys(f["medida"] for f in filas))
    fig, ejes = plt.subplots(len(dimensiones), len(medidas), figsize=(5.0 * len(medidas), 3.9 * len(dimensiones)),
                             facecolor=SUPERFICIE, squeeze=False)
    for i, dim in enumerate(dimensiones):
        for j, med in enumerate(medidas):
            ax = ejes[i][j]
            estilo(ax)
            f = next((x for x in filas if x["dimension"] == dim and x["medida"] == med), None)
            if f is None:
                ax.set_visible(False)
                continue
            xs, obs = f["eje_x"], f["observado_medio"]
            bajo = [o - mn for o, mn in zip(obs, f["observado_minimo"])]
            alto = [mx - o for o, mx in zip(obs, f["observado_maximo"])]
            if f["curva_sin_ajuste"]:
                etiqueta_teo = ("peor caso (constante de CPU del peor caso construido)" if med == "CPU"
                                else "peor caso (sin escalar)")
            else:
                etiqueta_teo = "teórica ajustada"
            ax.plot(xs, f["teorico_ajustado"], color=TEORICO, linestyle="--", linewidth=2, label=etiqueta_teo)
            ax.errorbar(xs, obs, yerr=[bajo, alto], color=OBSERVADO, marker="o", markersize=5, linewidth=0,
                        elinewidth=1.2, capsize=3, label="observado (media; barras mín–máx)")
            ax.set_xscale("log")
            if min(f["observado_minimo"]) > 0 and min(f["teorico_ajustado"]) > 0:
                ax.set_yscale("log")
            ax.xaxis.set_major_locator(FixedLocator(xs))
            ax.xaxis.set_major_formatter(FuncFormatter(numero))
            ax.xaxis.set_minor_locator(NullLocator())
            ax.xaxis.set_minor_formatter(NullFormatter())
            ax.set_xlabel(f["etiqueta_tamano"], fontsize=9, color=TEXTO)
            ax.set_ylabel(MEDIDAS.get(med, med), fontsize=9, color=TEXTO)
            coef = ", ".join(f"{c:.3g}" for c in f["coeficientes"])
            titulo = (f"modelo: {f['teoria']}; coef. {coef}\n"
                      f"pendiente log-log: obs. {f['pendiente_loglog_observada']:.2f} · ajuste "
                      f"{f['pendiente_loglog_ajuste']:.2f} · término dominante {f['pendiente_loglog_termino_dominante']:.2f}")
            ax.set_title("\n".join(textwrap.fill(linea, 70) for linea in titulo.split("\n")), fontsize=7, color=TEXTO2)
            ax.legend(fontsize=7, frameon=False, loc="best")
    hay_cpu = "CPU" in medidas
    fig.suptitle(TITULOS.get(algoritmo, algoritmo), fontsize=11, color=TEXTO, y=0.995)
    if hay_cpu:
        fig.text(0.5, 0.005, NOTA, ha="center", fontsize=8.5, color=TEXTO2)
    fig.tight_layout(rect=(0, 0.03 if hay_cpu else 0, 1, 0.965), h_pad=2.0, w_pad=1.5)
    ruta = rutas.dir_figuras() / f"fase6_{algoritmo}.png"
    fig.savefig(ruta, dpi=150, facecolor=SUPERFICIE)
    plt.close(fig)
    return ruta


def tablas_cocientes(resumen):
    """resultados/fase6_cocientes.md: tablas T/g por algoritmo, dimensión y medida (generadas, no editar)."""
    lineas = ["# Fase 6: tablas de cocientes observado/teórico", "",
              "Generado por `scripts/fase6_figuras.py` desde `resultados/fase6_validacion.json`; no se edita a mano.",
              "Como en las presentaciones del curso: si T = Θ(g), el cociente T/g queda entre dos constantes c₁ y c₂.",
              "El tiempo es de CPU con el oráculo sintético, no de GPU.", ""]
    for f in resumen:
        lineas += [f"## {TITULOS.get(f['algoritmo'], f['algoritmo'])}: {MEDIDAS.get(f['medida'], f['medida'])} "
                   f"frente a {f['etiqueta_tamano']}", "",
                   f"Modelo: {f['teoria']}; coeficientes {', '.join(f'{c:.4g}' for c in f['coeficientes'])}. "
                   f"Pendiente log-log: observada {f['pendiente_loglog_observada']:.3f}, ajuste "
                   f"{f['pendiente_loglog_ajuste']:.3f}, término dominante {f['pendiente_loglog_termino_dominante']:.3f}.", "",
                   "| tamaño | observado (media) | teórico ajustado | observado / ajustado | término dominante g | observado / g |",
                   "|---|---|---|---|---|---|"]
        for a, b in zip(f["cocientes_frente_al_ajuste"]["filas"], f["cocientes_frente_al_termino_dominante"]["filas"]):
            lineas.append(f"| {numero(a['tamano'])} | {a['observado']:.4g} | {a['teorico']:.4g} | {a['cociente']:.4f} "
                          f"| {b['teorico']:.4g} | {b['cociente']:.4g} |")
        c = f["cocientes_frente_al_ajuste"]
        lineas += ["", f"c₁ = {c['c1']:.4f}, c₂ = {c['c2']:.4f} (observado / ajustado).", ""]
    ruta = rutas.dir_resultados() / "fase6_cocientes.md"
    ruta.write_text("\n".join(lineas), encoding="utf-8")
    return ruta


def main():
    resumen = cargar_resultado("fase6_validacion")["datos"]["resumen"]
    for algoritmo in dict.fromkeys(f["algoritmo"] for f in resumen):
        print("→", figura(algoritmo, [f for f in resumen if f["algoritmo"] == algoritmo]))
    print("→", tablas_cocientes(resumen))


if __name__ == "__main__":
    main()
