# KairosWeb v2.0.36 — Acceso por niveles y diagnóstico Spot

## Cambios
- **Visitante**: acceso directo a la navegación; páginas de consulta no reciben saldos, unidades, exposiciones, señales, alertas ni cálculos privados del backend. El servidor responde 401 `PORTFOLIO_AUTH_REQUIRED` en APIs protegidas, sin serializar datos sensibles.
- **Usuario**: formulario de `KAIROS_WEB_USER` y `KAIROS_WEB_PASSWORD` (variables privadas de Render) con sesión firmada, cookie HttpOnly/Secure/SameSite Strict, verificación CSRF en login, cierre de sesión y limitación por IP en memoria (5 fallos/15 min por proceso). Los endpoints privados incluyen ahora controles de autorización del lado del servidor.
- **Configuración**: mantiene un segundo control administrativo con `KAIROS_SETTINGS_ADMIN_KEY`, sesión y validación CSRF. Cerrar la sesión administrativa no destruye la sesión normal del portafolio.
- **Portafolio**: título único "Portafolio" (antes "KAIROS | PORTAFOLIO").
- **MCP Binance**: reintentos acotados para HTTP 429/500/502/503/504 y timeouts; diagnóstico muestra categoría, código HTTP cuando está disponible, ID y enlace para reintentar. SIN precios ficticios ni fallback a valores obsoletos.

## Diagnóstico del incidente e7e31c141a
Captura identifica `UPSTREAM_HTTP` en `BINANCE_SPOT_MCP`; la causa detallada depende de los logs del servicio Render con el ID y el código HTTP. No equivale a un fallo de autenticación del usuario. La consulta Binance MCP en esta conversación devolvió 12 precios, pero no verifica el camino HTTP Render→MCP.

## Control de aceptación
- Guest: `/` y `/mode/<slug>` solo muestran campos ocultos; `/api/portfolio`, `/api/settings`, `/api/mcp-diagnostics`, `/api/alerts` requieren sesión. `/health` y recursos estáticos públicos no muestran saldos.
- User: puede consultar datos autenticado y cerrar sesión con CSRF. No puede editar MASTER sin sesión administrativa adicional.
- Admin: contraseña adicional obligatoria incluso con la sesión de usuario abierta; endpoints de escritura siguen autenticados y con CSRF.
- No modificar `01_CONTROL`, `02_POSICIONES`, `03_LIQUIDEZ` ni enviar órdenes.

## Variables existentes en Render
`KAIROS_WEB_USER`, `KAIROS_WEB_PASSWORD`, `KAIROS_SESSION_SECRET`, `KAIROS_SETTINGS_ADMIN_KEY`.
En múltiples instancias, activar además protección anti fuerza-bruta en el gateway; el limitador local no es compartido.

## Validación local
219 pruebas Python aprobadas, 2 omitidas antes de última consolidación; 9 suites JavaScript, 14 plantillas Jinja parseadas. Pruebas HTTP reales de sesión y conectividad en Render **pendientes** porque este entorno no tiene Flask ni FastMCP instalados.
