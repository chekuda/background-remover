"""
API de eliminación de fondo para fotos de producto.
Versión con redimensionado de seguridad para no reventar la RAM del
plan free de Render (512 MB) con imágenes grandes (frecuente en WebP).
"""

import io
import gc
from pathlib import Path

import onnxruntime as ort
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse
from PIL import Image, UnidentifiedImageError
from rembg import remove
from rembg.session_factory import new_session

MODELO = "u2netp"

# Lado máximo permitido (px). Si la imagen es más grande, se reduce
# antes de procesar. 1600px es más que suficiente para fotos de
# producto en ecommerce/Wix, y evita picos de RAM enormes.
LADO_MAXIMO = 1600

sess_opts = ort.SessionOptions()
sess_opts.enable_cpu_mem_arena = False
sess_opts.enable_mem_pattern = False
sess_opts.enable_mem_reuse = False

_session = new_session(MODELO, sess_opts=sess_opts, providers=["CPUExecutionProvider"])

app = FastAPI(title="Quitar fondo de producto")


@app.get("/")
def salud():
    return {"estado": "ok", "mensaje": "API de eliminación de fondo activa", "modelo": MODELO}


@app.post("/quitar-fondo")
async def quitar_fondo(archivo: UploadFile = File(...)):
    datos_entrada = await archivo.read()

    if len(datos_entrada) > 15 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="La imagen supera los 15 MB, por favor comprímela antes de subirla.")

    try:
        imagen = Image.open(io.BytesIO(datos_entrada))
        if getattr(imagen, "is_animated", False):
            imagen.seek(0)
        imagen = imagen.convert("RGB")
    except UnidentifiedImageError:
        raise HTTPException(status_code=400, detail="El archivo no es una imagen válida o el formato no está soportado.")

    if max(imagen.size) > LADO_MAXIMO:
        imagen.thumbnail((LADO_MAXIMO, LADO_MAXIMO), Image.LANCZOS)

    buffer_normalizado = io.BytesIO()
    imagen.save(buffer_normalizado, format="PNG")
    buffer_normalizado.seek(0)
    bytes_normalizados = buffer_normalizado.read()

    del imagen, datos_entrada, buffer_normalizado
    gc.collect()

    try:
        datos_salida = remove(
            bytes_normalizados,
            session=_session,
            alpha_matting=False,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al procesar la imagen: {e}")

    nombre_original = Path(archivo.filename or "imagen").stem
    nombre_salida = f"{nombre_original}-no-bg.png"

    return StreamingResponse(
        io.BytesIO(datos_salida),
        media_type="image/png",
        headers={"Content-Disposition": f'attachment; filename="{nombre_salida}"'},
    )