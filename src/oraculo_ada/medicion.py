"""Medición de tiempo de pared."""

import time


class Cronometro:
    """Cronómetro de pared con ``time.perf_counter``.

    >>> with Cronometro() as c:
    ...     _ = sum(range(1000))
    >>> c.segundos >= 0
    True
    """

    def __init__(self):
        self.inicio = None
        self.segundos = 0.0

    def __enter__(self):
        self.inicio = time.perf_counter()
        return self

    def __exit__(self, *exc):
        self.segundos = time.perf_counter() - self.inicio
        return False
