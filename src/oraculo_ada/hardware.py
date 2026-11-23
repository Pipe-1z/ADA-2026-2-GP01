"""Identificación del hardware y etiqueta que separa los cachés (CLAUDE.md, regla 14)."""

import os
import platform
import re
import subprocess
import sys

ETIQUETA_T4 = "t4"


def _nombre_gpu():
    try:
        import torch
    except ImportError:
        return None
    if not torch.cuda.is_available():
        return None
    return torch.cuda.get_device_name(0)


def info_hardware():
    """Diccionario con el sistema, Python y, si hay GPU NVIDIA, sus datos."""
    info = {
        "python": platform.python_version(),
        "sistema": platform.platform(),
        "procesador": platform.processor() or platform.machine(),
        "colab": "COLAB_RELEASE_TAG" in os.environ or "google.colab" in sys.modules,
        "gpu": None,
    }
    try:
        import torch
    except ImportError:
        return info
    info["torch"] = torch.__version__
    info["cuda_torch"] = torch.version.cuda
    if torch.cuda.is_available():
        propiedades = torch.cuda.get_device_properties(0)
        info["gpu"] = torch.cuda.get_device_name(0)
        info["gpu_capacidad"] = f"{propiedades.major}.{propiedades.minor}"
        info["gpu_memoria_gb"] = round(propiedades.total_memory / 1e9, 2)
        try:
            info["driver"] = subprocess.run(
                ["nvidia-smi", "--query-gpu=driver_version", "--format=csv,noheader"],
                capture_output=True, text=True, check=True,
            ).stdout.strip()
        except Exception:  # noqa: BLE001 - dato informativo
            info["driver"] = None
    return info


def etiqueta_hardware(nombre_gpu=...):
    """Etiqueta corta del hardware: ``t4``, ``cpu`` o el nombre de la GPU normalizado.

    >>> etiqueta_hardware("Tesla T4")
    't4'
    >>> etiqueta_hardware("NVIDIA GeForce RTX 5050 Laptop GPU")
    'rtx-5050-laptop'
    >>> etiqueta_hardware(None)
    'cpu'
    """
    if nombre_gpu is ...:
        nombre_gpu = _nombre_gpu()
    if not nombre_gpu:
        return "cpu"
    if re.search(r"\bT4\b", nombre_gpu):
        return ETIQUETA_T4
    nombre = re.sub(r"(?i)\b(nvidia|geforce|gpu)\b", " ", nombre_gpu)
    return re.sub(r"[^a-z0-9]+", "-", nombre.lower()).strip("-")


def verificar_hardware(etiqueta, nombre_gpu=...):
    """Falla si la etiqueta pedida no corresponde al hardware real.

    Evita, por ejemplo, escribir salidas de la GPU local en el caché de la T4.
    """
    real = etiqueta_hardware(nombre_gpu)
    if etiqueta != real:
        raise RuntimeError(
            f"se pidió el caché de '{etiqueta}' pero el hardware es '{real}': "
            "las salidas de otro hardware van en su propio caché (CLAUDE.md, regla 14)"
        )
    return real
