"""
GECTAM Bot - Lógica del cotizador (sin FastAPI)

Aquí vive todo lo que "piensa" el bot:
  - construir el prompt con el catálogo real de la base de datos
  - llamar a Claude con memoria de la conversación
  - ejecutar la herramienta `registrar_cotizacion` cuando el cliente ya
    confirmó qué quiere

Regla importante: el TOTAL de una cotización lo calcula este código con los
precios de la base de datos, nunca la IA. Así el bot no puede inventar precios.
"""

import json
import os

import database as db

MODELO = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-6")
MAX_TOKENS = 700
MAX_MENSAJE = 1000      # caracteres máximos por mensaje del cliente
MAX_VUELTAS_TOOL = 4    # evita ciclos infinitos con herramientas


def _fmt_precio(valor):
    return "sin precio fijo" if valor is None else f"${valor:,.2f} MXN"


def construir_prompt_sistema(catalogo: list[dict]) -> str:
    """Arma el prompt del sistema con el catálogo actual de la BD."""
    automaticos, manuales = [], []
    for s in catalogo:
        if s["cotizable_automatico"] and s["precio"] is not None:
            tipo = "precio fijo" if s["tipo_precio"] == "fijo" else "precio base, puede variar"
            automaticos.append(
                f"- ID {s['id']}: {s['nombre']} — {s['descripcion'] or 'sin descripción'} "
                f"({_fmt_precio(s['precio'])}, {tipo})"
            )
        else:
            manuales.append(f"- {s['nombre']} — {s['descripcion'] or 'sin descripción'}")

    bloque_auto = "\n".join(automaticos) or "(no hay servicios cotizables automáticamente por ahora)"
    bloque_manual = "\n".join(manuales) or "(ninguno)"

    return f"""Eres el asistente virtual de GECTAM, una empresa de servicios. Atiendes a clientes por chat en español, con un tono amable, claro y breve (máximo 4-5 líneas por respuesta).

TU TRABAJO
1. Entender qué necesita el cliente y explicarle los servicios disponibles.
2. Armar una cotización con los servicios del catálogo.
3. Cuando el cliente confirme qué servicios y cantidades quiere, y te dé su nombre y un medio de contacto (teléfono o correo), usa la herramienta `registrar_cotizacion`.
4. Después de registrarla, dile al cliente el total que te devolvió la herramienta y que alguien de GECTAM lo contactará para confirmar.

CATÁLOGO DE SERVICIOS COTIZABLES AUTOMÁTICAMENTE
{bloque_auto}

SERVICIOS QUE REQUIEREN COTIZACIÓN MANUAL (no puedes dar precio)
{bloque_manual}

REGLAS ESTRICTAS
- Usa ÚNICAMENTE los servicios y precios del catálogo de arriba. NUNCA inventes servicios, precios, descuentos ni promociones.
- Nunca calcules ni prometas un total por tu cuenta: el total oficial lo devuelve `registrar_cotizacion`. Puedes dar un estimado verbal solo si dejas claro que es aproximado.
- Si piden algo que no está en el catálogo o que requiere cotización manual, explica que una persona de GECTAM lo atenderá, y pídele su nombre y contacto.
- Si no sabes algo de la empresa (horarios, ubicación, políticas), dilo con honestidad en lugar de adivinar.
- No pidas más datos personales de los necesarios (solo nombre y contacto).
- Responde solo sobre temas de GECTAM y sus servicios; si preguntan otra cosa, redirige amablemente.
"""


HERRAMIENTAS = [
    {
        "name": "registrar_cotizacion",
        "description": (
            "Registra la cotización final cuando el cliente ya confirmó los servicios y cantidades "
            "y proporcionó su nombre y un medio de contacto. Devuelve el total oficial calculado "
            "con los precios del catálogo."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "cliente_nombre": {"type": "string", "description": "Nombre del cliente"},
                "cliente_contacto": {"type": "string", "description": "Teléfono o correo del cliente"},
                "servicios": {
                    "type": "array",
                    "description": "Servicios que el cliente quiere contratar",
                    "items": {
                        "type": "object",
                        "properties": {
                            "servicio_id": {"type": "integer", "description": "ID del servicio en el catálogo"},
                            "cantidad": {"type": "integer", "description": "Cantidad (mínimo 1)"},
                        },
                        "required": ["servicio_id", "cantidad"],
                    },
                },
            },
            "required": ["cliente_nombre", "cliente_contacto", "servicios"],
        },
    }
]


