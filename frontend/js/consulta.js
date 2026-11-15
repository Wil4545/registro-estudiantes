(() => {
  "use strict";

  const API = window.APP_CONFIG.API_BASE;
  const cuerpo = document.getElementById("cuerpo");
  const buscador = document.getElementById("buscador");
  const btnActualizar = document.getElementById("btnActualizar");
  const resumen = document.getElementById("resumen");
  const alerta = document.getElementById("alerta");
  const COLUMNAS = 10;

  let estudiantes = [];
  let ultimaCarga = null;

  const normalizar = (t) =>
    String(t ?? "").normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase();

  const escapar = (t) =>
    String(t ?? "").replace(/[&<>"']/g, (c) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

  const fechaCorta = (iso) => {
    const [a, m, d] = iso.split("-");
    return `${d}/${m}/${a}`;
  };
  const fechaHora = (iso) =>
    new Date(iso).toLocaleString("es-GT", { dateStyle: "short", timeStyle: "short" });

  function filaMensaje(texto) {
    cuerpo.innerHTML = `<tr><td colspan="${COLUMNAS}" class="vacio">${escapar(texto)}</td></tr>`;
  }

  function render() {
    const q = normalizar(buscador.value.trim());
    const filtrados = !q ? estudiantes : estudiantes.filter((e) =>
      normalizar([
        e.id, e.carne, e.nombres, e.apellidos, e.correo, e.carrera,
        e.telefono, fechaCorta(e.fecha_nacimiento), e.genero,
      ].join(" ")).includes(q));

    if (!filtrados.length) {
      filaMensaje(estudiantes.length ? "Ningún estudiante coincide con la búsqueda." : "Aún no hay estudiantes registrados.");
    } else {
      cuerpo.innerHTML = filtrados.map((e) => `
        <tr>
          <td>${e.id}</td>
          <td>${escapar(e.carne)}</td>
          <td>${escapar(e.nombres)}</td>
          <td>${escapar(e.apellidos)}</td>
          <td>${escapar(e.correo)}</td>
          <td>${escapar(e.carrera)}</td>
          <td>${escapar(e.telefono)}</td>
          <td>${fechaCorta(e.fecha_nacimiento)}</td>
          <td>${escapar(e.genero)}</td>
          <td>${fechaHora(e.fecha_registro)}</td>
        </tr>`).join("");
    }

    const total = estudiantes.length;
    const hora = ultimaCarga ? ` · Actualizado ${ultimaCarga.toLocaleTimeString("es-GT")}` : "";
    resumen.textContent = q
      ? `Mostrando ${filtrados.length} de ${total} estudiante(s)${hora}`
      : `${total} estudiante(s) registrado(s)${hora}`;
  }

  async function cargar() {
    btnActualizar.disabled = true;
    btnActualizar.textContent = "Actualizando...";
    alerta.className = "alerta oculto";
    if (!estudiantes.length) filaMensaje("Cargando...");

    try {
      const r = await fetch(`${API}/api/estudiantes`, { cache: "no-store" });
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      estudiantes = await r.json();
      ultimaCarga = new Date();
      render();
    } catch (err) {
      alerta.className = "alerta error";
      alerta.textContent = `No se pudo obtener el listado (${err.message}). Intente de nuevo.`;
      if (!estudiantes.length) filaMensaje("Sin datos.");
      resumen.textContent = "";
    } finally {
      btnActualizar.disabled = false;
      btnActualizar.innerHTML = "&#x21bb; Actualizar";
    }
  }

  let t;
  buscador.addEventListener("input", () => { clearTimeout(t); t = setTimeout(render, 150); });
  btnActualizar.addEventListener("click", cargar);

  cargar();
})();
