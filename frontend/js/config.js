// URL base del web service.
// - Vacío ("") cuando el frontend lo sirve el mismo FastAPI (local o Render): recomendado.
// - Si publica el frontend en otro hosting (Netlify, GitHub Pages...), ponga la URL del servicio:
//   API_BASE: "https://registro-estudiantes.onrender.com"
window.APP_CONFIG = {
  API_BASE: "",
};
