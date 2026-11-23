"""Envoltura del oráculo del curso con la interfaz común.

Usa solo la interfaz pública de ``oraculo.py`` (CLAUDE.md, regla 12):
``Oraculo.evaluar``, ``Oraculo.validar``, ``espacio``, ``CATALOGO`` y
``TEMPERATURAS``. Las configuraciones se toman de ``espacio()``, como en el
notebook de búsqueda, para no construir nunca una configuración inválida.

**Contador de consultas.** El oráculo del curso tiene caché, pero su interfaz
no dice cuántas consultas de una evaluación fueron nuevas. Esta envoltura lleva
un **libro de consultas** propio en disco: para cada (configuración, semilla),
el conjunto de ids de instancia ya consultados. Una consulta es nueva si no está
en el libro. El libro va junto al caché del mismo hardware y debe mantenerse
sincronizado con él (los dos se guardan en la misma carpeta, en Drive si se
corre en Colab).

**Cachés por hardware** (regla 14): el caché de la T4 es ``cache_oraculo.json``;
el de cualquier otro hardware, ``cache_oraculo_<etiqueta>.json``. Lo mismo para
los libros (``libro_consultas_<etiqueta>.json``).
"""

import json
from pathlib import Path
from types import SimpleNamespace

from .. import rutas
from ..hardware import ETIQUETA_T4, etiqueta_hardware, verificar_hardware
from ..medicion import Cronometro
from .base import OraculoBase, Resultado


def ruta_cache_oraculo(etiqueta, directorio=None):
    """Caché del oráculo del curso para ese hardware (regla 14)."""
    directorio = Path(directorio) if directorio else rutas.dir_cache()
    nombre = "cache_oraculo.json" if etiqueta == ETIQUETA_T4 else f"cache_oraculo_{etiqueta}.json"
    return directorio / nombre


def ruta_libro_consultas(etiqueta, directorio=None):
    directorio = Path(directorio) if directorio else rutas.dir_cache()
    return directorio / f"libro_consultas_{etiqueta}.json"


class PresupuestoAgotado(RuntimeError):
    """Una evaluación superaría el tope de consultas nuevas autorizado."""


def registrar_primera_entrega(oraculo_real, ruta_registro, busqueda, config_validada=None, n_validacion=None):
    """Marca en el libro las consultas de la primera entrega, que ya están en el caché de la T4.

    Cada fila del registro (``resultados/registro_busqueda.csv``) se evaluó sobre todas las
    instancias de búsqueda con semilla 1; la configuración final se validó con
    ``validar(n=None)`` (``n_validacion`` instancias). Es idempotente.
    """
    import csv

    ids = [x["id"] for x in busqueda]
    with open(ruta_registro, encoding="utf-8") as f:
        for fila in csv.DictReader(f):
            config = oraculo_real.config([int(fila[r]) for r in oraculo_real.ranuras],
                                         temperatura=float(fila["temperatura"]))
            oraculo_real.registrar_consultas(config, ids, semilla=1)
    if config_validada is not None and n_validacion:
        clave = oraculo_real._clave_libro(config_validada, 1, prefijo="validar")
        oraculo_real._libro[clave] = {str(i) for i in range(n_validacion)}
        oraculo_real._guardar_libro()


