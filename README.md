# Kairos Web v4.0.2 — estabilidad de conexión MCP

Parche sobre v4.0.1. Sin cambios de política de portafolio ni de interfaz.

- Registra en Render `http_status` HTTP real para errores httpx.HTTPStatusError, incluso anidados en ExceptionGroup.
- Los logs contienen solo ID, proveedor, tipo y código HTTP; nunca URL/token/cabeceras/trazas con secretos.
- `/api/mcp-diagnostics` devuelve `diagnostic.http_status` cuando está disponible.
- Una sola petición de mercado en vuelo por proceso. Caché de 30 segundos con `observed_at` original; no ofrece cotizaciones caducadas como LIVE.
- Gunicorn pasa a 1 worker y 8 threads para compartir caché en el plan Free.

## Instalación
Copiar contenido de esta carpeta a la raíz del repo KairosWeb; commit/push a main. Mantener variables de entorno de Render. Después probar `/api/mcp-diagnostics`, `/api/portfolio`, `/mode/balancer`, `/mode/compras` y `/mode/ventas`.

## Nota
Un 502/503/504 de Render o del MCP necesita revisión operativa del servicio remoto; el parche registra el HTTP exacto y no promete resolver errores upstream.
