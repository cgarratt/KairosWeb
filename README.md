# Kairos Web 1.0 — Render

Dashboard **solo lectura** para Master Kairos v5.3.5, construido con Flask + FastMCP Client. No envía órdenes, no consulta saldos de cuentas y no ejecuta modos todavía. El menú muestra los diez modos como **pendientes de integración** (no botones engañosos).

## Despliegue

1. Crear un repositorio GitHub **privado** y subir los archivos de esta carpeta (sin secretos).
2. En Render → New → Blueprint, seleccionar ese repositorio y confirmar `render.yaml`; alternativamente Web Service Python con build `pip install -r requirements.txt` y start `gunicorn app:app --bind 0.0.0.0:$PORT`.
3. Configurar variables de entorno obligatorias en Render: `KAIROS_WEB_PASSWORD` (contraseña larga), `BINANCE_MCP_URL` y `HYPERLIQUID_MCP_URL` (URLs HTTPS terminadas en `/mcp`). Usuario: `kairos` predeterminado, modificable con `KAIROS_WEB_USER`.
4. Solo cuando corresponda, indicar `BINANCE_MCP_TOKEN` y `HYPERLIQUID_MCP_TOKEN` para autenticación Bearer de los servicios MCP; jamás pegar credenciales en HTML, GitHub ni variables públicas.
5. Render despliega y proporciona una URL `https://…onrender.com`. Acceder con autenticación HTTP Basic. Usar **HTTPS siempre**. En producción sensible se recomienda SSO / identity-aware proxy en lugar de Basic Auth.
6. Ver `/health` (sin credenciales) y la pestaña Conexiones; luego actualizar Dashboard.

**Importante:** Los MCP conectados a ChatGPT **no se heredan automáticamente** al servicio web. Debes introducir las URLs HTTPS reales de los dos servicios Render. Si los MCP usan otro esquema de auth, se deberá implementar explícitamente antes de conectarlos.

**Master incluido:** snapshot fechado 2026-10-15. Hay operaciones posteriores reportadas en la conversación que **no están** en ese fichero; para una valoración vigente se debe importar un snapshot consolidado más reciente, y confirmar fills y saldos. No se infieren fills ni se leen fondos de Binance/Hyperliquid automáticamente.

**Fuente Binance:** `get_kairos_spot_prices` (12 pares Spot/USDT). Fuente Hyperliquid: `get_hype_spot_ohlcv` (HYPE/USDC, histórico macro, no valor spot del portfolio). Nunca combinar series o introducir precios alternativos. Los estados `DATA_ERROR` bloquean cifras actuales si la lectura falla. Caché navegador deshabilitada. No se modifica el Master ni las reglas.

**Endpoint:** `/api/portfolio` muestra patrimonio y pesos solo cuando llegan 12 precios válidos; `/api/hype-macro` valida MCP Hyperliquid bajo demanda; `/api/mcp-status` muestra estado de configuración sin exponer URLs; `/api/modes` informa estado de integración; `/health` salud del servicio.

**Siguiente fase:** almacenamiento de snapshot versionado / fills deduplicados, autenticación fuerte, registro de auditoría y backend para ejecutar cálculos de modos desde Python bajo reglas Master, exclusivamente propuestas. Luego eventualmente conectar órdenes reales solo mediante un mandato nuevo y aprobaciones.
