import os
from dotenv import load_dotenv

load_dotenv()

ZABBIX_URL = os.getenv("ZABBIX_URL")
ZABBIX_TOKEN = os.getenv("ZABBIX_TOKEN")
ZABBIX_HOSTNAME = os.getenv("ZABBIX_HOSTNAME", "WIN-LAPTOP")

APP_ENTORNO = os.getenv("APP_ENTORNO", "desconocido")

HOST_RAM_GB = float(os.getenv("HOST_RAM_GB", "0"))
HOST_CPU_CORES = int(os.getenv("HOST_CPU_CORES", "0"))

PG_HOST = os.getenv("PG_HOST", "localhost")
PG_PORT = os.getenv("PG_PORT", "5432")
PG_DB = os.getenv("PG_DB", "diag_db")
PG_USER = os.getenv("PG_USER", "diag_user")
PG_PASSWORD = os.getenv("PG_PASSWORD", "")