def ejecutar_registrar_cotizacion(session_id: str, datos: dict) -> dict:
    """
    Valida lo que pidió la IA contra la base de datos, calcula el total y
    guarda la cotización. Devuelve un dict (se le regresa a la IA como resultado).
    """
    nombre = str(datos.get("cliente_nombre", "")).strip()
    contacto = str(datos.get("cliente_contacto", "")).strip()
    items = datos.get("servicios") or []

    if not nombre or not contacto:
        return {"ok": False, "error": "Faltan el nombre o el contacto del cliente. Pídeselos."}
    if not isinstance(items, list) or not items:
        return {"ok": False, "error": "No se indicó ningún servicio."}

    catalogo = {s["id"]: s for s in db.obtener_catalogo()}
    lineas, total = [], 0.0

    for it in items:
        try:
            sid = int(it.get("servicio_id"))
            cantidad = int(it.get("cantidad", 1))
        except (TypeError, ValueError, AttributeError):
            return {"ok": False, "error": "Servicio o cantidad inválidos."}
        if cantidad < 1 or cantidad > 1000:
            return {"ok": False, "error": f"Cantidad inválida para el servicio {sid}."}
        s = catalogo.get(sid)
        if s is None:
            return {"ok": False, "error": f"El servicio con ID {sid} no existe en el catálogo."}
        if not s["cotizable_automatico"] or s["precio"] is None:
            return {
                "ok": False,
                "error": f"'{s['nombre']}' requiere cotización manual; no se puede incluir. "
                         "Dile al cliente que una persona de GECTAM lo atenderá.",
            }
        subtotal = s["precio"] * cantidad
        total += subtotal
        nota = " (precio base, puede variar)" if s["tipo_precio"] == "variable" else ""
        lineas.append(f"{cantidad} x {s['nombre']} @ {_fmt_precio(s['precio'])} = {_fmt_precio(subtotal)}{nota}")

    resumen = "\n".join(lineas)
    db.guardar_cotizacion(session_id, nombre, contacto, resumen, total)
    return {"ok": True, "total": total, "total_formateado": _fmt_precio(total), "detalle": resumen}


def _a_mensajes_api(historial) -> list[dict]:
    """Convierte el historial de la BD al formato de la API (roles alternados)."""
    mensajes = []
    for fila in historial:
        rol = "user" if fila["remitente"] == "cliente" else "assistant"
        if mensajes and mensajes[-1]["role"] == rol:
            mensajes[-1]["content"] += "\n" + fila["mensaje"]
        else:
            mensajes.append({"role": rol, "content": fila["mensaje"]})
    # la API exige que el primer mensaje sea del usuario
    while mensajes and mensajes[0]["role"] != "user":
        mensajes.pop(0)
    return mensajes


def responder(client, session_id: str, texto_cliente: str) -> str:
    """
    Flujo completo de un turno de chat:
    guarda el mensaje, llama a Claude (con historial y herramientas),
    ejecuta herramientas si hace falta, guarda y devuelve la respuesta.
    """
    texto_cliente = texto_cliente.strip()[:MAX_MENSAJE]
    db.guardar_mensaje(session_id, "cliente", texto_cliente)

    mensajes = _a_mensajes_api(db.obtener_historial(session_id, limite=20))
    sistema = construir_prompt_sistema(db.obtener_catalogo())

    texto_final = ""
    for _ in range(MAX_VUELTAS_TOOL):
        resp = client.messages.create(
            model=MODELO,
            max_tokens=MAX_TOKENS,
            system=sistema,
            tools=HERRAMIENTAS,
            messages=mensajes,
        )
        texto_final = "".join(b.text for b in resp.content if b.type == "text").strip()

        if resp.stop_reason != "tool_use":
            break

        # Claude pidió usar una herramienta: la ejecutamos y le devolvemos el resultado
        mensajes.append({"role": "assistant", "content": resp.content})
        resultados = []
        for b in resp.content:
            if b.type == "tool_use":
                if b.name == "registrar_cotizacion":
                    salida = ejecutar_registrar_cotizacion(session_id, b.input)
                else:
                    salida = {"ok": False, "error": "Herramienta desconocida."}
                resultados.append({
                    "type": "tool_result",
                    "tool_use_id": b.id,
                    "content": json.dumps(salida, ensure_ascii=False),
                })
        mensajes.append({"role": "user", "content": resultados})

    if not texto_final:
        texto_final = "Lo siento, no pude generar una respuesta. ¿Puedes intentar de nuevo?"

    db.guardar_mensaje(session_id, "bot", texto_final)
    return texto_final
