# KairosWeb v1.5.0

KairosWeb es una aplicación Flask/Render que consulta `KAIROS_V5_MASTER` nativo como fuente de posiciones, custodia, liquidez y parámetros publicados; precios/indicadores únicamente Binance MCP e histórico HYPE exclusivamente Hyperliquid Spot HYPE/USDC.

**Leer primero:** [RELEASE_NOTES_v1.5.0.md](RELEASE_NOTES_v1.5.0.md).

## Variables existentes de Render

Conservar `KAIROS_GOOGLE_SHEET_ID`, `KAIROS_GOOGLE_SERVICE_ACCOUNT_JSON`, `KAIROS_GOOGLE_WRITER_JSON`, `KAIROS_SETTINGS_ADMIN_KEY`, `KAIROS_SESSION_SECRET`, `KAIROS_SHEETS_CACHE_SECONDS`, `BINANCE_MCP_URL`, `HYPERLIQUID_MCP_URL` y credenciales web existentes. No incluir claves en GitHub ni en este ZIP.

## Consulta y seguridad

- `/health` y `/api/sheets-status`
- `/settings?tab=parameters`: parámetros agrupados por módulo, tramos individuales 0–100%, suma 100% por onda.
- `/settings?tab=pivots`: O1 preliminar desde OHLCV semanal construido con velas Spot cerradas. La consulta **no** certifica Elliott ni genera órdenes.
- `/mode/forecast`: simulación O2–O5 con parámetros publicados o defaults virtuales; no altera Google Sheets.

**Almacenamiento:** los 16 nuevos parámetros de Forecast se publican en el Master únicamente tras una modificación autorizada desde Settings; durante la carga son virtuales. El guardado es auditado y crea una nueva revisión. No existen presupuestos dobles C1/C2 ni ventas automáticas.
