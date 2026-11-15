# Sistema de Registro de Estudiantes

Aplicación web con:

- **Formulario de registro** (`index.html`): validación en tiempo real, máscara de teléfono, reCAPTCHA v2 y botón de envío deshabilitado hasta que todo sea válido.
- **Web service en la nube** (FastAPI): recibe los datos por `POST /api/estudiantes`, verifica el reCAPTCHA con Google, vuelve a validar los datos y los guarda en PostgreSQL.
- **Ventana de consulta** (`consulta.html`): tabla con todas las columnas guardadas, buscador instantáneo y botón **Actualizar**.

---

## 1. Tecnologías

| Capa | Tecnología |
|---|---|
| Frontend | HTML5, CSS3, JavaScript (sin frameworks) |
| Backend / Web service | Python 3.12, FastAPI, Uvicorn |
| ORM y validación | SQLAlchemy 2, Pydantic 2, email-validator |
| Base de datos | SQLite (local) · PostgreSQL (nube) |
| Anti-bots | Google reCAPTCHA v2 ("No soy un robot"), verificado en el servidor |
| Hosting | Render (web service + PostgreSQL) |

## 2. Estructura del proyecto

```
registro-estudiantes/
├── app/
│   ├── main.py          # Endpoints del web service + sirve el frontend
│   ├── schemas.py       # Validaciones del servidor (Pydantic) y catálogo de carreras
│   ├── models.py        # Tabla "estudiantes" (SQLAlchemy)
│   ├── database.py      # Conexión (SQLite / PostgreSQL)
│   ├── recaptcha.py     # Verificación del token con Google
│   └── config.py        # Variables de entorno
├── frontend/
│   ├── index.html       # Formulario de registro
│   ├── consulta.html    # Tabla de consulta
│   ├── css/styles.css
│   └── js/
│       ├── config.js    # URL del web service (API_BASE)
│       ├── registro.js  # Validación, reCAPTCHA y envío POST
│       └── consulta.js  # Carga, búsqueda y actualización de la tabla
├── tests/test_api.py    # Pruebas automáticas (pytest)
├── requirements.txt
├── requirements-dev.txt
├── render.yaml          # Despliegue automático en Render
├── .env.example
└── .python-version
```

## 3. Levantar el proyecto en local (Windows)

> **Use Python 3.12.** Con Python 3.14 algunas dependencias (Pydantic) aún no tienen
> paquetes precompilados y la instalación falla. Descárguelo de python.org si es necesario.

```powershell
# 1. Entrar a la carpeta del proyecto
cd registro-estudiantes

# 2. Crear y activar el entorno virtual con Python 3.12
py -3.12 -m venv .venv
.venv\Scripts\activate

# 3. Instalar dependencias
python -m pip install --upgrade pip
pip install -r requirements-dev.txt

# 4. Crear el archivo de configuración
copy .env.example .env

# 5. Iniciar el servidor
python -m uvicorn app.main:app --reload
```

> Use `python -m uvicorn` (no solo `uvicorn`) para evitar el error
> "uvicorn no se reconoce como un comando" en Windows.

Abra en el navegador:

| URL | Qué es |
|---|---|
| http://127.0.0.1:8000/ | Formulario de registro |
| http://127.0.0.1:8000/consulta.html | Consulta de estudiantes |
| http://127.0.0.1:8000/docs | Documentación interactiva de la API (Swagger) |

En local se crea automáticamente el archivo `estudiantes.db` (SQLite). No hay que instalar nada más.

**Linux / macOS:** igual, cambiando la activación por `source .venv/bin/activate` y `copy` por `cp`.

### Ejecutar las pruebas

```powershell
python -m pytest -v
```

Las pruebas cubren: registro exitoso, campos requeridos, cada regla de validación, edad límite (16 años exactos), reCAPTCHA inválido y duplicados de carné/correo.

## 4. Configurar reCAPTCHA

El proyecto viene con las **claves de prueba oficiales de Google**: el widget aparece, siempre se aprueba y muestra el aviso rojo *"This reCAPTCHA is for testing purposes only"*. Sirven para desarrollar; para la entrega use sus propias claves:

