# KairosWeb v1.3.0 — Release (código listo para desplegar)

**Base:** KairosWeb v1.2.0. **Contrato de datos:** `KAIROS_V5_MASTER` Google Sheets, `schema_version=5.0.0`. **KairosGPT:** sin cambios. **Despliegue:** GitHub/Render pendiente, no realizado por este paquete.

## Cambios aprobados 12–19

1. **Configuración:** se eliminó la insignia decorativa «Validar → Guardar → Sincronizar». El botón real sigue siendo «Guardar cambios», con sesión administrativa, evidencia, validación y auditoría. No se cambió la política de publicación.
2. **Pivotes preliminares:** la sección conserva la precarga archivada de los 12 activos. Al pulsar «Actualizar candidatos desde MCP», el backend usa Binance Spot (11 activos) y Hyperliquid Spot HYPE/USDC (HYPE) token por token. En Binance, si no hay SH1 estructural candidato, se consulta OHLCV 1D cerrado y se ofrece el **máximo diario observado estrictamente después de la fecha candidata de Cycle Low** como **O1 preliminar**, nunca certificado. Se registran fecha, método y advertencia. Los casos de SUI/PUMP con CL corregido y fecha no homologada NO usan la fecha del flash crash descartado para inferir O1. Las ondas O2–O5 permanecen vacías si no hay evidencia, no se rellenan algebraicamente. En HYPE, un O3 observado sin 5R se muestra como candidato, no como pivote confirmado. Las anclas editadas manualmente y las oficiales no se sobrescriben automáticamente.
3. **Forecast:** precios en puntos de la gráfica de ondas con letras más grandes y contraste para ambos temas; descripción del token, onda, valor y estado en cada punto. No cambió la lógica matemática.
4. **Campana:** muestra solo alertas 1H **certificadas, accionables, sin leer y deduplicadas** en las clases COMPRA, VENTA, TRADINGBOT READY y PREPARAR LIQUIDEZ. BSI SELL únicamente si el Master autoriza baseline/anclas BSI y el evento está certificado. Se excluyen WATCH, PRECONFIRMADO, DATA ERROR no urgente, NO ORDEN, RR<2 no elegible, falta de presupuesto, y repeticiones idénticas persistentes. La acción masiva «Marcar todas como leídas» se aplica solo a las alertas mostradas. Los eventos de KairosGPT siguen archivados íntegramente.
5. **Interactividad:** cursores `pointer`, `not-allowed`, hover y estados de foco para menús, botones y controles.
6. **Tooltips:** descripciones en navegación, botones, tablas, barras y puntos SVG de Forecast; toque en móviles y foco/teclado en elementos interactivos.
7. **BSI:** título unificado «BTC Strength Index (BSI)» con explicación de comparación frente a BTC. BSI SELL sigue bloqueado mientras no se homologue.
8. **Conexiones MCP:** eliminado panel final «Conexiones MCP» del Dashboard. Nueva sección **Configuración → Estado de conexiones MCP** con pruebas reales separadas para Binance e Hyperliquid, timestamp de última respuesta exitosa del proceso, diagnóstico sin revelar claves y botón «Refrescar» solo para administradores. «Verificar» NO reinicia servicios; «Refrescar» invalida la caché Spot de KairosWeb cuando corresponde y hace una nueva consulta, **NO reinicia Render**. El diagnóstico puede abrirse con `/settings?tab=mcp` incluso si el Master falla; el guardado del Master continúa cerrado ante DATA ERROR.

## Contrato de alertas accionables

El emisor KairosGPT debe registrar en `16_ALERTAS_EVENTOS` una acción certificada con `estado_evento=READY` (o estado aprobado explícito), `certificacion=CERTIFICADA/VERIFICADA/APROBADA` para COMPRA, VENTA y LIQUIDEZ, `nivel_usdt > 0` y, para compra/preparación, `usdt_preparar > 0`; el texto `accion_sugerida` debe describir una instrucción concreta. Se admiten los prefijos `COMPRA_` y `VENTA_` además de los tipos canónicos. Para TradingBot se exige `TRADINGBOT_`, `certificacion=CERTIFICADA_QF/VERIFICADA_QF`, `nivel_usdt > 0` e instrucciones SL/TP. La campana no constituye automatización ni evidencia de fill. Se requiere homologar el esquema del productor para que emita estos estados, de lo contrario el resultado correcto es **0 alertas accionables**. No se modifican aquí tareas programadas de KairosGPT.

## Diagnóstico MCP y seguridad

- `GET /api/mcp-diagnostics?provider=binance` o `provider=hyperliquid`: prueba de conectividad detrás de la contraseña Basic de KairosWeb; devuelve `OK / CHECK_REQUIRED` y por proveedor `status`, `checked_utc`, `last_success_utc`, errores con categoría general y sin credenciales.
- `GET /api/admin/session`: estado de sesión administrativa para diagnóstico, sin devolver secretos; admite consulta cuando el Master no responde.
- `POST /api/mcp-refresh` con JSON `{ "provider": "binance" | "hyperliquid" }`, sesión admin y `X-Kairos-Csrf`: reconsulta, caché local invalidada para Binance; **nunca reinicia ni despliega Render**.
- `GET /health` sigue siendo estado del proceso de KairosWeb, no `/health` del MCP ni una operación de reinicio.
- No existe fallback a snapshots JSON/PNG antiguos, ni se escribieron saldos, pivotes, fills o parámetros reales durante el desarrollo.
- No hay claves, secretos ni autenticación dentro del ZIP.

## Pruebas locales

- `python -m pytest -q` — **91 PASS** (incluye 15 nuevos casos de 1.3.0 para alertas, pivotes y contrato MCP).
- `node tests/test_forecast_segments.js` y `node tests/test_settings_format.js` — PASS.
- `python tests/browser_pivot_smoke.py` — PASS en Chromium offline.
- `python tests/browser_release_v13.py` — PASS, sección MCP, botones, tooltips y tema oscuro; simulación sin escrituras.
- `python -m compileall -q .` y `node --check` — PASS.

## Despliegue y verificación

1. Sustituir los archivos del repositorio GitHub por el **contenido descomprimido** del ZIP. Se conservan las variables de entorno de 1.2.0: `KAIROS_GOOGLE_SHEET_ID`, `KAIROS_GOOGLE_SERVICE_ACCOUNT_JSON`, `KAIROS_GOOGLE_WRITER_JSON`, `KAIROS_SETTINGS_ADMIN_KEY`, `KAIROS_SESSION_SECRET`, `BINANCE_MCP_URL`, `HYPERLIQUID_MCP_URL` y credenciales de la web.
2. Comprobar en Render `/health` → `version: "1.3.0"` y `/api/sheets-status` → snapshot PUBLICADO.
3. Abrir `/settings?tab=mcp`; pulsar «Verificar conexión» por proveedor y validar timestamps. El diagnóstico no exige editar el Master.
4. En Configuración → Pivotes preliminares, ver los candidatos archivados y pulsar «Actualizar candidatos desde MCP»; revisar O1 y la fecha de observación. No publicar pivotes como confirmados sin evidencia de 5L/5R+BOS y validación humana.
5. En tema claro y oscuro, revisar Forecast, la campana y el nuevo título BSI.
6. Para validar «Refrescar conexión», iniciar sesión administrativa. Esta acción no cambia los saldos ni el Master.

**No se ha ejecutado un deploy ni una prueba HTTP real en Render con estas credenciales**. Las pruebas anteriores son locales y simuladas. Antes de considerar la versión estable en producción, validar los endpoints reales y una sesión administrativa.
