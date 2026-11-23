"""Fase 5: figuras generadas desde resultados/ (nunca se editan a mano).

- figuras/fase5_reparto_<conjunto>.png: probabilidad de elegir la mejor y simple regret frente a
  B/|S| para uniforme, Successive Halving y UCB1, por variante (media de los casos).
- figuras/fase5_estrategias.png: precisión media frente al presupuesto para las estrategias de
  mejora, por variante.

Paleta categórica validada con scripts/validate_palette.js (dataviz): azul, naranja, aqua en
orden fijo; cada serie lleva además un marcador distinto (codificación secundaria).
"""

import json

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from oraculo_ada import rutas
from oraculo_ada.registro import cargar_resultado

SUPERFICIE, TEXTO, TEXTO2, REJILLA = "#fcfcfb", "#0b0b0b", "#52514e", "#e4e3df"
CATEGORICA = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6", "#e34948"]
MARCADORES = ["o", "s", "^", "D", "v", "P", "X", "*"]
VARIANTES = {"calibrado_24": "Calibrado (techo 24 %)", "calibrado_28": "Calibrado (techo 28 %)",
             "disyuntivo": "Disyuntivo (3-SAT generalizado)", "sin_limpias": "Sin opciones limpias"}
ESQUEMAS = {"uniforme": "Uniforme", "successive_halving": "Successive Halving", "ucb1": "UCB1"}


def estilo(ax):
    ax.set_facecolor(SUPERFICIE)
    for lado in ("top", "right"):
        ax.spines[lado].set_visible(False)
    for lado in ("left", "bottom"):
        ax.spines[lado].set_color(REJILLA)
    ax.tick_params(colors=TEXTO2, labelsize=8)
    ax.grid(True, color=REJILLA, linewidth=0.6)
    ax.set_axisbelow(True)


def figura_reparto(conjunto):
    datos = cargar_resultado("fase5_reparto")["datos"]["resumen"]
    fig, ejes = plt.subplots(2, 4, figsize=(13, 6.2), sharex=True, facecolor=SUPERFICIE)
    for col, (var, titulo) in enumerate(VARIANTES.items()):
        bloque = datos.get(f"{var}|{conjunto}", {})
        for fila, (metrica, etiqueta) in enumerate((("prob_elegir_mejor", "P(elegir la mejor)"),
                                                    ("regret_medio", "Simple regret medio"))):
            ax = ejes[fila][col]
            estilo(ax)
            for j, (esq, nombre) in enumerate(ESQUEMAS.items()):
                por_b = bloque.get(esq, {})
                bs = sorted(int(b) for b in por_b)
                if not bs:
                    continue
                ys = [por_b[str(b)][metrica]["media"] for b in bs]
                ax.plot(bs, ys, color=CATEGORICA[j], marker=MARCADORES[j], markersize=5, linewidth=2, label=nombre)
            ax.set_xscale("log", base=2)
            if fila == 0:
                ax.set_title(titulo, fontsize=10, color=TEXTO)
                ax.set_ylim(0, 1.02)
            if col == 0:
                ax.set_ylabel(etiqueta, fontsize=9, color=TEXTO)
            if fila == 1:
                ax.set_xlabel("Presupuesto B / |S|", fontsize=9, color=TEXTO)
    manejadores, etiquetas = ejes[0][0].get_legend_handles_labels()
    fig.legend(manejadores, etiquetas, loc="upper center", ncol=3, frameon=False, fontsize=9)
    tamano = "128 configuraciones al azar" if conjunto == "muestra_128" else "vecindario doble (490 configuraciones)"
    fig.suptitle(f"Algoritmo 4: reparto del presupuesto sobre {tamano}", fontsize=11, color=TEXTO, y=0.995)
    fig.tight_layout(rect=(0, 0, 1, 0.93))
    ruta = rutas.dir_figuras() / f"fase5_reparto_{conjunto}.png"
    fig.savefig(ruta, dpi=160, facecolor=SUPERFICIE)
    plt.close(fig)
    return ruta


def figura_estrategias():
    datos = cargar_resultado("fase5_estrategias")["datos"]
    resumen = datos["resumen"]
    nombres = ["original", "dos_ranuras", "reinicios", "dos_ranuras_sh_n2_r1", "dos_ranuras_sh_n4_r1",
               "dos_ranuras_sh_n8_r1", "dos_ranuras_sh_n8_r2"]
    rotulos = {"original": "Original", "dos_ranuras": "Dos ranuras (2b)", "reinicios": "Reinicios (hasta 20)",
               "dos_ranuras_sh_n2_r1": "Dos ranuras + SH, n₀=2, 1 ronda",
               "dos_ranuras_sh_n4_r1": "Dos ranuras + SH, n₀=4, 1 ronda",
               "dos_ranuras_sh_n8_r1": "Dos ranuras + SH, n₀=8, 1 ronda",
               "dos_ranuras_sh_n8_r2": "Dos ranuras + SH, n₀=8, 2 rondas"}
    fig, ejes = plt.subplots(1, 4, figsize=(14, 4.2), facecolor=SUPERFICIE)
    for col, (var, titulo) in enumerate(VARIANTES.items()):
        ax = ejes[col]
        estilo(ax)
        for j, nombre in enumerate(nombres):
            por_b = resumen[var][nombre]["por_presupuesto"]
            bs = sorted(int(b) for b in por_b)
            ys = [por_b[str(b)]["precision"]["media"] for b in bs]
            ax.plot([b / 1000 for b in bs], ys, color=CATEGORICA[j], marker=MARCADORES[j], markersize=5,
                    linewidth=2, label=rotulos[nombre])
        ax.set_title(titulo, fontsize=10, color=TEXTO)
        ax.set_xlabel("Presupuesto (miles de consultas)", fontsize=9, color=TEXTO)
        if col == 0:
            ax.set_ylabel("Precisión media alcanzada", fontsize=9, color=TEXTO)
    manejadores, etiquetas = ejes[0].get_legend_handles_labels()
    fig.legend(manejadores, etiquetas, loc="upper center", ncol=4, frameon=False, fontsize=8.5)
    fig.suptitle("Estrategias de mejora con el mismo presupuesto", fontsize=11, color=TEXTO, y=0.995)
    fig.tight_layout(rect=(0, 0, 1, 0.84))
    ruta = rutas.dir_figuras() / "fase5_estrategias.png"
    fig.savefig(ruta, dpi=160, facecolor=SUPERFICIE)
    plt.close(fig)
    return ruta


if __name__ == "__main__":
    for conjunto in ("muestra_128", "vecindario_doble"):
        print("→", figura_reparto(conjunto))
    print("→", figura_estrategias())