1. Entre a https://www.google.com/recaptcha/admin/create con su cuenta de Google.
2. **Etiqueta:** `Registro Estudiantes`.
3. **Tipo:** reCAPTCHA **v2** → casilla **"No soy un robot"**.
4. **Dominios:** agregue `localhost`, `127.0.0.1` y el dominio de Render (ej. `registro-estudiantes.onrender.com`).
5. Copie la **clave del sitio** y la **clave secreta** en `.env` (local) o en las variables de entorno de Render:

```
RECAPTCHA_SITE_KEY=su_clave_del_sitio
RECAPTCHA_SECRET_KEY=su_clave_secreta
```

La clave secreta **nunca** llega al navegador: el frontend obtiene solo la clave del sitio desde `GET /api/config`, y la verificación del token la hace el servidor contra Google.

## 5. Desplegar en la nube (Render)

### Opción A — Blueprint (automático)

1. Suba el proyecto a un repositorio de GitHub (el `.gitignore` ya excluye `.env`, `.venv` y la base local).
2. En https://dashboard.render.com → **New** → **Blueprint** → elija el repositorio.
3. Render lee `render.yaml` y crea:
   - el web service `registro-estudiantes` (Python 3.12),
   - la base de datos PostgreSQL `registro-estudiantes-db`, conectada automáticamente mediante `DATABASE_URL`.
4. Le pedirá `RECAPTCHA_SITE_KEY` y `RECAPTCHA_SECRET_KEY`: pegue sus claves (o las de prueba de `.env.example`).
5. Al terminar, abra `https://<su-servicio>.onrender.com/`.

### Opción B — Manual

1. **New → PostgreSQL** (plan Free). Copie la *Internal Database URL*.
2. **New → Web Service** → conecte el repositorio y configure:
   - Runtime: `Python 3`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
3. En **Environment** agregue:

| Variable | Valor |
|---|---|
| `PYTHON_VERSION` | `3.12.7` |
| `DATABASE_URL` | URL de la base de datos del paso 1 |
| `RECAPTCHA_SITE_KEY` | su clave del sitio |
| `RECAPTCHA_SECRET_KEY` | su clave secreta |
| `CORS_ORIGINS` | `*` |

La tabla `estudiantes` se crea sola al arrancar el servicio.

**Notas del plan gratuito de Render:**
- El servicio se "duerme" tras 15 min sin uso; la primera petición después tarda ~30–60 s.
- La base de datos gratuita de Render vence a los 30 días. Si necesita más tiempo, cree una base gratuita en https://neon.tech y pegue su cadena de conexión en `DATABASE_URL` (el sistema acepta `postgres://` y `postgresql://`).

### Frontend en otro hosting (opcional)

Por defecto el mismo servicio de Render sirve el frontend. Si quiere publicar la carpeta `frontend/` en otro lado (Netlify, GitHub Pages), edite `frontend/js/config.js`:

```js
window.APP_CONFIG = { API_BASE: "https://registro-estudiantes.onrender.com" };
```

y en Render ponga `CORS_ORIGINS` con el dominio de ese frontend.

## 6. Documentación del web service

Base URL local: `http://127.0.0.1:8000` · Nube: `https://<su-servicio>.onrender.com`

| Método | Ruta | Descripción |
|---|---|---|
| **POST** | `/api/estudiantes` | Registra un estudiante |
| GET | `/api/estudiantes` | Lista todos (más recientes primero). Opcional `?q=texto` |
| GET | `/api/carreras` | Catálogo de carreras |
| GET | `/api/generos` | Catálogo de géneros |
| GET | `/api/config` | Clave pública de reCAPTCHA |
| GET | `/api/health` | Estado del servicio |

### POST `/api/estudiantes`

**Request** (`Content-Type: application/json`):

```json
{
  "carne": "20260001",
  "nombres": "Juan Carlos",
  "apellidos": "Pérez López",
  "correo": "juan.perez@correo.com",
  "carrera": "Ingeniería en Sistemas",
  "telefono": "5555-1234",
  "fecha_nacimiento": "2004-05-17",
  "genero": "Masculino",
  "recaptcha_token": "<token devuelto por el widget>"
}
```

**Respuestas:**