class OraculoReal(OraculoBase):
    """Oráculo del curso con contador de consultas, cronómetro y libro de consultas.

    Parámetros
    ----------
    oraculo_curso : instancia de ``oraculo.Oraculo`` (o un objeto con la misma interfaz).
    instancias : conjunto por defecto de ``evaluar`` (la partición de búsqueda).
    hardware : etiqueta del hardware (``t4``, ``rtx-5050-laptop``, ...); se guarda en el libro.
    ruta_libro : archivo JSON del libro de consultas.
    catalogo, temperaturas, espacio_fn : por defecto, ``CATALOGO``, ``TEMPERATURAS`` y
        ``espacio`` de ``oraculo.py``; se pueden inyectar para las pruebas.
    """

    def __init__(self, oraculo_curso, instancias, *, hardware, ruta_libro, catalogo=None,
                 temperaturas=None, espacio_fn=None, limite_consultas_nuevas=None):
        if catalogo is None or temperaturas is None or espacio_fn is None:
            import oraculo as curso  # interfaz pública del oráculo del curso

            catalogo = curso.CATALOGO if catalogo is None else catalogo
            temperaturas = curso.TEMPERATURAS if temperaturas is None else temperaturas
            espacio_fn = curso.espacio if espacio_fn is None else espacio_fn
        ranuras = list(catalogo)
        super().__init__(ranuras, {r: range(len(catalogo[r])) for r in ranuras}, instancias, temperaturas)
        self.oraculo = oraculo_curso
        self.hardware = hardware
        self._oficiales = {self.clave(c): c for c in espacio_fn(tuple(self.temperaturas))}
        self.ruta_libro = Path(ruta_libro)
        self._libro = self._cargar_libro()
        # Tope de consultas nuevas para esta instancia del oráculo (None = sin tope). Si una
        # evaluación lo superaría, se lanza PresupuestoAgotado ANTES de consultar al modelo.
        self.limite_consultas_nuevas = limite_consultas_nuevas

    # ---- libro de consultas ----------------------------------------------

    def _cargar_libro(self):
        if not self.ruta_libro.exists():
            return {}
        datos = json.loads(self.ruta_libro.read_text(encoding="utf-8"))
        if datos.get("hardware") != self.hardware:
            raise RuntimeError(
                f"el libro {self.ruta_libro} es de '{datos.get('hardware')}', no de '{self.hardware}' (regla 14)"
            )
        return {k: set(v) for k, v in datos["consultas"].items()}

    def _guardar_libro(self):
        self.ruta_libro.parent.mkdir(parents=True, exist_ok=True)
        datos = {"hardware": self.hardware,
                 "consultas": {k: sorted(v) for k, v in sorted(self._libro.items())}}
        temporal = self.ruta_libro.with_suffix(".tmp")
        temporal.write_text(json.dumps(datos), encoding="utf-8")
        temporal.replace(self.ruta_libro)

    def _clave_libro(self, config, semilla, prefijo="evaluar"):
        return f"{prefijo}|{','.join(map(str, self.clave(config)))}|{semilla}"

    def registrar_consultas(self, config, ids, semilla=1):
        """Marca consultas como ya hechas (por ejemplo, las del registro de la primera entrega)."""
        self.validar_config(config)
        self._libro.setdefault(self._clave_libro(config, semilla), set()).update(str(i) for i in ids)
        self._guardar_libro()

    def consultas_hechas(self, config, semilla=1):
        return set(self._libro.get(self._clave_libro(config, semilla), set()))

    def total_registrado(self):
        """Número total de consultas anotadas en el libro (sirve para contar entre sesiones)."""
        return sum(len(v) for v in self._libro.values())

    # ---- consulta -----------------------------------------------------

    def oficial(self, config):
        """La configuración tal como la arma ``espacio()`` del curso."""
        self.validar_config(config)
        return self._oficiales[self.clave(config)]

    def _evaluar(self, config, instancias, semilla):
        ids = [str(x["id"]) for x in instancias]
        clave = self._clave_libro(config, semilla)
        vistas = self._libro.setdefault(clave, set())
        nuevas = sum(1 for i in ids if i not in vistas)
        if self.limite_consultas_nuevas is not None and self.consultas + nuevas > self.limite_consultas_nuevas:
            raise PresupuestoAgotado(
                f"la evaluación necesita {nuevas} consultas nuevas y ya se usaron {self.consultas} "
                f"de {self.limite_consultas_nuevas}")
        r = self.oraculo.evaluar(self.oficial(config), instancias, semilla=semilla)
        vistas.update(ids)
        self._guardar_libro()
        trazas = [{"id": t["id"], "violo": t["violo"], "salida": t.get("salida")} for t in r.trazas]
        return r.n - len(trazas), trazas, nuevas

    def validar(self, config, n=None, semilla=1):
        """``Oraculo.validar`` con conteo: la validación usa siempre las mismas n primeras instancias."""
        clave = self._clave_libro(config, semilla, prefijo="validar")
        previas = len(self._libro.get(clave, set()))
        with Cronometro() as reloj:
            r = self.oraculo.validar(self.oficial(config), n=n, semilla=semilla)
        nuevas = max(0, r.n - previas)
        self._libro[clave] = {str(i) for i in range(max(previas, r.n))}   # posiciones de la muestra fija
        self._guardar_libro()
        self.consultas += nuevas
        self.consultas_solicitadas += r.n
        self.evaluaciones += 1
        self.segundos += reloj.segundos
        self.historial.append({"config": dict(config), "semilla": semilla, "instancias": r.n, "validacion": True,
                               "aciertos": r.n - len(r.trazas), "consultas_nuevas": nuevas,
                               "segundos": reloj.segundos})
        trazas = [{"id": t["id"], "violo": t["violo"], "salida": t.get("salida")} for t in r.trazas]
        return Resultado(aciertos=r.n - len(trazas), n=r.n, trazas=trazas, consultas_nuevas=nuevas,
                         segundos=reloj.segundos)

    def costo_por_consulta(self):
        """Segundos por consulta nueva, contando solo evaluaciones sin consultas repetidas."""
        puras = [h for h in self.historial if h["consultas_nuevas"] == h["instancias"]]
        consultas = sum(h["consultas_nuevas"] for h in puras)
        return {"evaluaciones": len(puras), "consultas": consultas,
                "segundos": sum(h["segundos"] for h in puras),
                "segundos_por_consulta": (sum(h["segundos"] for h in puras) / consultas) if consultas else None}


