
# Diagnóstico de Máquinas Virtuales con Zabbix

Sistema de diagnóstico y mantenimiento para máquinas virtuales (y hosts físicos) integrado con **Zabbix**, **psutil** y **Docker**.  
Incluye una **GUI administrativa** en Tkinter, histórico de métricas en **PostgreSQL/SQLite** y exporte de reportes en **CSV/HTML** listos para PDF.

## Características

- Reconocimiento de sistema:
  - Detección de VM vs equipo físico.
  - Modelo de CPU, núcleos/hilos, frecuencias base/actuales.
  - RAM total (GB) y disco principal (GB).

- Integración con Zabbix:
  - CPU, RAM y uso de disco C: del host Windows monitorizado.
  - Uptime, uso de swap y estado de servicios críticos (por ejemplo AnyDesk).
  - Cálculo de **estado global** (OK / ADVERTENCIA / CRÍTICO) con motivos.

- Recomendaciones de capacidad:
  - Sugerencias para aumentar RAM/vCPU de la VM sin exceder los límites del host físico (configurables por `.env`).

- Histórico de métricas:
  - Registro automático de mediciones en cada diagnóstico.
  - Almacenamiento en **PostgreSQL** (Docker) o **SQLite** como fallback.
  - Resumen de promedios de las últimas N mediciones (CPU, RAM, disco, swap).

- Diagnóstico de red:
  - Latencia ICMP desde la VM/host hasta el servidor Zabbix.

- Reportes:
  - Exportación a **CSV** con secciones y recomendaciones.
  - Exportación a **HTML** con diseño administrativo, listo para convertir a PDF.

- GUI administrativa:
  - Panel de **reconocimiento de sistema**.
  - Panel de **estado desde Zabbix**.
  - Zona de **notificaciones** centralizada.
  - **Zona de pruebas de alertas** (escenarios simulados) sin afectar el sistema real.

## Requisitos

- Python 3.11+  
- Docker / Docker Desktop (para Postgres y, opcionalmente, Netdata)  
- Servidor Zabbix accesible por HTTP/HTTPS.[3][1]

## Instalación (Linux / Ubuntu)

```bash
git clone https://github.com/WokerJJ/diagnostico-vm-zabbix.git
cd diagnostico-vm-zabbix
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### Contenedor PostgreSQL (opcional pero recomendado)

```bash
docker run -d \
  --name diag_postgres \
  -e POSTGRES_USER=diag_user \
  -e POSTGRES_DB=diag_db \
  -e POSTGRES_HOST_AUTH_METHOD=trust \
  -p 5432:5432 \
  postgres:16
```

> Uso educativo / laboratorio: el contenedor está configurado en modo **trust** (sin contraseña). No se recomienda exponerlo fuera de la red local.[1][3]

## Configuración (.env)

Crea un archivo `.env` en la raíz:

```env
# Zabbix
ZABBIX_URL=http://192.168.1.9:8080/api_jsonrpc.php
ZABBIX_TOKEN=TU_TOKEN_ZABBIX
ZABBIX_HOSTNAME=WIN-LAPTOP

# Entorno (por ejemplo: vm_ubuntu, windows_fisico, etc.)
APP_ENTORNO=vm_ubuntu

# Capacidad del host físico (para recomendaciones de VM)
HOST_RAM_GB=16
HOST_CPU_CORES=8

# Base de datos (PostgreSQL vía Docker)
PG_HOST=localhost
PG_PORT=5432
PG_DB=diag_db
PG_USER=diag_user
PG_PASSWORD=
PG_ENABLED=true
```

## Ejecución

```bash
# Activar entorno
source venv/bin/activate

# Lanzar la GUI
python main.py
```

En Windows:

```powershell
cd C:\ruta\diagnostico-vm-zabbix
venv\Scripts\activate
python main.py
```

## Estructura del proyecto (resumen)

```text
diagnostico-vm-zabbix/
├─ main.py               # Lanzador de la GUI
├─ .env                  # Configuración (no se sube al repo)
├─ requirements.txt
├─ gui/
│  └─ gui_main.py        # Ventana principal, notificaciones, acciones
├─ monitor/
│  ├─ sistema_local.py   # Reconocimiento de sistema (CPU/RAM/disco, VM/físico)
│  ├─ zabbix_client.py   # Cliente API Zabbix (token Bearer)
│  ├─ reconocimiento.py  # Orquestación del diagnóstico completo
│  ├─ historico.py       # Histórico en PostgreSQL/SQLite
│  └─ red.py             # Latencia ICMP
├─ utils/
│  ├─ config.py          # Carga de .env y constantes
│  ├─ notificaciones.py  # Sistema centralizado de notificaciones
│  └─ exportar.py        # Exportación CSV/HTML (PDF listo para integrar)
└─ reportes/             # Salida de reportes (ignorada por git)
```

## Estado actual

- Integración con Zabbix funcional (CPU/RAM/Disco/Swap/Uptime/Servicios).[1]
- GUI administrativa usable en Ubuntu y Windows.
- Histórico de mediciones y resumen básico.
- Reportes CSV/HTML listos para convertir a PDF.


Proyecto orientado a prácticas de **mantenimiento y diagnóstico de infraestructuras virtualizadas**, combinando métricas locales, Zabbix y contenedores Docker.