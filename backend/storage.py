import logging
import uuid
import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL    = os.getenv("SUPABASE_URL")
SUPABASE_KEY    = os.getenv("SUPABASE_KEY")
SUPABASE_BUCKET = os.getenv("SUPABASE_BUCKET")

EXTENSIONES_PERMITIDAS = {'png', 'jpg', 'jpeg', 'webp'}

logger = logging.getLogger(__name__)

_supabase = None

def _get_client():
    global _supabase
    if _supabase is None:
        if not SUPABASE_URL or not SUPABASE_KEY:
            raise RuntimeError("Supabase no esta configurado. Revisa el archivo .env")
        _supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    return _supabase


def extension_valida(filename: str) -> bool:
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in EXTENSIONES_PERMITIDAS


def subir_imagen(archivo) -> str | None:
    
    if not archivo or not archivo.filename:
        return None

    if not extension_valida(archivo.filename):
        return None

    try:
        client = _get_client()
        extension = archivo.filename.rsplit('.', 1)[1].lower()
        nombre_archivo = f"{uuid.uuid4().hex}.{extension}"
        contenido = archivo.read()
        content_type = archivo.content_type or 'image/jpeg'

        client.storage.from_(SUPABASE_BUCKET).upload(
            path=nombre_archivo,
            file=contenido,
            file_options={"content-type": content_type}
        )

        url = client.storage.from_(SUPABASE_BUCKET).get_public_url(nombre_archivo)
        return url

    except Exception as e:
        logger.error(f"Error al subir imagen: {e}")
        return None