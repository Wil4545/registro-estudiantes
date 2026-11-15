"""Verificación del token reCAPTCHA v2 contra los servidores de Google."""
import httpx

from .config import settings

VERIFY_URL = "https://www.google.com/recaptcha/api/siteverify"


class RecaptchaNoDisponible(Exception):
    """No se pudo contactar a Google para verificar."""


async def verificar_recaptcha(token: str, ip_cliente: str | None = None) -> bool:
    datos = {"secret": settings.RECAPTCHA_SECRET_KEY, "response": token}
    if ip_cliente:
        datos["remoteip"] = ip_cliente
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(VERIFY_URL, data=datos)
            resp.raise_for_status()
            return bool(resp.json().get("success"))
    except (httpx.HTTPError, ValueError) as exc:
        raise RecaptchaNoDisponible(str(exc)) from exc
