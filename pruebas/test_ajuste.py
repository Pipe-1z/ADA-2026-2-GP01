"""Pruebas de las utilidades de ajuste de la Fase 6."""

import math

import pytest

from oraculo_ada.analisis.ajuste import ajustar_constante, pendiente_loglog, tabla_cocientes


def test_constante_exacta_si_T_es_proporcional():
    g = [10, 20, 40, 80]
    assert ajustar_constante([3 * v for v in g], g) == pytest.approx(3)


def test_pendientes_conocidas():
    x = [2, 4, 8, 16, 32]
    assert pendiente_loglog(x, [5 * v for v in x]) == pytest.approx(1)
    assert pendiente_loglog(x, [v * v for v in x]) == pytest.approx(2)
    assert pendiente_loglog(x, [7.0] * 5) == pytest.approx(0)
    assert pendiente_loglog(x, [v * math.log2(v) for v in x]) > 1


def test_tabla_de_cocientes():
    t = tabla_cocientes([1, 2, 3], [2, 4, 7], [1, 2, 3])
    assert [f["cociente"] for f in t["filas"]] == pytest.approx([2, 2, 7 / 3])
    assert t["c1"] == pytest.approx(2) and t["c2"] == pytest.approx(7 / 3)


def test_errores():
    with pytest.raises(ValueError):
        pendiente_loglog([1], [1])
    with pytest.raises(ValueError):
        pendiente_loglog([1, 2], [0, 1])
    with pytest.raises(ValueError):
        ajustar_constante([1], [0])


def test_combinacion_de_dos_bases():
    from oraculo_ada.analisis.ajuste import ajustar_combinacion

    x = [1, 2, 4, 8, 16]
    obs = [3 + 0.5 * v for v in x]
    a, b = ajustar_combinacion(obs, [[1] * 5, x])
    assert a == pytest.approx(3) and b == pytest.approx(0.5)
    # si la mejor combinación tendría un coeficiente negativo, se queda con una base sola
    a, b = ajustar_combinacion([v for v in x], [[1] * 5, [2 * v for v in x]])
    assert a == 0 and b == pytest.approx(0.5)
