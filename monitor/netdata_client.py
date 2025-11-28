import requests
from typing import Optional, Dict, Any

from utils.config import NETDATA_URL, NETDATA_ENABLED


class NetdataClient:
    """
    Cliente mínimo para leer métricas básicas desde Netdata.
    Solo se usa si NETDATA_ENABLED=true.
    """

    def __init__(self, base_url: str = NETDATA_URL):
        self.base_url = base_url.rstrip("/")

    def _get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        if not NETDATA_ENABLED:
            return None
        url = f"{self.base_url}{path}"
        try:
            resp = requests.get(url, params=params, timeout=5)
            resp.raise_for_status()
            return resp.json()
        except Exception:
            return None

    def get_cpu_avg_last_minute(self) -> Optional[float]:
        """
        CPU total media del último minuto usando el chart 'system.cpu'.
        Toma la suma de las dimensiones y la normaliza a 0–100 %.
        """
        params = {
            "chart": "system.cpu",
            "format": "json",
            "points": 1,
            "group": "average",
            "after": -60,
            "options": "absolute",
        }
        data = self._get("/api/v1/data", params=params)
        if not data or "data" not in data or not data["data"]:
            return None

        # row = [timestamp, user, system, nice, ... idle]
        row = data["data"][0]
        if len(row) < 3:
            return None

        # ignoramos timestamp (row[0]) y calculamos porcentaje de uso como
        # 100 - idle, asumiendo que la última dimensión es idle.
        values = row[1:]
        idle = values[-1]
        # algunos setups devuelven idle como fracción 0–1; otros ya en 0–100
        if idle <= 1.0:
            idle_pct = idle * 100.0
        else:
            idle_pct = idle
        uso = max(0.0, min(100.0, 100.0 - idle_pct))
        return uso



    def get_load_avg(self) -> Optional[float]:
        """
        Load average 1m desde chart system.load.
        """
        params = {
            "chart": "system.load",
            "format": "json",
            "points": 1,
            "group": "average",
            "after": -60,
            "options": "absolute",
        }
        data = self._get("/api/v1/data", params=params)
        if not data or "data" not in data or not data["data"]:
            return None
        row = data["data"][0]
        if len(row) < 2:
            return None
        return float(row[1])

    def get_ram_used_pct(self) -> Optional[float]:
        """
        Porcentaje de RAM usada usando el chart 'system.ram'.
        Se normaliza y se recorta a 0–100 % para evitar valores raros.
        """
        params = {
            "chart": "system.ram",
            "format": "json",
            "points": 1,
            "group": "average",
            "after": -60,
            "options": "percentage-of-average",
        }
        data = self._get("/api/v1/data", params=params)
        if not data or "data" not in data or not data["data"]:
            return None

        row = data["data"][0]
        if len(row) < 2:
            return None

        used_pct = float(row[1])

        # Si viene muy pasado, lo normalizamos y recortamos.
        if used_pct > 1000 or used_pct < 0:
            return None  # mejor no mostrar dato
        if used_pct > 100:
            used_pct = 100.0

        return used_pct

