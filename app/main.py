"""Web service de registro de estudiantes (FastAPI)."""
from fastapi import Depends, FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from . import recaptcha
from .config import settings
from .database import Base, engine, get_db
from .models import Estudiante
from .schemas import CARRERAS, GENEROS, EstudianteCreate, EstudianteOut

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="API Registro de Estudiantes",
    version="1.0.0",
    description="Web service para registrar y consultar estudiantes.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


def _error(codigo: int, mensaje: str, errores: list[dict] | None = None) -> JSONResponse:
    return JSONResponse(status_code=codigo, content={"detail": mensaje, "errores": errores or []})


@app.exception_handler(RequestValidationError)
async def manejar_validacion(_: Request, exc: RequestValidationError):
    """Devuelve los errores de validación en español y por campo."""
    errores = []
    for err in exc.errors():
        campo = str(err["loc"][-1]) if err.get("loc") else "body"
        if err["type"] == "missing":
            mensaje = "Este campo es requerido"
        elif err["type"] == "value_error":
            mensaje = err["msg"].removeprefix("Value error, ")
        else:
            mensaje = "Valor inválido"
        errores.append({"campo": campo, "mensaje": mensaje})
    return _error(status.HTTP_422_UNPROCESSABLE_ENTITY, "Datos inválidos", errores)


# ---------------------------------------------------------------- API

@app.get("/api/health", tags=["Sistema"])
def health():
    return {"status": "ok"}


@app.get("/api/config", tags=["Sistema"])
def config_publica():
    """Configuración pública que necesita el frontend (solo la site key, nunca la secreta)."""
    return {"recaptchaSiteKey": settings.RECAPTCHA_SITE_KEY}


@app.get("/api/carreras", tags=["Catálogos"])
def listar_carreras():
    return CARRERAS


@app.get("/api/generos", tags=["Catálogos"])
def listar_generos():
    return GENEROS


@app.post(
    "/api/estudiantes",
    response_model=EstudianteOut,
    status_code=status.HTTP_201_CREATED,
    tags=["Estudiantes"],
    responses={
        400: {"description": "reCAPTCHA inválido"},
        409: {"description": "Carné o correo duplicado"},
        422: {"description": "Datos inválidos"},
    },
)
async def registrar_estudiante(datos: EstudianteCreate, request: Request, db: Session = Depends(get_db)):
    # 1) Verificar reCAPTCHA en el servidor (el frontend no es confiable)
    ip = request.client.host if request.client else None
    try:
        valido = await recaptcha.verificar_recaptcha(datos.recaptcha_token, ip)
    except recaptcha.RecaptchaNoDisponible:
        return _error(503, "No se pudo verificar el reCAPTCHA. Intente de nuevo.")
    if not valido:
        return _error(400, "Verificación reCAPTCHA inválida o expirada",
                      [{"campo": "recaptcha_token", "mensaje": "Vuelva a marcar la casilla 'No soy un robot'"}])

    # 2) Duplicados (mensaje claro por campo)
    errores = []
    if db.scalar(select(Estudiante.id).where(Estudiante.carne == datos.carne)):
        errores.append({"campo": "carne", "mensaje": "Ya existe un estudiante con ese carné"})
    if db.scalar(select(Estudiante.id).where(func.lower(Estudiante.correo) == datos.correo)):
        errores.append({"campo": "correo", "mensaje": "Ya existe un estudiante con ese correo"})
    if errores:
        return _error(409, "Registro duplicado", errores)

    # 3) Guardar
    estudiante = Estudiante(**datos.model_dump(exclude={"recaptcha_token"}))
    db.add(estudiante)
    try:
        db.commit()
    except IntegrityError:  # carrera de dos peticiones simultáneas
        db.rollback()
        return _error(409, "Registro duplicado (carné o correo)")
    db.refresh(estudiante)
    return estudiante


@app.get("/api/estudiantes", response_model=list[EstudianteOut], tags=["Estudiantes"])
def listar_estudiantes(q: str | None = None, db: Session = Depends(get_db)):
    """Lista todos los estudiantes (más recientes primero). `q` filtra opcionalmente."""
    consulta = select(Estudiante).order_by(Estudiante.fecha_registro.desc(), Estudiante.id.desc())
    if q and q.strip():
        patron = f"%{q.strip()}%"
        consulta = consulta.where(or_(
            Estudiante.carne.ilike(patron), Estudiante.nombres.ilike(patron),
            Estudiante.apellidos.ilike(patron), Estudiante.correo.ilike(patron),
            Estudiante.carrera.ilike(patron), Estudiante.telefono.ilike(patron),
            Estudiante.genero.ilike(patron),
        ))
    return db.scalars(consulta).all()


# ---------------------------------------------------------- Frontend
# Se monta al final para que no tape las rutas /api ni /docs.
app.mount("/", StaticFiles(directory=settings.FRONTEND_DIR, html=True), name="frontend")
