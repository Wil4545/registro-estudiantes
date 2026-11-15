"""Pruebas del web service. Ejecutar con:  python -m pytest -v"""
import os
from datetime import date

os.environ["DATABASE_URL"] = "sqlite:///./test_estudiantes.db"

import pytest
from fastapi.testclient import TestClient

from app import recaptcha
from app.database import Base, engine
from app.main import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def limpiar_bd(monkeypatch):
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    async def falso(token, ip=None):  # no llamar a Google en las pruebas
        return token == "ok"
    monkeypatch.setattr(recaptcha, "verificar_recaptcha", falso)
    yield


def hace(anios: int, dias: int = 0) -> str:
    h = date.today()
    try:
        d = h.replace(year=h.year - anios)
    except ValueError:  # 29 de febrero
        d = h.replace(year=h.year - anios, day=28)
    return date.fromordinal(d.toordinal() + dias).isoformat()


def valido(**cambios):
    datos = {
        "carne": "2026ab01", "nombres": "José  Luis", "apellidos": "Pérez Núñez",
        "correo": "Jose@Correo.com", "carrera": "Ingeniería en Sistemas",
        "telefono": "5555-1234", "fecha_nacimiento": hace(20), "genero": "Masculino",
        "recaptcha_token": "ok",
    }
    datos.update(cambios)
    return datos


def campos_error(r):
    return {e["campo"] for e in r.json()["errores"]}


def test_registro_y_consulta():
    r = client.post("/api/estudiantes", json=valido())
    assert r.status_code == 201, r.text
    e = r.json()
    assert e["carne"] == "2026AB01"
    assert e["nombres"] == "José Luis"
    assert e["correo"] == "jose@correo.com"
    lista = client.get("/api/estudiantes").json()
    assert len(lista) == 1 and lista[0]["id"] == e["id"]
    assert client.get("/api/estudiantes?q=perez").status_code == 200


def test_todos_requeridos():
    r = client.post("/api/estudiantes", json={})
    assert r.status_code == 422
    assert campos_error(r) == {"carne", "nombres", "apellidos", "correo", "carrera",
                               "telefono", "fecha_nacimiento", "genero", "recaptcha_token"}


@pytest.mark.parametrize("campo,valor", [
    ("carne", "1234567"), ("carne", "2026-0001"), ("carne", "2026 0001"),
    ("nombres", "Juan2"), ("apellidos", "López!"), ("nombres", "   "),
    ("correo", "malcorreo"), ("correo", "a@b"),
    ("carrera", "Medicina"),
    ("telefono", "55551234"), ("telefono", "555-51234"), ("telefono", "5555-123a"),
    ("fecha_nacimiento", "2050-01-01"), ("fecha_nacimiento", "no-fecha"),
    ("genero", "X"),
])
def test_validaciones(campo, valor):
    r = client.post("/api/estudiantes", json=valido(**{campo: valor}))
    assert r.status_code == 422
    assert campo in campos_error(r)


def test_edad_limite():
    assert client.post("/api/estudiantes", json=valido(fecha_nacimiento=hace(16, 1))).status_code == 422
    assert client.post("/api/estudiantes", json=valido(fecha_nacimiento=hace(16))).status_code == 201


def test_recaptcha_invalido():
    r = client.post("/api/estudiantes", json=valido(recaptcha_token="falso"))
    assert r.status_code == 400


def test_duplicados():
    assert client.post("/api/estudiantes", json=valido()).status_code == 201
    r = client.post("/api/estudiantes", json=valido(carne="2026AB01", correo="otro@correo.com"))
    assert r.status_code == 409 and campos_error(r) == {"carne"}
    r = client.post("/api/estudiantes", json=valido(carne="20269999", correo="JOSE@correo.com"))
    assert r.status_code == 409 and campos_error(r) == {"correo"}


def test_frontend_y_config():
    assert client.get("/").status_code == 200
    assert client.get("/consulta.html").status_code == 200
    assert "recaptchaSiteKey" in client.get("/api/config").json()
    assert len(client.get("/api/carreras").json()) == 6
