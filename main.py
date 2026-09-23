"""
API de eliminación de fondo para fotos de producto.
Ajustada para caber en el plan FREE de Render (512 MB de RAM).

Cambios respecto a la versión anterior:
- Modelo cambiado a "u2netp" (mucho más ligero en RAM que isnet-general-use).
- alpha_matting desactivado por defecto (consume RAM extra); puedes activarlo
  si luego subes a un plan con más memoria.

Endpoint:
    POST /quitar-fondo
    Body: form-data con un campo "archivo" = tu imagen (jpg, png, webp...)
    Respuesta: el PNG sin fondo, nombrado "<nombre-original>-no-bg.png"
"""

import io
from pathlib import Path

from fastapi import FastAPI, UploadFile, File
from fastapi.responses import StreamingResponse
from rembg import remove, new_session

app = FastAPI(title="Quitar fondo de producto")

MODELO = "u2netp"
_session = new_session(MODELO)


@app.get("/")
def salud():
    return {"estado": "ok", "mensaje": "API de eliminación de fondo activa", "modelo": MODELO}


@app.post("/quitar-fondo")
async def quitar_fondo(archivo: UploadFile = File(...)):
    datos_entrada = await archivo.read()

    datos_salida = remove(
        datos_entrada,
        session=_session,
        alpha_matting=False,
    )

    nombre_original = Path(archivo.filename or "imagen").stem
    nombre_salida = f"{nombre_original}-no-bg.png"

    return StreamingResponse(
        io.BytesIO(datos_salida),
        media_type="image/png",
        headers={"Content-Disposition": f'attachment; filename="{nombre_salida}"'},
    )
