"""
Módulo de histórico de mediciones.
Usa PostgreSQL si PG_ENABLED=true en .env, de lo contrario usa SQLite local.
"""

import os
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

import psycopg2
from psycopg2.extras import DictCursor

from utils.config import (
    PG_HOST,
    PG_PORT,
    PG_DB,
    PG_USER,
    PG_PASSWORD,
)

# SQLite como fallback/local
DB_PATH = Path("reportes/historico.db")


def _pg_enabled() -> bool:
    return os.getenv("PG_ENABLED", "false").lower() == "true"


# ---------- PostgreSQL ----------

def _get_pg_conn():
    """
    Devuelve conexión a Postgres o None si falla.
    Requiere que el contenedor 'diag_postgres' esté arriba.
    """
    try:
        conn = psycopg2.connect(
            host=PG_HOST,
            port=int(PG_PORT),
            dbname=PG_DB,
            user=PG_USER,
            password=PG_PASSWORD or None,
            cursor_factory=DictCursor,
        )
        return conn
    except Exception:
        return None


def _init_pg():
    conn = _get_pg_conn()
    if conn is None:
        return
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS mediciones (
            id SERIAL PRIMARY KEY,
            ts TIMESTAMPTZ NOT NULL,
            cpu_uso DOUBLE PRECISION,
            ram_uso DOUBLE PRECISION,
            disco_c_uso DOUBLE PRECISION,
            swap_pfree DOUBLE PRECISION,
            estado_global TEXT
        )
        """
    )
    conn.commit()
    conn.close()


def _guardar_medicion_pg(diag: Dict[str, Any]) -> bool:
    _init_pg()
    conn = _get_pg_conn()
    if conn is None:
        return False

    zbx = diag.get("zabbix", {})
    ts = datetime.now()  # timezone naive; Postgres lo almacena como timestamptz
    fila = (
        ts,
        zbx.get("cpu_uso_pct"),
        zbx.get("ram_uso_pct"),
        zbx.get("disco_c_uso_pct"),
        zbx.get("swap_pfree_pct"),
        diag.get("estado_global", "OK"),
    )

    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO mediciones (ts, cpu_uso, ram_uso, disco_c_uso, swap_pfree, estado_global)
        VALUES (%s, %s, %s, %s, %s, %s)
        """,
        fila,
    )
    conn.commit()
    conn.close()
    return True


def _obtener_resumen_pg(n_ultimas: int) -> Optional[dict]:
    _init_pg()
    conn = _get_pg_conn()
    if conn is None:
        return None
    cur = conn.cursor()
    cur.execute(
        """
        SELECT
            AVG(cpu_uso) AS cpu_prom,
            AVG(ram_uso) AS ram_prom,
            AVG(disco_c_uso) AS disco_prom,
            AVG(swap_pfree) AS swap_pfree_prom,
            COUNT(*) AS muestras
        FROM (
            SELECT cpu_uso, ram_uso, disco_c_uso, swap_pfree
            FROM mediciones
            ORDER BY id DESC
            LIMIT %s
        ) t
        """,
        (n_ultimas,),
    )
    row = cur.fetchone()
    conn.close()
    if not row or row["muestras"] == 0:
        return None
    return dict(row)


# ---------- SQLite (fallback/local) ----------

def _init_sqlite():
    DB_PATH.parent.mkdir(exist_ok=True)
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS mediciones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts TEXT NOT NULL,
            cpu_uso REAL,
            ram_uso REAL,
            disco_c_uso REAL,
            swap_pfree REAL,
            estado_global TEXT
        )
        """
    )
    con.commit()
    con.close()


def _guardar_medicion_sqlite(diag: Dict[str, Any]) -> None:
    _init_sqlite()
    zbx = diag.get("zabbix", {})
    ts = datetime.now().isoformat(timespec="seconds")
    fila = (
        ts,
        zbx.get("cpu_uso_pct"),
        zbx.get("ram_uso_pct"),
        zbx.get("disco_c_uso_pct"),
        zbx.get("swap_pfree_pct"),
        diag.get("estado_global", "OK"),
    )
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute(
        """
        INSERT INTO mediciones (ts, cpu_uso, ram_uso, disco_c_uso, swap_pfree, estado_global)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        fila,
    )
    con.commit()
    con.close()


def _obtener_resumen_sqlite(n_ultimas: int) -> dict:
    if not DB_PATH.exists():
        return {}

    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute(
        """
        SELECT
            AVG(cpu_uso),
            AVG(ram_uso),
            AVG(disco_c_uso),
            AVG(swap_pfree),
            COUNT(*)
        FROM (
            SELECT cpu_uso, ram_uso, disco_c_uso, swap_pfree
            FROM mediciones
            ORDER BY id DESC
            LIMIT ?
        )
        """,
        (n_ultimas,),
    )
    row = cur.fetchone()
    con.close()

    if not row or row[-1] == 0:
        return {}

    return {
        "cpu_prom": row[0],
        "ram_prom": row[1],
        "disco_prom": row[2],
        "swap_pfree_prom": row[3],
        "muestras": row[4],
    }


# ---------- API pública del módulo ----------

def guardar_medicion(diag: Dict[str, Any]) -> None:
    """
    Guarda una fila en el histórico. Intenta Postgres si está habilitado;
    si falla, usa SQLite local.
    """
    if _pg_enabled():
        ok = _guardar_medicion_pg(diag)
        if ok:
            return
    # Fallback
    _guardar_medicion_sqlite(diag)


def obtener_resumen(n_ultimas: int = 20) -> dict:
    """
    Devuelve promedios simples de las últimas N mediciones.
    Intenta Postgres si está habilitado; si falla, usa SQLite.
    """
    if _pg_enabled():
        resumen = _obtener_resumen_pg(n_ultimas)
        if resumen is not None and resumen.get("muestras", 0) > 0:
            return resumen
    # Fallback
    return _obtener_resumen_sqlite(n_ultimas)
