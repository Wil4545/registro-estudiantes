(() => {
  "use strict";

  const API = window.APP_CONFIG.API_BASE;
  const EDAD_MINIMA = 16;
  const CARRERAS_RESPALDO = [
    "Ingeniería en Sistemas", "Ingeniería Industrial", "Administración de Empresas",
    "Contaduría Pública", "Psicología", "Ingeniería Civil",
  ];

  const form = document.getElementById("formRegistro");
  const btnEnviar = document.getElementById("btnEnviar");
  const alerta = document.getElementById("alerta");
  const selCarrera = document.getElementById("carrera");
  const inpFecha = document.getElementById("fecha_nacimiento");
  const inpTel = document.getElementById("telefono");

  let captchaToken = "";
  let captchaId = null;
  let enviando = false;
  const tocados = new Set();

  // ------------------------------------------------------------ Reglas
  const RE_CARNE = /^[A-Za-z0-9]+$/;
  const RE_NOMBRE = /^[A-Za-zÁÉÍÓÚáéíóúÑñÜü ]+$/;
  const RE_CORREO = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/;
  const RE_TEL = /^\d{4}-\d{4}$/;

  function edad(isoFecha) {
    const [a, m, d] = isoFecha.split("-").map(Number);
    const hoy = new Date();
    let e = hoy.getFullYear() - a;
    if (hoy.getMonth() + 1 < m || (hoy.getMonth() + 1 === m && hoy.getDate() < d)) e--;
    return e;
  }

  const reglas = {
    carne(v) {
      v = v.trim();
      if (!v) return "El carné es requerido";
      if (!RE_CARNE.test(v)) return "Solo letras y números (sin espacios ni símbolos)";
      if (v.length < 8) return `Mínimo 8 caracteres (lleva ${v.length})`;
      return "";
    },
    nombres(v) {
      v = v.trim();
      if (!v) return "Los nombres son requeridos";
      if (!RE_NOMBRE.test(v)) return "Solo letras y espacios";
      return "";
    },
    apellidos(v) {
      v = v.trim();
      if (!v) return "Los apellidos son requeridos";
      if (!RE_NOMBRE.test(v)) return "Solo letras y espacios";
      return "";
    },
    correo(v) {
      v = v.trim();
      if (!v) return "El correo es requerido";
      if (!RE_CORREO.test(v)) return "Formato inválido (ej. usuario@dominio.com)";
      return "";
    },
    carrera(v) {
      if (!v) return "Seleccione una carrera";
      return "";
    },
    telefono(v) {
      if (!v) return "El teléfono es requerido";
      if (!RE_TEL.test(v)) return "Formato requerido: ####-####";
      return "";
    },
    fecha_nacimiento(v) {
      if (!v) return "La fecha de nacimiento es requerida";
      if (!/^\d{4}-\d{2}-\d{2}$/.test(v)) return "Fecha inválida";
      if (new Date(v + "T00:00:00") > new Date()) return "No puede ser una fecha futura";
      if (Number(v.slice(0, 4)) < 1900) return "Fecha inválida";
      if (edad(v) < EDAD_MINIMA) return `Debe tener al menos ${EDAD_MINIMA} años`;
      return "";
    },
    genero() {
      return form.querySelector('input[name="genero"]:checked') ? "" : "Seleccione un género";
    },
  };

  const valor = (campo) =>
    campo === "genero"
      ? (form.querySelector('input[name="genero"]:checked') || {}).value || ""
      : form.elements[campo].value;

  function mostrarError(campo, msg) {
    const span = document.getElementById(`error-${campo}`);
    if (span) span.textContent = msg;
    const el = campo === "genero" ? null : form.elements[campo];
    if (el) {
      el.classList.toggle("invalido", !!msg);
      el.classList.toggle("valido", !msg);
      el.setAttribute("aria-invalid", msg ? "true" : "false");
    }
  }

  function validarCampo(campo, forzarMostrar = false) {
    const msg = reglas[campo](valor(campo));
    if (forzarMostrar || tocados.has(campo)) mostrarError(campo, msg);
    return !msg;
  }

  function formularioValido() {
    return Object.keys(reglas).every((c) => !reglas[c](valor(c)));
  }

  function actualizarBoton() {
    btnEnviar.disabled = enviando || !formularioValido() || !captchaToken;
  }

  // ------------------------------------------------------------ Eventos
  Object.keys(reglas).forEach((campo) => {
    const elementos = campo === "genero"
      ? form.querySelectorAll('input[name="genero"]')
      : [form.elements[campo]];
    elementos.forEach((el) => {
      el.addEventListener("input", () => { tocados.add(campo); validarCampo(campo); actualizarBoton(); });
      el.addEventListener("change", () => { tocados.add(campo); validarCampo(campo); actualizarBoton(); });
      el.addEventListener("blur", () => { tocados.add(campo); validarCampo(campo); });
    });
  });

  // Máscara de teléfono: 55551234 -> 5555-1234
  inpTel.addEventListener("input", () => {
    const d = inpTel.value.replace(/\D/g, "").slice(0, 8);
    inpTel.value = d.length > 4 ? `${d.slice(0, 4)}-${d.slice(4)}` : d;
  }, true);

  // Fecha máxima permitida = hoy - 16 años
  (() => {
    const h = new Date();
    const max = new Date(h.getFullYear() - EDAD_MINIMA, h.getMonth(), h.getDate());
    const pad = (n) => String(n).padStart(2, "0");
    inpFecha.max = `${max.getFullYear()}-${pad(max.getMonth() + 1)}-${pad(max.getDate())}`;
    inpFecha.min = "1900-01-01";
  })();

  form.addEventListener("reset", () => {
    setTimeout(() => {
      tocados.clear();
      Object.keys(reglas).forEach((c) => mostrarError(c, ""));
      form.querySelectorAll(".valido,.invalido").forEach((el) => el.classList.remove("valido", "invalido"));
      ocultarAlerta();
      actualizarBoton();
    });
  });

  // ------------------------------------------------------------ Alertas
  function mostrarAlerta(tipo, html) {
    alerta.className = `alerta ${tipo}`;
    alerta.innerHTML = html;
    alerta.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }
  function ocultarAlerta() { alerta.className = "alerta oculto"; alerta.textContent = ""; }

  // ------------------------------------------------------------ Envío POST
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    Object.keys(reglas).forEach((c) => { tocados.add(c); validarCampo(c, true); });
    if (!formularioValido() || !captchaToken) { actualizarBoton(); return; }

    const payload = {
      carne: valor("carne").trim(),
      nombres: valor("nombres").trim(),
      apellidos: valor("apellidos").trim(),
      correo: valor("correo").trim(),
      carrera: valor("carrera"),
      telefono: valor("telefono"),
      fecha_nacimiento: valor("fecha_nacimiento"),
      genero: valor("genero"),
      recaptcha_token: captchaToken,
    };

    enviando = true;
    btnEnviar.textContent = "Enviando...";
    actualizarBoton();
    ocultarAlerta();

    try {
      const resp = await fetch(`${API}/api/estudiantes`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const data = await resp.json().catch(() => ({}));

      if (resp.status === 201) {
        mostrarAlerta("exito",
          `Estudiante <strong>${escapar(data.nombres)} ${escapar(data.apellidos)}</strong> ` +
          `(carné ${escapar(data.carne)}) registrado correctamente. ` +
          `<a href="consulta.html">Ver listado</a>`);
        form.reset();
      } else {
        (data.errores || []).forEach((er) => mostrarError(er.campo, er.mensaje));
        mostrarAlerta("error", escapar(data.detail || `Error ${resp.status} al registrar`));
      }
    } catch {
      mostrarAlerta("error", "No se pudo conectar con el servidor. Verifique su conexión.");
    } finally {
      enviando = false;
      btnEnviar.textContent = "Registrar estudiante";
      reiniciarCaptcha(); // un token de reCAPTCHA solo sirve una vez
    }
  });

  function escapar(t) {
    return String(t ?? "").replace(/[&<>"']/g, (c) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  }

  // ------------------------------------------------------------ reCAPTCHA
  function reiniciarCaptcha() {
    captchaToken = "";
    if (window.grecaptcha && captchaId !== null) grecaptcha.reset(captchaId);
    actualizarBoton();
  }

  window.onRecaptchaLoad = function () {
    captchaId = grecaptcha.render("recaptcha", {
      sitekey: window.__RECAPTCHA_SITE_KEY,
      callback: (token) => { captchaToken = token; mostrarError("recaptcha_token", ""); actualizarBoton(); },
      "expired-callback": () => {
        captchaToken = "";
        mostrarError("recaptcha_token", "La verificación expiró, márquela de nuevo");
        actualizarBoton();
      },
      "error-callback": () => {
        captchaToken = "";
        mostrarError("recaptcha_token", "Error al cargar reCAPTCHA. Recargue la página.");
        actualizarBoton();
      },
    });
  };

  // ------------------------------------------------------------ Inicio
  async function iniciar() {
    // Catálogo de carreras
    let carreras = CARRERAS_RESPALDO;
    try {
      const r = await fetch(`${API}/api/carreras`);
      if (r.ok) carreras = await r.json();
    } catch { /* se usa el respaldo */ }
    carreras.forEach((c) => selCarrera.add(new Option(c, c)));

    // Site key de reCAPTCHA desde el servidor
    try {
      const r = await fetch(`${API}/api/config`);
      const cfg = await r.json();
      window.__RECAPTCHA_SITE_KEY = cfg.recaptchaSiteKey;
      const s = document.createElement("script");
      s.src = "https://www.google.com/recaptcha/api.js?onload=onRecaptchaLoad&render=explicit&hl=es";
      s.async = true; s.defer = true;
      document.head.appendChild(s);
    } catch {
      mostrarAlerta("error", "No se pudo conectar con el servidor para cargar el reCAPTCHA.");
    }
    actualizarBoton();
  }

  iniciar();
})();
