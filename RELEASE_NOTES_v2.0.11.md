# KairosWeb v2.0.11 — Configuración y UX móvil

**Origen:** release acumulativo basado en KairosWeb v2.0.10, con mejoras de acceso administrativo y tooltips móviles. Sin cambios de fuentes financieras ni órdenes reales.

### Autenticación administrativa
- `/settings` y sus pestañas: un único login para toda la sección; se preserva la pestaña inicial y no se aceptan redirecciones arbitrarias.
- Credenciales almacenadas únicamente como variables de entorno; cookie de sesión firmada HttpOnly, Secure, SameSite Strict, duración 30 minutos.
- `/api/settings/data` requiere sesión administrativa; endpoints de escritura continúan protegidos por comprobaciones de origen, autorización y CSRF.
- Se elimina el vínculo redundante «Iniciar sesión de administrador para editar» de la interfaz de Configuración.

### Tooltip responsive
- En pantallas móviles de <= 680 px o con `hover:none` y `pointer:coarse`, se quitan atributos title de botones, links y menú; se oculta tooltip táctil.
- Escritorio conserva tooltips, inclusive en controles dinámicos. `aria-label` permanece disponible para tecnologías de asistencia.

### Integridad y operación
- `/health` verifica plantillas/login y JavaScript mobile tooltip además de los componentes existentes, para detectar carga parcial en GitHub/Render.
- Órdenes sigue solo propuestas, sin llamadas para colocar/cancelar operaciones; cambios en Google Sheets siempre sujetos a publicación explícita.
- `KAIROS_V5_MASTER` mantiene schema 5.0.0, sin modificación de snapshot, balances ni custodias.

### Validación pendiente después del despliegue
- Probar autenticación real, cookies y expiración de sesión en Render.
- Probar tooltips con dispositivos reales móviles/escritorio.

### Validaciones locales de esta compilación
- `pytest -q`: **145 PASS**, 2 SKIP (Flask y servicios MCP reales no disponibles en este entorno).
- `node tests/*.js`: **9 PASS**.
- Chromium local: escritorio conserva tooltips, móvil los quita (incluyendo botones dinámicos).
- Sintaxis Python y JavaScript OK, `/health` markers contract OK.
- Pendiente: smoke test HTTP/cookies reales en Render y revisión visual sobre móviles físicos.
