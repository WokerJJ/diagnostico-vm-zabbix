"""
Exportación de diagnósticos a CSV y preparación para PDF.
@author: Woker
"""

import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

def _timestamp_iso() -> str:
    """Devuelve timestamp en formato ISO para nombres de archivo."""
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def exportar_diagnostico_csv(diag: Dict[str, Any], ruta_salida: str = None) -> str:
    """
    Exporta un diagnóstico (dict) a CSV.
    Formato: una fila por métrica con columnas: métrica, valor, unidad, estado, recomendación.
    
    Args:
        diag: dict con estructura {"sistema_local": {...}, "zabbix": {...}, ...}
        ruta_salida: ruta donde guardar el archivo (por defecto, ./reportes/diag_TIMESTAMP.csv)
    
    Returns:
        Ruta completa del archivo creado.
    """
    if ruta_salida is None:
        Path("reportes").mkdir(exist_ok=True)
        ruta_salida = f"reportes/diagnostico_{_timestamp_iso()}.csv"

    filas = []

    # Encabezado
    filas.append(["SECCIÓN", "MÉTRICA", "VALOR", "UNIDAD", "ESTADO", "RECOMENDACIÓN"])

    # Sección: Sistema Local
    if "sistema_local" in diag:
        info = diag["sistema_local"]
        filas.append(["SISTEMA LOCAL", "Hostname", info.get("hostname", "-"), "", "OK", ""])
        filas.append(["SISTEMA LOCAL", "SO", info.get("so", "-"), "", "OK", ""])
        filas.append(["SISTEMA LOCAL", "Versión SO", info.get("so_version", "-"), "", "OK", ""])
        filas.append(["SISTEMA LOCAL", "Arquitectura", info.get("arquitectura", "-"), "", "OK", ""])
        
        es_vm = info.get("es_vm", False)
        tipo = "Máquina Virtual" if es_vm else "Sistema Físico"
        filas.append(["SISTEMA LOCAL", "Tipo de sistema", tipo, "", "OK", ""])

        cores_l = info.get("cpu_cores_logicos", "-")
        filas.append(["SISTEMA LOCAL", "CPUs (lógicos)", cores_l, "núcleos", "OK", ""])

        cores_f = info.get("cpu_cores_fisicos", "-")
        filas.append(["SISTEMA LOCAL", "CPUs (físicos)", cores_f, "núcleos", "OK", ""])

        ram_total = info.get("ram_total_bytes", 0)
        if ram_total > 0:
            ram_gb = ram_total / (1024 ** 3)
            filas.append(["SISTEMA LOCAL", "RAM Total", f"{ram_gb:.2f}", "GB", "OK", ""])

    # Sección: Zabbix
    if "zabbix" in diag:
        zbx = diag["zabbix"]
        filas.append(["ZABBIX", "Hostname Monitorizado", zbx.get("hostname", "-"), "", "OK", ""])

        cpu = zbx.get("cpu_uso_pct")
        if cpu is not None:
            estado_cpu = "OK" if cpu < 80 else "ADVERTENCIA" if cpu < 95 else "CRÍTICO"
            rec_cpu = "" if cpu < 80 else "Revisar procesos de alto consumo."
            filas.append(["ZABBIX", "CPU Uso", f"{cpu:.1f}", "%", estado_cpu, rec_cpu])

        ram = zbx.get("ram_uso_pct")
        if ram is not None:
            estado_ram = "OK" if ram < 80 else "ADVERTENCIA" if ram < 95 else "CRÍTICO"
            rec_ram = "" if ram < 80 else "Considerar aumentar RAM o liberar recursos."
            filas.append(["ZABBIX", "RAM Uso", f"{ram:.1f}", "%", estado_ram, rec_ram])

        disco = zbx.get("disco_c_uso_pct")
        if disco is not None:
            estado_disco = "OK" if disco < 80 else "ADVERTENCIA" if disco < 95 else "CRÍTICO"
            rec_disco = "" if disco < 80 else "Liberar espacio en disco o expandir partición."
            filas.append(["ZABBIX", "Disco C: Uso", f"{disco:.1f}", "%", estado_disco, rec_disco])

        disco_libre = zbx.get("disco_c_libre_bytes")
        if disco_libre is not None:
            disco_libre_gb = disco_libre / (1024 ** 3)
            filas.append(["ZABBIX", "Disco C: Espacio Libre", f"{disco_libre_gb:.2f}", "GB", "OK", ""])

        # Uptime
        up = zbx.get("uptime_seg")
        if up is not None:
            horas = up / 3600
            filas.append(["ZABBIX", "Uptime", f"{horas:.1f}", "horas", "OK", ""])

        # Swap
        swap_pfree = zbx.get("swap_pfree_pct")
        if swap_pfree is not None:
            estado_swap = "OK" if swap_pfree > 20 else "ADVERTENCIA"
            rec_swap = "" if swap_pfree > 20 else "Revisar uso de swap, posible falta de RAM."
            filas.append(["ZABBIX", "Swap libre", f"{swap_pfree:.1f}", "%", estado_swap, rec_swap])

        # Servicios críticos
        servicios = zbx.get("servicios", {})
        for nombre, estado in servicios.items():
            if estado == 1:
                estado_txt = "En ejecución"
                rec_serv = ""
            elif estado == 0:
                estado_txt = "Detenido"
                rec_serv = "Verificar si el servicio debe estar activo para la operación normal."
            else:
                estado_txt = f"Estado={estado}"
                rec_serv = "Revisar configuración del servicio en el sistema operativo."

            filas.append(
                ["ZABBIX", f"Servicio {nombre}", estado_txt, "", "OK", rec_serv]
            )


    # Sección: Recomendaciones de capacidad (VM vs host)
    recs = diag.get("recomendaciones", [])
    if recs:
        for rec in recs:
            filas.append(["RECOMENDACIONES", "Capacidad VM/Host", rec, "", "", ""])

    estado_global = diag.get("estado_global", "OK")
    motivos_estado = diag.get("motivos_estado", [])

    filas.append(["RESUMEN", "Estado global", estado_global, "", estado_global, ""])

    for m in motivos_estado:
        filas.append(["RESUMEN", "Motivo estado", m, "", "", ""])

    # Sección: Alertas simuladas (zona de pruebas)
    alertas_sim = diag.get("alertas_simuladas", [])
    if alertas_sim:
        for a in alertas_sim:
            filas.append(["ALERTAS_SIMULADAS", "Escenario de prueba", a, "", "", ""])

    # Guardar CSV
    Path(ruta_salida).parent.mkdir(parents=True, exist_ok=True)
    with open(ruta_salida, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(filas)

    return ruta_salida


def generar_html_diagnostico(diag: Dict[str, Any], titulo: str = "Diagnóstico del Sistema") -> str:
    """
    Genera un HTML básico con el diagnóstico.
    Pensado para ser convertido a PDF después.
    
    Args:
        diag: dict con estructura {"sistema_local": {...}, "zabbix": {...}, ...}
        titulo: título del reporte
    
    Returns:
        String con HTML.
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    html = f"""
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{titulo}</title>
    <style>
        body {{
            font-family: "Segoe UI", Tahoma, Geneva, Verdana, sans-serif;
            background: #f5f5f5;
            margin: 20px;
            padding: 0;
        }}
        .container {{
            max-width: 900px;
            margin: 0 auto;
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #333;
            text-align: center;
            border-bottom: 3px solid #0066cc;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #0066cc;
            margin-top: 20px;
            border-left: 4px solid #0066cc;
            padding-left: 10px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 15px 0;
        }}
        th {{
            background: #0066cc;
            color: white;
            padding: 10px;
            text-align: left;
        }}
        td {{
            padding: 8px;
            border-bottom: 1px solid #ddd;
        }}
        tr:nth-child(even) {{
            background: #f9f9f9;
        }}
        .status-ok {{
            color: green;
            font-weight: bold;
        }}
        .status-warn {{
            color: orange;
            font-weight: bold;
        }}
        .status-error {{
            color: red;
            font-weight: bold;
        }}
        .footer {{
            margin-top: 30px;
            text-align: center;
            color: #999;
            font-size: 12px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>{titulo}</h1>
        <p style="text-align: center; color: #666;">Generado: {timestamp}</p>
"""

    # Sección: Sistema Local
    if "sistema_local" in diag:
        info = diag["sistema_local"]
        html += """
        <h2>Sistema Local</h2>
        <table>
            <tr>
                <th>Parámetro</th>
                <th>Valor</th>
            </tr>
"""
        html += f"<tr><td>Hostname</td><td>{info.get('hostname', '-')}</td></tr>\n"
        html += f"<tr><td>Sistema Operativo</td><td>{info.get('so', '-')} {info.get('release', '')}</td></tr>\n"
        html += f"<tr><td>Arquitectura</td><td>{info.get('arquitectura', '-')}</td></tr>\n"
        
        es_vm = info.get("es_vm", False)
        tipo = "Máquina Virtual" if es_vm else "Sistema Físico"
        html += f"<tr><td>Tipo de Sistema</td><td>{tipo}</td></tr>\n"
        
        html += f"<tr><td>CPUs (lógicos)</td><td>{info.get('cpu_cores_logicos', '-')}</td></tr>\n"
        html += f"<tr><td>CPUs (físicos)</td><td>{info.get('cpu_cores_fisicos', '-')}</td></tr>\n"
        
        ram_total = info.get("ram_total_bytes", 0)
        if ram_total > 0:
            ram_gb = ram_total / (1024 ** 3)
            html += f"<tr><td>RAM Total</td><td>{ram_gb:.2f} GB</td></tr>\n"
        
        html += """
        </table>
"""

    # Sección: Zabbix
    if "zabbix" in diag:
        zbx = diag["zabbix"]

        estado_global = diag.get("estado_global", "OK")
        motivos_estado = diag.get("motivos_estado", [])

        clase_estado = "status-ok" if estado_global == "OK" else \
                       "status-warn" if estado_global == "ADVERTENCIA" else \
                       "status-error"

        html += f"""
        <h2>Monitoreo desde Zabbix</h2>
        <p><strong>Estado global:</strong> <span class="{clase_estado}">{estado_global}</span></p>
"""

        if motivos_estado:
            html += "<ul>\n"
            for m in motivos_estado:
                html += f"<li>{m}</li>\n"
            html += "</ul>\n"

        html += """
        <table>
            <tr>
                <th>Métrica</th>
                <th>Valor</th>
                <th>Estado</th>
                <th>Recomendación</th>
            </tr>
"""

        cpu = zbx.get("cpu_uso_pct")
        if cpu is not None:
            estado_cpu = "OK" if cpu < 80 else "ADVERTENCIA" if cpu < 95 else "CRÍTICO"
            clase = "status-ok" if cpu < 80 else "status-warn" if cpu < 95 else "status-error"
            rec_cpu = "" if cpu < 80 else "Revisar procesos de alto consumo."
            html += f"<tr><td>Uso de CPU</td><td>{cpu:.1f} %</td><td class='{clase}'>{estado_cpu}</td><td>{rec_cpu}</td></tr>\n"

        ram = zbx.get("ram_uso_pct")
        if ram is not None:
            estado_ram = "OK" if ram < 80 else "ADVERTENCIA" if ram < 95 else "CRÍTICO"
            clase = "status-ok" if ram < 80 else "status-warn" if ram < 95 else "status-error"
            rec_ram = "" if ram < 80 else "Considerar aumentar RAM o liberar recursos."
            html += f"<tr><td>Uso de RAM</td><td>{ram:.1f} %</td><td class='{clase}'>{estado_ram}</td><td>{rec_ram}</td></tr>\n"

        disco = zbx.get("disco_c_uso_pct")
        if disco is not None:
            estado_disco = "OK" if disco < 80 else "ADVERTENCIA" if disco < 95 else "CRÍTICO"
            clase = "status-ok" if disco < 80 else "status-warn" if disco < 95 else "status-error"
            rec_disco = "" if disco < 80 else "Liberar espacio en disco o expandir partición."
            html += f"<tr><td>Uso Disco C:</td><td>{disco:.1f} %</td><td class='{clase}'>{estado_disco}</td><td>{rec_disco}</td></tr>\n"

        disco_libre = zbx.get("disco_c_libre_bytes")
        if disco_libre is not None:
            disco_libre_gb = disco_libre / (1024 ** 3)
            html += f"<tr><td>Espacio Libre C:</td><td>{disco_libre_gb:.2f} GB</td><td class='status-ok'>OK</td><td></td></tr>\n"

        up = zbx.get("uptime_seg")
        if up is not None:
            horas = up / 3600
            html += f"<tr><td>Uptime</td><td>{horas:.1f} h</td><td class='status-ok'>OK</td><td></td></tr>\n"

        swap_pfree = zbx.get("swap_pfree_pct")
        if swap_pfree is not None:
            estado_swap = "OK" if swap_pfree > 20 else "ADVERTENCIA"
            clase = "status-ok" if swap_pfree > 20 else "status-warn"
            rec_swap = "" if swap_pfree > 20 else "Revisar uso de swap y carga de memoria."
            html += f"<tr><td>Swap libre</td><td>{swap_pfree:.1f} %</td><td class='{clase}'>{estado_swap}</td><td>{rec_swap}</td></tr>\n"

        # Servicios críticos (incluye AnyDesk con texto legible)
        servicios = zbx.get("servicios", {})
        for nombre, estado in servicios.items():
            if estado == 1:
                estado_txt = "En ejecución"
                clase_serv = "status-ok"
                rec_serv = ""
            elif estado == 0:
                estado_txt = "Detenido"
                clase_serv = "status-warn"
                rec_serv = "Verificar si este servicio debe estar activo."
            else:
                estado_txt = f"Estado={estado}"
                clase_serv = "status-warn"
                rec_serv = "Revisar configuración del servicio en el sistema operativo."

            html += (
                f"<tr><td>Servicio {nombre}</td>"
                f"<td>{estado_txt}</td>"
                f"<td class='{clase_serv}'>OK</td>"
                f"<td>{rec_serv}</td></tr>\n"
            )

        html += """
        </table>
"""

    # Sección: Red
    info_red = diag.get("red", {})
    lat = info_red.get("latencia_zabbix_ms")
    if lat is not None:
        html += f"""
        <h2>Diagnóstico de red</h2>
        <p>Latencia media desde la VM hasta el servidor Zabbix: <strong>{lat:.1f} ms</strong>.</p>
"""
    netdata = diag.get("netdata", {})
    if netdata and any(v is not None for v in netdata.values()):
        html += "<h2>Métricas en tiempo real (Netdata)</h2>\n<ul>\n"
        if netdata.get("cpu_avg_60s") is not None:
            html += f"<li>CPU de la VM (promedio últimos 60 s): {netdata['cpu_avg_60s']:.1f} %</li>\n"
        if netdata.get("load_avg_1m") is not None:
            html += f"<li>Load average 1 minuto: {netdata['load_avg_1m']:.2f}</li>\n"
        if netdata.get("ram_uso_pct") is not None:
            html += f"<li>RAM usada en la VM (promedio últimos 60 s): {netdata['ram_uso_pct']:.1f} %</li>\n"
        html += "</ul>\n"

    # Sección: Resumen histórico
    resumen = diag.get("resumen", {})
    if resumen and resumen.get("muestras"):
        html += f"""
        <h2>Resumen histórico de métricas</h2>
        <p>Basado en las últimas {int(resumen['muestras'])} mediciones:</p>
        <ul>
            <li>CPU media: {resumen['cpu_prom']:.1f} %</li>
            <li>RAM media: {resumen['ram_prom']:.1f} %</li>
            <li>Uso medio de Disco C:: {resumen['disco_prom']:.1f} %</li>
        </ul>
"""

    # Sección: Recomendaciones de capacidad
    recs = diag.get("recomendaciones", [])
    if recs:
        html += """
        <h2>Recomendaciones de capacidad (VM vs Host)</h2>
        <ul>
"""
        for rec in recs:
            html += f"<li>{rec}</li>\n"
        html += """
        </ul>
"""

    # Sección: Alertas simuladas (zona de pruebas)
    alertas_sim = diag.get("alertas_simuladas", [])
    if alertas_sim:
        html += """
        <h2>Alertas simuladas (zona de pruebas)</h2>
        <ul>
"""
        for a in alertas_sim:
            html += f"<li>{a}</li>\n"
        html += """
        </ul>
"""

    html += """
    <div class="footer">
        <p>Reporte generado automáticamente por Sistema de Diagnóstico y Auditoría.</p>
        <p>Cumple con buenas prácticas de monitoreo y auditoría.</p>
    </div>
</div>
</body>
</html>
"""

    return html


def exportar_diagnostico_html(diag: Dict[str, Any], ruta_salida: str = None) -> str:
    """
    Genera y guarda el HTML del diagnóstico a un archivo.
    
    Args:
        diag: dict con diagnóstico.
        ruta_salida: ruta donde guardar (por defecto ./reportes/diag_TIMESTAMP.html)
    
    Returns:
        Ruta completa del archivo creado.
    """
    if ruta_salida is None:
        Path("reportes").mkdir(exist_ok=True)
        ruta_salida = f"reportes/diagnostico_{_timestamp_iso()}.html"

    html_contenido = generar_html_diagnostico(diag)
    
    Path(ruta_salida).parent.mkdir(parents=True, exist_ok=True)
    with open(ruta_salida, "w", encoding="utf-8") as f:
        f.write(html_contenido)

    return ruta_salida


def exportar_diagnostico_pdf(diag: Dict[str, Any], ruta_salida: str = None) -> str:
    """
    Placeholder para exportación a PDF.
    
    Cuando quieras integrar una librería (pdf-reports, xhtml2pdf, etc.),
    usarás generar_html_diagnostico(diag) y convertirás el HTML a PDF.
    
    Por ahora, solo guarda el HTML como base.
    """
    # Por ahora, generamos el HTML y dejamos listo el placeholder
    html_path = exportar_diagnostico_html(diag)
    
    if ruta_salida is None:
        Path("reportes").mkdir(exist_ok=True)
        ruta_salida = f"reportes/diagnostico_{_timestamp_iso()}.pdf"

    # TODO: Integrar librería PDF (pdf-reports, xhtml2pdf, weasyprint, etc.)
    # Por ahora, solo registramos en notificaciones que es un placeholder.
    
    return ruta_salida
