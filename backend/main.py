"""
GECTAM Bot - Backend
Fase 3 (Desarrollo) del proyecto de estadía.

El endpoint /chat ahora llama a la API de Claude (Anthropic) para generar
respuestas reales. El catálogo de servicios todavía es de ejemplo (genérico);
en el Paso 7 lo reemplazamos con la info real de GECTAM.
"""

import os

from anthropic import Anthropic
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

load_dotenv()  # lee las variables del archivo .env

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
if not ANTHROPIC_API_KEY:
    raise RuntimeError(
        "Falta ANTHROPIC_API_KEY. Crea un archivo .env en la carpeta backend "
        "(usa .env.example como base) con tu API key de Anthropic."
    )

client = Anthropic(api_key=ANTHROPIC_API_KEY)

# --- Prompt del sistema: esto define cómo se comporta el bot ---
# Es genérico por ahora. En el Paso 7 lo actualizamos con el catálogo real
# de servicios, precios y reglas de negocio de GECTAM.
SYSTEM_PROMPT = """
Eres el asistente virtual de GECTAM, una empresa de servicios. Tu trabajo es
ayudar a los clientes a entender qué servicios ofrece la empresa y guiarlos
para armar una cotización.

Por ahora NO tienes un catálogo real de servicios cargado (esto se agregará
después), así que si el cliente pregunta por precios o servicios específicos,
explica amablemente que estás en fase de prueba y que pronto tendrás el
catálogo completo. Sé breve, claro y amigable.
"""

app = FastAPI(title="GECTAM Bot API")

# CORS: permite que el widget de chat (que corre en el navegador, en otro
# origen) pueda hacer peticiones a este backend. Cuando despliegues a
# producción, cambia allow_origins=["*"] por el dominio real de GECTAM.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatMessage(BaseModel):
    message: str
    # Más adelante añadiremos aquí un session_id o similar para llevar
    # el historial de la conversación de cada cliente.


class ChatResponse(BaseModel):
    reply: str


@app.get("/")
def root():
    return {"status": "ok", "service": "GECTAM Bot API"}


@app.post("/chat", response_model=ChatResponse)
def chat(payload: ChatMessage):
    """
    Endpoint que recibe el mensaje del cliente desde el widget de chat,
    se lo manda a Claude junto con el prompt de sistema, y devuelve la
    respuesta generada.
    """
    user_message = payload.message.strip()

    if not user_message:
        return ChatResponse(reply="No recibí ningún mensaje, ¿puedes escribir de nuevo?")

    try:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=500,
            system=SYSTEM_PROMPT,
            messages=[
                {"role": "user", "content": user_message}
            ],
        )
        reply_text = response.content[0].text
    except Exception as e:
        # Si algo falla (key inválida, sin conexión, etc.) no tumbamos el
        # servidor: devolvemos un error controlado.
        raise HTTPException(status_code=500, detail=f"Error al llamar a la IA: {e}")

    return ChatResponse(reply=reply_text)
