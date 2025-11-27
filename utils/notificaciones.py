"""
Sistema de notificaciones centralizado para la app de diagnóstico.
Tipos: INFO, ADVERTENCIA, ERROR.
Las notificaciones se pueden enviar a:
- Consola (fallback)
- Callback de GUI (para mostrarlas en un Text o panel dedicado).
"""

from datetime import datetime
from typing import Callable, Optional

# Callback global que la GUI registrará.
_gui_callback: Optional[Callable[[str, str], None]] = None


def registrar_callback_gui(func: Callable[[str, str], None]) -> None:
    """
    Registra una función de la GUI que recibirá las notificaciones.
    La firma debe ser: func(tipo: str, mensaje: str).
    """
    global _gui_callback
    _gui_callback = func


def _emitir(tipo: str, mensaje: str) -> None:
    """
    Emite una notificación a la GUI (si hay callback) y a consola.
    tipo: "INFO", "WARN", "ERROR".
    """
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    linea = f"[{ts}] [{tipo}] {mensaje}"

    # Consola (siempre)
    print(linea)

    # GUI, si está registrada
    if _gui_callback is not None:
        try:
            _gui_callback(tipo, linea)
        except Exception as e:
            # No romper la app por un fallo visual
            print(f"[{ts}] [ERROR] Error enviando notificación a GUI: {e}")


def info(mensaje: str) -> None:
    _emitir("INFO", mensaje)


def advertencia(mensaje: str) -> None:
    _emitir("WARN", mensaje)


def error(mensaje: str) -> None:
    _emitir("ERROR", mensaje)