| Código | Significado | Cuerpo |
|---|---|---|
| `201` | Registrado | El estudiante guardado (con `id` y `fecha_registro`) |
| `400` | reCAPTCHA inválido o expirado | `{"detail": "...", "errores": [...]}` |
| `409` | Carné o correo ya registrado | `{"detail": "Registro duplicado", "errores": [{"campo": "carne", "mensaje": "..."}]}` |
| `422` | Datos inválidos | `{"detail": "Datos inválidos", "errores": [{"campo": "telefono", "mensaje": "El teléfono debe tener el formato ####-####..."}]}` |
| `503` | No se pudo contactar a Google | `{"detail": "..."}` |

**Ejemplo 201:**

```json
{
  "id": 1,
  "carne": "20260001",
  "nombres": "Juan Carlos",
  "apellidos": "Pérez López",
  "correo": "juan.perez@correo.com",
  "carrera": "Ingeniería en Sistemas",
  "telefono": "5555-1234",
  "fecha_nacimiento": "2004-05-17",
  "genero": "Masculino",
  "fecha_registro": "2026-11-15T15:30:12.345678+00:00"
}
```

**Probar desde PowerShell** (con las claves de prueba cualquier token es aceptado):

```powershell
$body = @{
  carne="20260001"; nombres="Juan Carlos"; apellidos="Pérez López"
  correo="juan.perez@correo.com"; carrera="Ingeniería en Sistemas"
  telefono="5555-1234"; fecha_nacimiento="2004-05-17"; genero="Masculino"
  recaptcha_token="prueba"
} | ConvertTo-Json
Invoke-RestMethod -Uri http://127.0.0.1:8000/api/estudiantes -Method Post `
  -ContentType "application/json; charset=utf-8" -Body ([Text.Encoding]::UTF8.GetBytes($body))
```

También puede probar todo desde **`/docs`** (Swagger).

## 7. Reglas de validación

Se aplican **dos veces**: en el navegador (JavaScript, para guiar al usuario) y en el servidor (Pydantic, porque el navegador se puede saltar).

| Campo | Tipo | Regla |
|---|---|---|
| Carné | text | Requerido, mínimo 8 caracteres (máx. 20), solo letras y números. Se guarda en mayúsculas y no se puede repetir. |
| Nombres | text | Requerido, solo letras (incluye tildes, ñ, ü) y espacios |
| Apellidos | text | Requerido, solo letras y espacios |
| Correo | email | Requerido, formato válido; no se puede repetir |
| Carrera | select | Requerido, debe ser una del catálogo |
| Teléfono | tel | Requerido, formato `####-####` (el guion se agrega solo al escribir) |
| Fecha de nacimiento | date | Requerido, no futura, edad mínima **16 años** cumplidos |
| Género | radio | Requerido: Masculino / Femenino / Otro |
| reCAPTCHA | — | Requerido; el servidor verifica el token con Google (un token sirve una sola vez) |

**Catálogo de carreras:** Ingeniería en Sistemas · Ingeniería Industrial · Administración de Empresas · Contaduría Pública · Psicología · Ingeniería Civil. Se edita en `app/schemas.py` (`CARRERAS`); el formulario lo carga desde `GET /api/carreras`.

**Botón de envío:** permanece deshabilitado hasta que los 8 campos sean válidos **y** la casilla de reCAPTCHA esté marcada. Si el reCAPTCHA expira, se vuelve a deshabilitar.

## 8. Ventana de consulta

- Muestra todas las columnas guardadas: ID, carné, nombres, apellidos, correo, carrera, teléfono, fecha de nacimiento, género y fecha de registro.
- **Buscador:** filtra al escribir en cualquier columna, sin distinguir mayúsculas ni tildes (`perez` encuentra `Pérez`).
- **Actualizar:** vuelve a consultar `GET /api/estudiantes` y muestra la hora de la última actualización.

## 9. Problemas comunes

| Problema | Solución |
|---|---|
| Error al instalar `pydantic-core` | Está usando Python 3.13/3.14. Cree el entorno con `py -3.12 -m venv .venv`. |
| `uvicorn` no se reconoce | Use `python -m uvicorn app.main:app --reload` con el entorno activado. |
| "ERROR para el propietario del sitio: Dominio no válido" | Agregue el dominio en la consola de reCAPTCHA (paso 4.4). |
| El botón nunca se habilita | Revise que todos los campos estén en verde y marque el reCAPTCHA. |
| La consulta tarda la primera vez en Render | El plan gratuito "despierta" el servicio; espere ~1 min. |
| `409 Registro duplicado` | Ese carné o correo ya existe. |
