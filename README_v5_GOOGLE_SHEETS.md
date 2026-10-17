# Kairos Web v5.0 — Google Sheets nativo + MCP Spot

**Base:** código UI y rutas de Kairos Web v4.3.3-SNAPSHOT. **Objetivo:** migrar inventario y parámetros al documento Google Sheets `KAIROS_V5_MASTER`, con lectura **únicamente** del estado `PUBLICADO`.

**Estado:** listo para configuración y pruebas en Render; **NO** validado todavía en producción. No se ha modificado GitHub, Render ni Kairos ChatGPT.

## Lo que hace la entrega

- Lee el Google Sheets nativo por API usando una cuenta de servicio privada, **solo lectura**. Lee `01_CONTROL`, `02_POSICIONES`, `03_LIQUIDEZ`, `04_CUSTODIA`, `05_ORDENES`, `06_FILLS`, `07_PIVOTES`, `08_INTEGRAL`, `09_BSI`, `11_VALIDACIONES`, `12_PARAMETROS_KAIROS`.
- Exige `estado_publicacion=PUBLICADO`, `schema_version=5.0.0`, `snapshot_id`, `publicado_utc` y verificaciones de 12 tokens, targets 100%, custodia por unidades, USDT por venue y QF sin duplicar.
- Lee las referencias históricas C1/C2 desde `07_PIVOTES`, marcadas **NO CERTIFICADAS**. Recupera el histórico BSI de `09_BSI` únicamente como **informativo**; BSI SELL sigue **BLOQUEADO**.
- Las políticas de capital, Balancer (±1 pp, C1 15% P, C2 10% P, USDT 40% indicador, reserva específica), O5 oficial 30% BTC / 70% USDT, y límites de riesgo TradingBot provienen de parámetros aprobados. TradingBot **WATCH**.
- Consulta Binance Spot MCP para precios, OHLCV e indicadores. `/api/hype-macro` consulta Hyperliquid HYPE/USDC 1d cerrado y agrupa semanas **lunes–domingo UTC completas**, no velas semanales arbitrarias.
- No incluye archivos `data/*.json` de inventario/costos/configuración; la aplicación **no** regresa silenciosamente a capturas ni datos antiguos si falla Sheets.
- Conserva páginas, tablas, estilos, Forecast simulado y notificaciones de v4.3.3. La bandeja de notificaciones continúa con SQLite *efímero* fuera del patrimonio; no usa PostgreSQL.

## Configuración obligatoria en Google Cloud (una sola vez)

1. En un proyecto Google Cloud propio, habilitar **Google Sheets API**.
2. Crear una **cuenta de servicio** con una clave JSON. Guardarla de manera privada; **nunca enviarla a este chat, GitHub ni al propio spreadsheet**.
3. En el Google Sheets nativo `KAIROS_V5_MASTER`, seleccionar **Compartir** y agregar el `client_email` de la cuenta de servicio con permiso **Lector**. El documento puede permanecer privado, no activar “cualquiera con el enlace”.

## Configuración obligatoria en Render

Desde **Render → kairos-web → Environment**, configurar:

| Variable | Valor |
|---|---|
| `KAIROS_GOOGLE_SHEET_ID` | `1_tG5FK_u0biVZm2iXaK6fJi1enBYJYLAG6txkpTgsy8` |
| `KAIROS_GOOGLE_SERVICE_ACCOUNT_JSON` | **El JSON completo de la cuenta de servicio**, colocado como variable secreta (NO en el repo) |
| `KAIROS_SHEETS_CACHE_SECONDS` | `60` (de 10 a 300 s permitidos) |
| `BINANCE_MCP_URL` | Mantener tu URL MCP HTTPS existente |
| `HYPERLIQUID_MCP_URL` | Mantener tu URL MCP HTTPS existente |
| `BINANCE_MCP_TOKEN`, `HYPERLIQUID_MCP_TOKEN` | Solo si están configurados, mantenerlos secretos |
| `KAIROS_WEB_USER`, `KAIROS_WEB_PASSWORD` | Conservar credenciales del sitio |

`KAIROS_GOOGLE_SERVICE_ACCOUNT_JSON` admite directamente el contenido JSON válido (incluyendo `private_key` con `\\n` JSON escapados). No añadir comillas externas. Render ofrece variables secretas; nunca subir credenciales al repositorio.

## Cómo actualizar en GitHub/Render

