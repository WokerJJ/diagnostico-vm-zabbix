import platform
import socket
import psutil
from cpuinfo import get_cpu_info  # py-cpuinfo

def detectar_vm() -> bool:
    info = platform.uname()
    texto = (info.system + " " + info.node + " " + info.release + " " +
             info.version + " " + info.machine).lower()
    pistas_vm = ["virtualbox", "vmware", "kvm", "hyper-v"]
    return any(tag in texto for tag in pistas_vm)

def obtener_info_sistema_local() -> dict:
    cpu_info = get_cpu_info() or {}
    cpu_model = cpu_info.get("brand_raw") or cpu_info.get("brand") or "Desconocido"
    cpu_freq_friendly = cpu_info.get("hz_advertised_friendly") or ""
    hz_actual = cpu_info.get("hz_actual")
    cpu_hz = cpu_info.get("hz_advertised_friendly") or ""

    if hz_actual and isinstance(hz_actual, (tuple, list)) and hz_actual[0]:
        ghz_actual = hz_actual[0] / 1_000_000_000
    else:
        ghz_actual = None

    cores_log = psutil.cpu_count(logical=True)
    cores_fis = psutil.cpu_count(logical=False)

    vm = psutil.virtual_memory()
    ram_total_gb = vm.total / (1024 ** 3)

    discos = [d for d in psutil.disk_partitions(all=False) if d.fstype]
    disco_principal = discos[0].mountpoint if discos else "/"
    disco_total_bytes = psutil.disk_usage(disco_principal).total

    info = {
        "hostname": socket.gethostname(),
        "so": platform.system(),
        "so_version": platform.version(),
        "release": platform.release(),
        "arquitectura": platform.machine(),
        "es_vm": detectar_vm(),
        "cpu_modelo": cpu_model,
        "cpu_freq_anunciada": cpu_freq_friendly,
        "cpu_freq_actual_ghz": ghz_actual,
        "cpu_cores_logicos": cores_log,
        "cpu_cores_fisicos": cores_fis,
        "ram_total_bytes": vm.total,
        "ram_total_gb": round(ram_total_gb, 2),
        "disco_principal": disco_principal,
        "disco_total_bytes": disco_total_bytes,
    }

    # Aquí más adelante puedes rellenar campos derivados, por ejemplo:
    # info["ram_max_recomendada_vm_gb"] = calcular_max_ram_vm(info)
    return info
