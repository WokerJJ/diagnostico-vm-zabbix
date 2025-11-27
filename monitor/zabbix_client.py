import os
import json
import requests
from utils.config import ZABBIX_URL, ZABBIX_TOKEN, ZABBIX_HOSTNAME

class ZabbixClient:
    """
    Cliente para Zabbix API usando token tipo Bearer en el header.
    NO usa el campo 'auth' en el cuerpo (compatible con Zabbix 7.x).
    """

    def __init__(self, url: str, token: str):
        if not url or not token:
            raise ValueError("URL de Zabbix o token no configurados.")
        self.url = url
        self.token = token
        self._request_id = 0

    def _next_id(self) -> int:
        self._request_id += 1
        return self._request_id

    def _call_api(self, method: str, params: dict):
        headers = {
            "Content-Type": "application/json-rpc",
            "Authorization": f"Bearer {self.token}",
        }
        payload = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
            "id": self._next_id()
            # SIN "auth"
        }

        resp = requests.post(self.url, headers=headers, data=json.dumps(payload), timeout=10)
        resp.raise_for_status()
        data = resp.json()
        if "error" in data:
            raise RuntimeError(f"Error API Zabbix: {data['error']}")
        return data["result"]

    # --------- Alto nivel ---------

    def get_host_id(self, hostname: str) -> str:
        params = {
            "output": ["hostid", "host"],
            "filter": {"host": [hostname]},
        }
        result = self._call_api("host.get", params)
        if not result:
            raise ValueError(f"No se encontró host con nombre {hostname}")
        return result[0]["hostid"]

    def get_items_for_host(self, hostid: str, search_keys: list[str]) -> dict:
        params = {
            "output": ["itemid", "name", "key_"],
            "hostids": [hostid],
        }
        result = self._call_api("item.get", params)
        mapping: dict[str, str] = {}
        for item in result:
            for key_wanted in search_keys:
                if key_wanted in item["key_"]:
                    mapping[key_wanted] = item["itemid"]
        return mapping

    def get_last_history_value(self, itemid: str, value_type: int = 0) -> float:
        params = {
            "output": "extend",
            "history": value_type,
            "itemids": [itemid],
            "sortfield": "clock",
            "sortorder": "DESC",
            "limit": 1,
        }
        result = self._call_api("history.get", params)
        if not result:
            raise ValueError(f"Sin valores de history para item {itemid}")
        return float(result[0]["value"])

    def obtener_diagnostico_host(self, hostname: str) -> dict:
        hostid = self.get_host_id(hostname)

        search_keys = [
            "system.cpu.util",
            "vm.memory.util",
            "vfs.fs.dependent.size[C:,pused]",
            "vfs.fs.dependent.size[C:,free]",
            "system.uptime",
            "system.swap.pfree",
            'service.info["AnyDesk",state]',
            'service.info["AudioEndpointBuilder",state]',
        ]

        items = self.get_items_for_host(hostid, search_keys)

        diag = {
            "hostname": hostname,
            "hostid": hostid,
            "cpu_uso_pct": None,
            "ram_uso_pct": None,
            "disco_c_uso_pct": None,
            "disco_c_libre_bytes": None,
            "uptime_seg": None,
            "swap_pfree_pct": None,
            "servicios": {},  # nombre -> estado
        }

        if "system.cpu.util" in items:
            diag["cpu_uso_pct"] = self.get_last_history_value(
                items["system.cpu.util"], value_type=0
            )

        if "vm.memory.util" in items:
            diag["ram_uso_pct"] = self.get_last_history_value(
                items["vm.memory.util"], value_type=0
            )

        if "vfs.fs.dependent.size[C:,pused]" in items:
            diag["disco_c_uso_pct"] = self.get_last_history_value(
                items["vfs.fs.dependent.size[C:,pused]"], value_type=0
            )

        if "vfs.fs.dependent.size[C:,free]" in items:
            diag["disco_c_libre_bytes"] = self.get_last_history_value(
                items["vfs.fs.dependent.size[C:,free]"], value_type=3
            )

        if "system.uptime" in items:
            diag["uptime_seg"] = self.get_last_history_value(
                items["system.uptime"], value_type=3
            )

        if "system.swap.pfree" in items:
            diag["swap_pfree_pct"] = self.get_last_history_value(
                items["system.swap.pfree"], value_type=0
            )

        # Servicios críticos (Zabbix devuelve 0=stopped,1=running,... según value map) [web:150][web:261]
        servicios_clave = {
            'service.info["AnyDesk",state]': "AnyDesk",
            'service.info["AudioEndpointBuilder",state]': "AudioEndpointBuilder",
        }
        for key_zbx, nombre_serv in servicios_clave.items():
            if key_zbx in items:
                estado = self.get_last_history_value(items[key_zbx], value_type=3)
                diag["servicios"][nombre_serv] = int(estado)

        return diag

