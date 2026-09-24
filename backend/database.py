"""
GECTAM Bot - Base de datos
Fase 3 (Desarrollo) del proyecto de estadía.

Este módulo crea y maneja la base de datos SQLite del proyecto.
Contiene 3 tablas:
  - servicios: el catálogo de GECTAM (por ahora con datos de ejemplo)
  - conversaciones: el historial de mensajes de cada sesión de chat
  - cotizaciones: las cotizaciones generadas, para el panel administrativo

No depende de la API de Claude para nada de lo que hace aquí.
"""

import sqlite3
from datetime import datetime

DB_NAME = "gectam.db"


def get_connection():
    """Abre una conexión a la base de datos SQLite."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row  # permite acceder a columnas por nombre
    return conn


def init_db():
    """Crea las tablas si no existen todavía, y siembra datos de ejemplo."""
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS servicios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            descripcion TEXT,
            precio REAL,
            tipo_precio TEXT DEFAULT 'fijo',       -- 'fijo' o 'variable'
            cotizable_automatico INTEGER DEFAULT 1  -- 1 = sí, 0 = no (requiere que un humano cotice)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS conversaciones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            remitente TEXT NOT NULL,   -- 'cliente' o 'bot'
            mensaje TEXT NOT NULL,
            fecha TEXT NOT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS cotizaciones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            cliente_nombre TEXT,
            cliente_contacto TEXT,
            resumen TEXT,
            total REAL,
            fecha TEXT NOT NULL
        )
    """)

    conn.commit()

    # --- Datos de ejemplo (genéricos) para poder probar el sistema ---
    # Cuando tengas el catálogo real de GECTAM (Fase 1), borramos esto y
    # metemos los servicios reales.
    cur.execute("SELECT COUNT(*) FROM servicios")
    if cur.fetchone()[0] == 0:
        servicios_ejemplo = [
            ("Servicio de ejemplo A", "Descripción genérica del servicio A", 500.0, "fijo", 1),
            ("Servicio de ejemplo B", "Descripción genérica del servicio B", 1200.0, "variable", 1),
            ("Servicio especial (requiere cotización manual)", "Este tipo de servicio no se cotiza automático", None, "variable", 0),
        ]
        cur.executemany(
            "INSERT INTO servicios (nombre, descripcion, precio, tipo_precio, cotizable_automatico) VALUES (?, ?, ?, ?, ?)",
            servicios_ejemplo,
        )
        conn.commit()

    conn.close()


def guardar_mensaje(session_id: str, remitente: str, mensaje: str):
    """Guarda un mensaje (del cliente o del bot) en el historial."""
    conn = get_connection()
    conn.execute(
        "INSERT INTO conversaciones (session_id, remitente, mensaje, fecha) VALUES (?, ?, ?, ?)",
        (session_id, remitente, mensaje, datetime.now().isoformat()),
    )
    conn.commit()
    conn.close()


def obtener_historial(session_id: str, limite: int = 20):
    """
    Devuelve los últimos mensajes de una sesión, en orden cronológico,
    listos para mandarle a Claude como historial de la conversación.
    """
    conn = get_connection()
    filas = conn.execute(
        "SELECT remitente, mensaje FROM conversaciones WHERE session_id = ? ORDER BY id DESC LIMIT ?",
        (session_id, limite),
    ).fetchall()
    conn.close()
    return list(reversed(filas))  # los regresamos en orden cronológico


def obtener_catalogo():
    """Devuelve todos los servicios del catálogo."""
    conn = get_connection()
    filas = conn.execute("SELECT * FROM servicios").fetchall()
    conn.close()
    return [dict(f) for f in filas]


def guardar_cotizacion(session_id: str, cliente_nombre: str, cliente_contacto: str, resumen: str, total: float):
    """Guarda una cotización generada, para que el panel administrativo la vea."""
    conn = get_connection()
    conn.execute(
        "INSERT INTO cotizaciones (session_id, cliente_nombre, cliente_contacto, resumen, total, fecha) VALUES (?, ?, ?, ?, ?, ?)",
        (session_id, cliente_nombre, cliente_contacto, resumen, total, datetime.now().isoformat()),
    )
    conn.commit()
    conn.close()


if __name__ == "__main__":
    # Puedes correr este archivo solo (python database.py) para crear
    # la base de datos sin tener que levantar el servidor completo.
    init_db()
    print(f"Base de datos '{DB_NAME}' creada/actualizada correctamente.")
    print("Catálogo actual:")
    for s in obtener_catalogo():
        print(" -", s)
