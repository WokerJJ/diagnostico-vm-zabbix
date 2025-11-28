# monitor/reconocimiento.py
from monitor.red import medir_latencia
from monitor.historico import obtener_resumen
from .sistema_local import obtener_info_sistema_local
from .zabbix_client import ZabbixClient
from monitor.netdata_client import NetdataClient
from utils.config import ZABBIX_URL, ZABBIX_TOKEN, ZABBIX_HOSTNAME, HOST_RAM_GB, HOST_CPU_CORES, NETDATA_ENABLED


def calcular_recomendaciones_vm(info_local: dict) -> dict:
    """
    A partir de la RAM/CPU de la VM y los límites del host (configurados),
    devuelve un dict con lista de recomendaciones de capacidad.
    """
    recomendaciones = []
    ram_vm = info_local.get("ram_total_gb")
    cores_vm = info_local.get("cpu_cores_logicos")

    from utils.config import HOST_RAM_GB, HOST_CPU_CORES

    if HOST_RAM_GB and ram_vm:
        ram_max_segura = HOST_RAM_GB * 0.8  # 80% del host
        if ram_vm < ram_max_segura:
            recomendaciones.append(
                f"Puede aumentar la RAM de la VM hasta ~{ram_max_segura:.1f} GB "
                f"sin exceder el 80% de la RAM del host ({HOST_RAM_GB} GB)."
            )

    if HOST_CPU_CORES and cores_vm:
        cores_max_seguro = int(HOST_CPU_CORES * 0.75)
        if cores_vm < cores_max_seguro:
            recomendaciones.append(
                f"Puede aumentar los vCPU de la VM hasta ~{cores_max_seguro} cores "
                f"sin sobreasignar CPU respecto al host ({HOST_CPU_CORES} cores)."
            )

    return {
        "recomendaciones_capacidad": recomendaciones
    }

def calcular_estado_global(diag_zbx: dict) -> dict:
    """
    Devuelve un dict con:
    - estado_global: "OK" | "ADVERTENCIA" | "CRÍTICO"
    - motivos: lista de strings explicando por qué.
    """
    motivos = []
    peor = "OK"

    def degradar(actual, nuevo):
        orden = ["OK", "ADVERTENCIA", "CRÍTICO"]
        return nuevo if orden.index(nuevo) > orden.index(actual) else actual

    cpu = diag_zbx.get("cpu_uso_pct")
    if cpu is not None:
        if cpu >= 95:
            peor = degradar(peor, "CRÍTICO")
            motivos.append(f"CPU al {cpu:.1f}% (≥95%).")
        elif cpu >= 80:
            peor = degradar(peor, "ADVERTENCIA")
            motivos.append(f"CPU al {cpu:.1f}% (≥80%).")

    ram = diag_zbx.get("ram_uso_pct")
    if ram is not None:
        if ram >= 95:
            peor = degradar(peor, "CRÍTICO")
            motivos.append(f"RAM al {ram:.1f}% (≥95%).")
        elif ram >= 80:
            peor = degradar(peor, "ADVERTENCIA")
            motivos.append(f"RAM al {ram:.1f}% (≥80%).")

    disco = diag_zbx.get("disco_c_uso_pct")
    if disco is not None:
        if disco >= 95:
            peor = degradar(peor, "CRÍTICO")
            motivos.append(f"Disco C: al {disco:.1f}% (≥95%).")
        elif disco >= 80:
            peor = degradar(peor, "ADVERTENCIA")
            motivos.append(f"Disco C: al {disco:.1f}% (≥80%).")

    swap_pfree = diag_zbx.get("swap_pfree_pct")
    if swap_pfree is not None:
        if swap_pfree <= 5:
            peor = degradar(peor, "CRÍTICO")
            motivos.append(f"Swap libre solo {swap_pfree:.1f}% (≤5%).")
        elif swap_pfree <= 20:
            peor = degradar(peor, "ADVERTENCIA")
            motivos.append(f"Swap libre baja: {swap_pfree:.1f}% (≤20%).")

    servicios = diag_zbx.get("servicios", {})
    for nombre, estado in servicios.items():
        if estado != 1:  # 1 = running en value map típico [web:150][web:261]
            peor = degradar(peor, "ADVERTENCIA")
            motivos.append(f"Servicio {nombre} no está en ejecución (estado={estado}).")

    return {
        "estado_global": peor,
        "motivos_estado": motivos,
    }


def reconocimiento_inicial() -> dict:
    """
    - Lee hardware local (VM/físico, CPU, RAM, disco).
    - Pide diagnóstico a Zabbix para WIN-LAPTOP.
    - Añade recomendaciones de capacidad para la VM.
    """
    info_local = obtener_info_sistema_local()
    zbx_client = ZabbixClient(ZABBIX_URL, ZABBIX_TOKEN)
    diag_zbx = zbx_client.obtener_diagnostico_host(ZABBIX_HOSTNAME)
    rec_vm = calcular_recomendaciones_vm(info_local)
    estado = calcular_estado_global(diag_zbx)

    lat_zbx = medir_latencia("192.168.1.9")  # IP del Zabbix server o gateway
    info_red = {"latencia_zabbix_ms": lat_zbx}
    resumen = obtener_resumen(20)

    netdata_info = {}
    if NETDATA_ENABLED:
        nd = NetdataClient()
        cpu_nd = nd.get_cpu_avg_last_minute()
        load_nd = nd.get_load_avg()
        ram_nd = nd.get_ram_used_pct()
        netdata_info = {
            "cpu_avg_60s": cpu_nd,
            "load_avg_1m": load_nd,
            "ram_uso_pct": ram_nd,
        }

    return {
         "sistema_local": info_local,
        "zabbix": diag_zbx,
        "recomendaciones": rec_vm["recomendaciones_capacidad"],
        "estado_global": estado["estado_global"],
        "motivos_estado": estado["motivos_estado"],
        "red": info_red,
        "resumen": resumen,
        "netdata": netdata_info,
    }

