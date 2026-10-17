# KairosWeb v1.4.0

Aplicación Flask/Render con Google Sheets Master `KAIROS_V5_MASTER` como fuente de inventario, custodia, liquidez y parámetros; Spot/indicadores desde Binance MCP e historia macro HYPE desde Hyperliquid Spot HYPE/USDC.

**Leer primero** [RELEASE_NOTES_v1.4.0.md](RELEASE_NOTES_v1.4.0.md). Contiene cambios, criterios de seguridad y pruebas. No usar imágenes/JSON antiguos para posiciones.

## Arranque de Render

Conservar `KAIROS_GOOGLE_SHEET_ID`, `KAIROS_GOOGLE_SERVICE_ACCOUNT_JSON`, `KAIROS_GOOGLE_WRITER_JSON`, `KAIROS_SETTINGS_ADMIN_KEY`, `KAIROS_SESSION_SECRET`, `BINANCE_MCP_URL`, `HYPERLIQUID_MCP_URL`, y credenciales de la web ya existentes. Secretos **solo** como variables del servicio Render; jamás en GitHub o Google Sheets.

La configuración de Forecast se mantiene en `12_PARAMETROS_KAIROS`; las cuatro nuevas claves se **provisionan únicamente si se guardan cambios administrativos**. Hasta entonces se usan defaults de simulación sin escribir en Sheets. BSI SELL bloqueado; TradingBot WATCH hasta certificar QF.

## Rutas de comprobación

- `/health`, `/api/sheets-status`
- `/mode/forecast`
- `/settings?tab=parameters`
- `/settings?tab=pivots`

No hay ejecución automática de órdenes ni transferencia de custodia.