class ConsultaFueraDeCache(RuntimeError):
    """El oráculo del curso necesitó generar una respuesta que no está en el caché."""


class _TokenizadorSinModelo:
    """Tokenizador de relleno para reproducir desde el caché, sin modelo ni GPU.

    Solo trae los atributos de configuración que se le asignan al construir el oráculo.
    Cualquier otro uso (es decir, cualquier intento de generar una respuesta nueva)
    detiene la reproducción con ``ConsultaFueraDeCache``.
    """

    pad_token = "<pad>"
    eos_token = "<eos>"
    chat_template = ""
    padding_side = "left"

    def __getattr__(self, nombre):            # solo se llama para atributos que no existen arriba
        raise ConsultaFueraDeCache("la consulta no está en el caché y se está reproduciendo sin modelo")

    def __call__(self, *args, **kwargs):
        raise ConsultaFueraDeCache("la consulta no está en el caché y se está reproduciendo sin modelo")


def oraculo_curso_desde_cache(ruta_cache, busqueda, validacion=None, nombre_modelo="Qwen/Qwen3-1.7B"):
    """``oraculo.Oraculo`` sin modelo que solo responde lo que ya está en ``ruta_cache``.

    ``nombre_modelo`` debe ser el nombre con que se generó el caché (entra en su
    clave). Una consulta ausente lanza ``ConsultaFueraDeCache``.
    """
    from oraculo import Oraculo

    sin_modelo = SimpleNamespace(red=None, tok=_TokenizadorSinModelo(), nombre=nombre_modelo)
    return Oraculo(sin_modelo, busqueda, validacion, cache=str(ruta_cache))


def crear_oraculo_real(hardware=None, *, modelo="qwen17b", directorio_cache=None, lote=16,
                       presupuesto=32_000_000, ruta_datos=None, limite_consultas_nuevas=None, modelo_cargado=None):
    """Carga el modelo y arma el oráculo del curso con el caché del hardware correcto.

    Devuelve ``(oraculo_real, busqueda, validacion)``. ``hardware`` por defecto es
    la etiqueta del hardware detectado; si se pide otra, falla (regla 14). Usa los
    mismos ``lote`` y ``presupuesto`` del notebook de búsqueda.
    """
    from ayudas import cargar_datos, cargar_modelo, dividir
    from oraculo import Oraculo

    etiqueta = hardware or etiqueta_hardware()
    verificar_hardware(etiqueta)
    ruta_cache = ruta_cache_oraculo(etiqueta, directorio_cache)
    busqueda, validacion = dividir(cargar_datos(str(ruta_datos or rutas.RAIZ / "datos_visibles.json")))
    curso = Oraculo(modelo_cargado or cargar_modelo(modelo), busqueda, validacion, cache=str(ruta_cache),
                    lote=lote, presupuesto=presupuesto)
    real = OraculoReal(curso, busqueda, hardware=etiqueta,
                       ruta_libro=ruta_libro_consultas(etiqueta, directorio_cache),
                       limite_consultas_nuevas=limite_consultas_nuevas)
    return real, busqueda, validacion
