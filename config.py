import os

from dotenv import load_dotenv

load_dotenv()  # lee el archivo .env de la raíz del repo y lo carga en os.environ


def required(name):
    """Devuelve la variable de entorno o falla con un mensaje claro si no existe."""
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"Falta la variable {name} en el archivo .env")
    return value


# Servidor gRPC
SERVER_HOST = required("SERVER_HOST")
SERVER_PORT = required("SERVER_PORT")

# Base de datos
DB_HOST = required("DB_HOST")
DB_PORT = required("DB_PORT")
DB_NAME = required("DB_NAME")
DB_USER = required("DB_USER")
DB_PASSWORD = required("DB_PASSWORD")

# Sesiones
SESSION_MINUTES = int(required("SESSION_MINUTES"))
