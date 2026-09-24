# GECTAM Bot — Proyecto de estadía

Estructura inicial del proyecto (Paso 1 y 2 de nuestro plan).

```
gectam-bot/
├── backend/
│   ├── main.py           # API FastAPI con el endpoint /chat (ya conectado a Claude)
│   ├── requirements.txt
│   ├── .env.example       # Copia esto a .env y pon tu API key real
│   └── .gitignore
└── frontend/
    └── widget.html        # Widget de chat (HTML/JS puro)
```

## Antes de correrlo: configura tu API key de Claude

1. Ve a [console.anthropic.com](https://console.anthropic.com), crea una cuenta y genera una API key.
2. En la carpeta `backend`, copia `.env.example` a un archivo nuevo llamado `.env`.
3. Abre `.env` y reemplaza `tu_api_key_aqui` con tu key real:
   ```
   ANTHROPIC_API_KEY=sk-ant-xxxxxxxx...
   ```
4. Guarda. El `.gitignore` ya está configurado para que `.env` **nunca** se suba a GitHub (no compartas tu key).

## Cómo correrlo en tu máquina

### 1. Backend

```bash
cd backend
python -m venv venv

# Activar el entorno virtual
# En Windows:
venv\Scripts\activate
# En Mac/Linux:
source venv/bin/activate

pip install -r requirements.txt
uvicorn main:app --reload
```

Esto levanta el backend en `http://127.0.0.1:8000`.
Puedes abrir esa URL en el navegador y deberías ver `{"status":"ok",...}`.

También puedes ir a `http://127.0.0.1:8000/docs` para ver la documentación
automática de FastAPI y probar el endpoint `/chat` sin necesidad del widget.

### 2. Frontend (widget)

Simplemente abre el archivo `frontend/widget.html` con doble clic en tu
navegador (con el backend corriendo). Escribe un mensaje y deberías ver una
respuesta de prueba (todavía no es IA real, eso viene en el siguiente paso).

## Siguientes pasos (según nuestro plan)

- [x] Paso 1: Estructura del proyecto + entorno
- [x] Paso 2: Backend mínimo + widget de chat
- [x] Paso 3: Conectar la API de Claude al backend
- [ ] Paso 4: Base de datos SQLite (catálogo y cotizaciones)
- [ ] Paso 5: Panel administrativo en Streamlit
- [ ] Paso 6: Subir a Render/Railway
- [ ] Paso 7: Reemplazar datos genéricos por el catálogo real de GECTAM

## Nota sobre el Paso 3

El bot ahora sí responde con IA real (Claude), pero **todavía no recuerda
la conversación anterior** — cada mensaje se manda solo, sin historial.
Eso lo resolvemos en el Paso 4, cuando conectemos la base de datos y
guardemos el historial de cada sesión de chat.
