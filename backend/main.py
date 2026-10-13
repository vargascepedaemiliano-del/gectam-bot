"""
GECTAM Bot - Backend (versión 2)

Cambios respecto a la versión anterior:
  - El bot ahora conoce el catálogo de la base de datos.
  - Recuerda la conversación (por session_id).
  - Guarda conversaciones y cotizaciones en SQLite.
  - La lógica del bot vive en cotizador.py; aquí solo está la API web.
"""

import hmac
import os
import re
import time
from typing import Literal, Optional

from anthropic import Anthropic
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

import cotizador
import database

load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
if not ANTHROPIC_API_KEY:
    raise RuntimeError(
        "Falta ANTHROPIC_API_KEY. Crea un archivo .env en la carpeta backend "
        "(usa .env.example como base) con tu API key de Anthropic."
    )

client = Anthropic(api_key=ANTHROPIC_API_KEY)

# Crea las tablas y los datos de ejemplo si la base de datos no existe
# (importante en Render, donde el archivo gectam.db no viene en GitHub).
database.init_db()

app = FastAPI(title="GECTAM Bot API")

# CORS: cuando el sitio de GECTAM esté en su dominio real, cambia ["*"]
# por la lista de dominios permitidos, por ejemplo ["https://www.gectam.com"].
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

SESSION_RE = re.compile(r"^[A-Za-z0-9_-]{8,64}$")


class ChatMessage(BaseModel):
    message: str = Field(..., max_length=2000)
    session_id: str = Field(..., description="Identificador de la conversación (lo genera el widget)")


class ChatResponse(BaseModel):
    reply: str


@app.get("/")
def root():
    return {"status": "ok", "service": "GECTAM Bot API", "version": 2}


@app.post("/chat", response_model=ChatResponse)
def chat(payload: ChatMessage):
    if not SESSION_RE.match(payload.session_id):
        raise HTTPException(status_code=400, detail="session_id inválido")

    if not payload.message.strip():
        return ChatResponse(reply="No recibí ningún mensaje, ¿puedes escribir de nuevo?")

    try:
        reply = cotizador.responder(client, payload.session_id, payload.message)
    except Exception as e:
        # No exponemos el detalle al cliente final; queda en los logs de Render.
        print(f"[ERROR] /chat falló: {e!r}")
        raise HTTPException(status_code=500, detail="El asistente no está disponible por el momento.")

    return ChatResponse(reply=reply)


# ---------------------------------------------------------------------------
# Panel de administrador
# Se protege con una contraseña que pones en Render como variable de entorno
# ADMIN_PASSWORD. Si no existe esa variable, el panel queda desactivado.
# ---------------------------------------------------------------------------

ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "")


def requiere_admin(x_admin_password: str = Header(default="")):
    if not ADMIN_PASSWORD:
        raise HTTPException(status_code=503, detail="Panel de administrador desactivado: falta ADMIN_PASSWORD en el servidor.")
    if not hmac.compare_digest(x_admin_password.encode(), ADMIN_PASSWORD.encode()):
        time.sleep(1)  # frena intentos repetidos de adivinar la contraseña
        raise HTTPException(status_code=401, detail="Contraseña incorrecta.")


class ServicioIn(BaseModel):
    nombre: str = Field(..., min_length=1, max_length=120)
    descripcion: Optional[str] = Field(default="", max_length=500)
    precio: Optional[float] = Field(default=None, ge=0)
    tipo_precio: Literal["fijo", "variable"] = "fijo"
    cotizable_automatico: bool = True


@app.get("/admin/resumen", dependencies=[Depends(requiere_admin)])
def admin_resumen():
    return database.estadisticas()


@app.get("/admin/sesiones", dependencies=[Depends(requiere_admin)])
def admin_sesiones():
    return database.listar_sesiones()


@app.get("/admin/sesiones/{session_id}", dependencies=[Depends(requiere_admin)])
def admin_sesion(session_id: str):
    return database.mensajes_de_sesion(session_id)


@app.get("/admin/cotizaciones", dependencies=[Depends(requiere_admin)])
def admin_cotizaciones():
    return database.listar_cotizaciones()


@app.get("/admin/servicios", dependencies=[Depends(requiere_admin)])
def admin_servicios():
    return database.obtener_catalogo()


@app.post("/admin/servicios", dependencies=[Depends(requiere_admin)])
def admin_crear_servicio(s: ServicioIn):
    nuevo_id = database.crear_servicio(s.nombre, s.descripcion, s.precio, s.tipo_precio, s.cotizable_automatico)
    return {"id": nuevo_id}


@app.put("/admin/servicios/{servicio_id}", dependencies=[Depends(requiere_admin)])
def admin_actualizar_servicio(servicio_id: int, s: ServicioIn):
    if not database.actualizar_servicio(servicio_id, s.nombre, s.descripcion, s.precio, s.tipo_precio, s.cotizable_automatico):
        raise HTTPException(status_code=404, detail="Servicio no encontrado.")
    return {"ok": True}


@app.delete("/admin/servicios/{servicio_id}", dependencies=[Depends(requiere_admin)])
def admin_borrar_servicio(servicio_id: int):
    if not database.borrar_servicio(servicio_id):
        raise HTTPException(status_code=404, detail="Servicio no encontrado.")
    return {"ok": True}
