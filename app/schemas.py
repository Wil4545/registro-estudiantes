"""Esquemas Pydantic: validación del lado del servidor (espejo de la validación en JavaScript)."""
import re
from datetime import date, datetime

from email_validator import EmailNotValidError, validate_email
from pydantic import BaseModel, ConfigDict, field_validator

CARRERAS = [
    "Ingeniería en Sistemas",
    "Ingeniería Industrial",
    "Administración de Empresas",
    "Contaduría Pública",
    "Psicología",
    "Ingeniería Civil",
]
GENEROS = ["Masculino", "Femenino", "Otro"]
EDAD_MINIMA = 16

RE_CARNE = re.compile(r"^[A-Za-z0-9]+$")
RE_NOMBRE = re.compile(r"^[A-Za-zÁÉÍÓÚáéíóúÑñÜü ]+$")
RE_TELEFONO = re.compile(r"^\d{4}-\d{4}$")


def calcular_edad(nacimiento: date, hoy: date | None = None) -> int:
    hoy = hoy or date.today()
    return hoy.year - nacimiento.year - ((hoy.month, hoy.day) < (nacimiento.month, nacimiento.day))


def _texto(v, campo: str) -> str:
    if v is None or (isinstance(v, str) and not v.strip()):
        raise ValueError(f"{campo} es requerido")
    if not isinstance(v, str):
        raise ValueError(f"{campo} debe ser texto")
    return v.strip()


class EstudianteCreate(BaseModel):
    carne: str
    nombres: str
    apellidos: str
    correo: str
    carrera: str
    telefono: str
    fecha_nacimiento: date
    genero: str
    recaptcha_token: str

    @field_validator("carne", mode="before")
    @classmethod
    def validar_carne(cls, v):
        v = _texto(v, "El carné")
        if not RE_CARNE.fullmatch(v):
            raise ValueError("El carné solo admite letras y números (sin espacios ni símbolos)")
        if len(v) < 8:
            raise ValueError("El carné debe tener al menos 8 caracteres")
        if len(v) > 20:
            raise ValueError("El carné no puede tener más de 20 caracteres")
        return v.upper()

    @field_validator("nombres", "apellidos", mode="before")
    @classmethod
    def validar_nombre(cls, v, info):
        etiqueta = "Los nombres" if info.field_name == "nombres" else "Los apellidos"
        v = " ".join(_texto(v, etiqueta).split())  # colapsa espacios repetidos
        if not RE_NOMBRE.fullmatch(v):
            raise ValueError(f"{etiqueta} solo admiten letras y espacios")
        if len(v) > 100:
            raise ValueError(f"{etiqueta} no pueden tener más de 100 caracteres")
        return v

    @field_validator("correo", mode="before")
    @classmethod
    def validar_correo(cls, v):
        v = _texto(v, "El correo")
        try:
            return validate_email(v, check_deliverability=False).normalized.lower()
        except EmailNotValidError:
            raise ValueError("El correo no tiene un formato válido (ej. usuario@dominio.com)")

    @field_validator("carrera", mode="before")
    @classmethod
    def validar_carrera(cls, v):
        v = _texto(v, "La carrera")
        if v not in CARRERAS:
            raise ValueError("Seleccione una carrera del catálogo")
        return v

    @field_validator("telefono", mode="before")
    @classmethod
    def validar_telefono(cls, v):
        v = _texto(v, "El teléfono")
        if not RE_TELEFONO.fullmatch(v):
            raise ValueError("El teléfono debe tener el formato ####-#### (ej. 5555-1234)")
        return v

    @field_validator("fecha_nacimiento", mode="before")
    @classmethod
    def validar_fecha(cls, v):
        if isinstance(v, date):
            nac = v
        else:
            v = _texto(v, "La fecha de nacimiento")
            try:
                nac = date.fromisoformat(v)
            except ValueError:
                raise ValueError("La fecha de nacimiento no es válida (formato AAAA-MM-DD)")
        if nac > date.today():
            raise ValueError("La fecha de nacimiento no puede estar en el futuro")
        if nac.year < 1900:
            raise ValueError("La fecha de nacimiento no es válida")
        if calcular_edad(nac) < EDAD_MINIMA:
            raise ValueError(f"El estudiante debe tener al menos {EDAD_MINIMA} años")
        return nac

    @field_validator("genero", mode="before")
    @classmethod
    def validar_genero(cls, v):
        v = _texto(v, "El género")
        if v not in GENEROS:
            raise ValueError("Seleccione un género válido: Masculino, Femenino u Otro")
        return v

    @field_validator("recaptcha_token", mode="before")
    @classmethod
    def validar_token(cls, v):
        return _texto(v, "La verificación reCAPTCHA")


class EstudianteOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    carne: str
    nombres: str
    apellidos: str
    correo: str
    carrera: str
    telefono: str
    fecha_nacimiento: date
    genero: str
    fecha_registro: datetime
