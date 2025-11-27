"""
Escenarios de prueba de alertas para diagnóstico de VMs.
No alteran el sistema real; solo generan alertas y recomendaciones simuladas.
"""

from typing import List, Dict

ESCENARIOS = {
    "cpu_alta": {
        "nombre": "CPU alta sostenida",
        "descripcion": "Simula una VM con uso de CPU > 90% durante largos periodos.",
        "alertas": [
            "Uso de CPU sobre el 90% sostenido. Revisar procesos intensivos.",
        ],
        "recomendaciones": [
            "Identificar procesos que consumen CPU y optimizarlos o limitar su uso.",
            "Considerar asignar más vCPU a la VM si el host tiene capacidad suficiente.",
        ],
    },
    "ram_casi_llena": {
        "nombre": "RAM casi al límite",
        "descripcion": "Simula una VM que usa más del 90% de la RAM asignada.",
        "alertas": [
            "Uso de RAM por encima del 90%. Riesgo de swapping y lentitud general.",
        ],
        "recomendaciones": [
            "Cerrar aplicaciones no críticas y liberar memoria.",
            "Aumentar la RAM asignada a la VM sin exceder los límites recomendados del host.",
        ],
    },
    "disco_c_casi_lleno": {
        "nombre": "Disco C: casi lleno",
        "descripcion": "Simula una partición C: con menos del 10% de espacio libre.",
        "alertas": [
            "Espacio libre en disco C: por debajo del 10%. Riesgo de fallos de escritura.",
        ],
        "recomendaciones": [
            "Eliminar archivos temporales y logs antiguos.",
            "Mover datos no críticos a otro disco o almacenamiento externo.",
        ],
    },
    "host_ajustado": {
        "nombre": "Host con recursos ajustados",
        "descripcion": "Simula un host casi al límite de CPU/RAM con varias VMs.",
        "alertas": [
            "Host físico cercano al límite de capacidad. Nuevas asignaciones a la VM pueden afectar estabilidad.",
        ],
        "recomendaciones": [
            "Evitar sobreasignar CPU/RAM a la VM hasta ampliar recursos del host.",
            "Evaluar consolidación de VMs o apagado de servicios no críticos.",
        ],
    },
}


def obtener_escenarios_disponibles() -> List[Dict]:
    return [
        {"id": clave, "nombre": datos["nombre"], "descripcion": datos["descripcion"]}
        for clave, datos in ESCENARIOS.items()
    ]


def aplicar_escenario(escenario_id: str) -> Dict[str, List[str]]:
    """
    Devuelve las alertas y recomendaciones del escenario indicado.
    No modifica nada, solo genera información simulada.
    """
    datos = ESCENARIOS.get(escenario_id)
    if not datos:
        return {"alertas": [], "recomendaciones": []}
    return {
        "alertas": datos["alertas"],
        "recomendaciones": datos["recomendaciones"],
    }
