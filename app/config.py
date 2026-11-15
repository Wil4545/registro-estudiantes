"""Configuración leída desde variables de entorno (.env en local, panel de Render en la nube)."""
import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

# Claves de PRUEBA públicas de Google: el widget siempre pasa y muestra un aviso.
# Reemplácelas por las suyas en producción (ver README).
_TEST_SITE_KEY = "6LeIxAcTAAAAAJcZVRqyHh71UMIEGNQ_MXjiZKhI"
_TEST_SECRET_KEY = "6LeIxAcTAAAAAGG-vFI1TnRWxMZNFuojJ4WifJWe"


class Settings:
    DATABASE_URL: str = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'estudiantes.db'}")
    RECAPTCHA_SITE_KEY: str = os.getenv("RECAPTCHA_SITE_KEY", _TEST_SITE_KEY)
    RECAPTCHA_SECRET_KEY: str = os.getenv("RECAPTCHA_SECRET_KEY", _TEST_SECRET_KEY)
    CORS_ORIGINS: list[str] = [
        o.strip() for o in os.getenv("CORS_ORIGINS", "*").split(",") if o.strip()
    ]
    FRONTEND_DIR: Path = BASE_DIR / "frontend"


settings = Settings()
