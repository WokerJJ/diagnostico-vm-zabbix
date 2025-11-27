from pythonping import ping

def medir_latencia(host: str, count: int = 4, timeout: int = 1) -> float | None:
    """
    Devuelve latencia media en ms al host dado, o None si no responde.
    """
    try:
        resp = ping(host, count=count, timeout=timeout, verbose=False)
        if resp.success():
            return resp.rtt_avg_ms
        return None
    except Exception:
        return None
