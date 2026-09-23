"""
API de eliminación de fondo para fotos de producto.
Pensada para desplegar GRATIS en Render.com (Web Service, plan Free).

Endpoint:
    POST /quitar-fondo
    Body: form-data con un campo "archivo" = tu imagen (jpg, png, webp...)
    Respuesta: el PNG sin fondo, con Content-Disposition indicando
               "<nombre-original>-no-bg.png"

Cómo desplegar en Render:
1. Sube estos archivos (main.py, requirements.txt) a un repo de GitHub.
2. Ve a https://dashboard.render.com -> New -> Web Service.
3. Conecta ese repo de GitHub.
4. Configura:
     Runtime: Python 3
     Build Command:  pip install -r requirements.txt
     Start Command:  uvicorn main:app --host 0.0.0.0 --port $PORT
     Plan: Free
5. Deploy. En unos minutos te da una URL pública tipo:
     https://tu-servicio.onrender.com

Cómo probarlo desde tu terminal (una vez desplegado):
    curl -X POST https://tu-servicio.onrender.com/quitar-fondo \
         -F "archivo=@taza-cafe.jpg" \
         -o taza-cafe-no-bg.png
"""

import io
from pathlib import Path

from fastapi import FastAPI, UploadFile, File
from fastapi.responses import StreamingResponse
from rembg import remove, new_session

app = FastAPI(title="Quitar fondo de producto")

MODELO = "isnet-general-use"
_session = new_session(MODELO)


@app.get("/")
def salud():
    return {"estado": "ok", "mensaje": "API de eliminación de fondo activa"}


@app.post("/quitar-fondo")
async def quitar_fondo(archivo: UploadFile = File(...)):
    datos_entrada = await archivo.read()

    datos_salida = remove(
        datos_entrada,
        session=_session,
        alpha_matting=True,
        alpha_matting_foreground_threshold=240,
        alpha_matting_background_threshold=10,
        alpha_matting_erode_size=10,
    )

    nombre_original = Path(archivo.filename or "imagen").stem
    nombre_salida = f"{nombre_original}-no-bg.png"

    return StreamingResponse(
        io.BytesIO(datos_salida),
        media_type="image/png",
        headers={"Content-Disposition": f'attachment; filename="{nombre_salida}"'},
    )
