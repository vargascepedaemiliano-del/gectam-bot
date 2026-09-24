"""
GECTAM Bot - Panel administrativo
Fase 3 (Desarrollo) del proyecto de estadía.

Panel simple en Streamlit para que alguien de GECTAM pueda ver:
- El catálogo de servicios
- Las cotizaciones generadas
- El historial de conversaciones

No necesita la API de Claude para funcionar, solo lee la base de datos
SQLite que ya creó el backend (gectam.db).
"""

import os
import sqlite3

import pandas as pd
import streamlit as st

# Ruta a la base de datos: está en la carpeta backend, un nivel arriba de esta
DB_PATH = os.path.join(os.path.dirname(__file__), "..", "backend", "gectam.db")

st.set_page_config(page_title="Panel GECTAM", layout="wide")


def cargar_tabla(nombre_tabla: str) -> pd.DataFrame:
    """Lee una tabla completa de la base de datos y la devuelve como DataFrame."""
    if not os.path.exists(DB_PATH):
        st.error(
            f"No encontré la base de datos en: {DB_PATH}\n\n"
            "Asegúrate de haber corrido 'python database.py' dentro de la carpeta backend."
        )
        return pd.DataFrame()

    conn = sqlite3.connect(DB_PATH)
    try:
        df = pd.read_sql_query(f"SELECT * FROM {nombre_tabla}", conn)
    finally:
        conn.close()
    return df


st.title("Panel administrativo — GECTAM")

seccion = st.sidebar.radio(
    "Sección",
    ["Catálogo de servicios", "Cotizaciones", "Conversaciones"],
)

if seccion == "Catálogo de servicios":
    st.header("Catálogo de servicios")
    st.caption("Estos son datos de ejemplo por ahora. Se reemplazan por el catálogo real de GECTAM más adelante.")
    df = cargar_tabla("servicios")
    st.dataframe(df, use_container_width=True)

elif seccion == "Cotizaciones":
    st.header("Cotizaciones generadas")
    df = cargar_tabla("cotizaciones")
    if df.empty:
        st.info("Todavía no hay cotizaciones generadas. Aparecerán aquí cuando el bot esté conectado a la IA y algún cliente cotice.")
    else:
        st.dataframe(df, use_container_width=True)
        st.metric("Total de cotizaciones", len(df))

elif seccion == "Conversaciones":
    st.header("Historial de conversaciones")
    df = cargar_tabla("conversaciones")
    if df.empty:
        st.info("Todavía no hay conversaciones registradas.")
    else:
        st.dataframe(df, use_container_width=True)