Copiar **el contenido** de la carpeta de este ZIP a la raíz del repositorio `KairosWeb` **reemplazando** los archivos de la v4.3.3. Eliminar `data/config.json`, `data/bsi_anchors.json`, `data/o2_reference_levels.json`, `data/cost_basis_verified.json`, `data/integral_portfolio_reference.json`, `data/snapshot_master_2026-10-17.json` del repo anterior (son **fuentes obsoletas**) para no mantener duplicados que lleven a confusión. No eliminar otros datos propios que no formen parte de ese listado.

Hacer commit/push a `main`. Render debe realizar despliegue automático si el repositorio está conectado. Configurar las variables **antes de esperar un dashboard funcional**.

## Pruebas en producción (después del deploy)

1. `GET /health`: muestra `version=5.0.0` y estado de la caché Sheets. Puede marcar servicio UP aunque no haya credenciales; **no** es prueba suficiente de datos.
2. `GET /api/sheets-status` con autenticación de la web: debe mostrar `status=OK`, `snapshot_id=KAIROS-2026-10-17-001`, `tokens=12`, `parameter_count=107`, reparto O5 `BTC=0.3`, `USDT=0.7`. Si falta autorización en Google o la hoja no está publicada devuelve **503 DATA_ERROR**.
3. `GET /api/mcp-diagnostics`: ambos proveedores deben estar `OK`.
4. `GET /api/portfolio`: debe mostrar `source="Binance Spot MCP + Google Sheets PUBLICADO"`, un precio reciente `observed_at`, USDT **28,130**, QF **7,225** y los 12 tokens del snapshot mientras este no cambie.
5. Dashboard `/`, `/mode/portafolio`, `/mode/balancer`, `/mode/compras`, `/mode/ventas`, `/mode/forecast`, `/mode/tradingbot`: abrir y verificar que la interfaz no cambió indebidamente, que las operaciones sean propuestas/simulaciones y el BSI SELL permanezca bloqueado.
6. Prueba negativa segura: **SIN** modificar la hoja real, usar tests `test_google_sheets_master.py`, que verifican rechazo de `BORRADOR`, targets mal sumados, QF inconsistente, O5 distinta de 30/70 y órdenes no reconciliadas. No modificar producción para comprobar fallos.

## Limitaciones conocidas (no confundir con certificación completa)

- **No equivalencia certificada con Kairos ChatGPT en todos los motores.** Se conserva el motor de escenarios y visualizaciones de v4.3.3. Las 107 filas de parámetros se **leen y auditan**, pero una parte de las reglas avanzadas está todavía en código (fórmulas del motor, simulaciones y selección visual). Se consumen explícitamente desde Sheet los parámetros críticos identificados en código.
- `07_PIVOTES` tiene referencias históricas y candidatos exploratorios, NO anclas O1/O3/O4 operativas certificadas. Propuestas LIMIT no son ejecutables.
- `09_BSI` aún no tiene baseline/HWM monetizado reconciliado. BSI SELL **BLOQUEADO**.
- Quantfury no integra API de posiciones/margen: TradingBot **WATCH**, sin READY.
- `08_INTEGRAL` sigue incluyendo importes históricos de 16/10 y queda señalado como histórico. No es balance live del portafolio.
- La sincronización es **de lectura**: modificar la hoja en estado publicado sin versión nueva rompe la trazabilidad; crear nuevo `snapshot_id` para cambios reales, recalcular validaciones y publicar con aprobación.
- Si la hoja se vuelve inaccesible después del TTL de 60 s, la web mostrará `DATA_ERROR`; no aparecerán balances inventados ni un fallback a JSON.
- La instalación de dependencias web y autenticación real con Google deben probarse en Render: el entorno local de construcción no tenía Flask/google-auth y bloqueó instalaciones, de modo que se ejecutaron pruebas de lógica, sintaxis y JavaScript pero **no** smoke test HTTP Flask ni acceso con credenciales a Sheets API.

## Diagnóstico de problemas frecuentes

- **503 /api/sheets-status**: revisar ID, API habilitada, cuenta de servicio compartida como lector, JSON correcto y `01_CONTROL` `PUBLICADO` + `11_VALIDACIONES`.
- **503 /api/portfolio con Sheets OK**: revisar Binance MCP, permisos y frescura del timestamp.
- **502 del Render gratis tras inactividad**: esperar que despierten los servicios MCP y consultar `/api/mcp-diagnostics`.
- **Google Sheets modifica datos pero web no cambia**: comprobar que se creó una versión de snapshot publicada nueva, esperar hasta el TTL, revisar `/api/sheets-status` y no deducir fill por variación de mercado.
