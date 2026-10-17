# KairosWeb v1.1.0 RC1 — ocho mejoras acumuladas

**Candidato de despliegue** derivado de KairosWeb v1.0.0 Pre-release, **sin cambios en KairosGPT** ni en los saldos de `KAIROS_V5_MASTER`. El contrato de Google Sheets sigue siendo `schema_version=5.0.0`.

## Qué incluye

1. **Alertas Kairos:** título simplificado; botón masivo «Marcar todas como leídas» junto a Actualizar. Eliminadas acciones individuales. Consulta sólo eventos de corridas 1H en `15_ALERTAS_RUNS`/`16_ALERTAS_EVENTOS`, descuenta los acuses de `17_ALERTAS_LECTURAS`. Al marcar todas escribe un único lote de acuses append-only; jamás elimina eventos históricos. WATCH/PRECONFIRMADO no son órdenes.
2. **Maestro de unidades:** HODL, Core, Exchange e **Inversión remanente USDT** son entradas; se calculan automáticamente **Total unidades** y **Costo medio = Inversión remanente / Total unidades**. Se guarda `02_POSICIONES` en E/F/G/J y N, se preservan fórmulas H/I. Requiere evidencia y no acredita fills.
3. **Guardar cambios unificado:** un botón común en todas las secciones; validación completa, publicación y auditoría atómica mediante `spreadsheets.batchUpdate` y relectura del snapshot. Fecha de corte de inventario, cuando corresponde, se genera en servidor con `America/Lima`. No se muestra campo editable de fecha ni clave en Settings.
4. **Porcentajes globales:** formateador explícito: `0.20` en fracción es `20%` editable; `DRIFT_BAND_PP=1` es `1 pp`; BSI `TRIGGER_STRICT_GT=20` es `20%` directamente. No se multiplica por 100 un valor ya definido en %. Los modos y dashboard ya expresaban porcentajes en su UI y conservan ese comportamiento.
5. **Liquidez por venue:** total USDT acumulado, reserva QF incluida una sola vez, USDT operativo, total previo del Master y diferencia propuesta. Actualización instantánea mientras se edita.
6. **Nombres amigables y explicaciones:** 18 parámetros editables reciben etiqueta en español, descripción y procedencia real de la columna I de `12_PARAMETROS_KAIROS`; se preserva clave técnica discretamente. Parámetros no aprobados no son editables.
7. **Pivotes preliminares:** botón y precarga automática al abrir la pestaña, leyendo **Binance MCP** (11 tokens) y **Hyperliquid Spot HYPE/USDC MCP** (histórico diario cerrado, semanas UTC lunes–domingo con 5L/5R). Muestra CH y fechas como contexto, precarga sólo campos vacíos CL/O1/O2/O3, nunca reemplaza cambios existentes sin intervención. SUI usa `SUI_CL_SELECTED` y PUMP `PUMP_CL_CANDIDATE` del Master para excluir extremos descartados. **Candidatos NO certificados**; O3 HYPE sin cinco semanas posteriores no es onda validada, O4/O5 pendiente. Al guardar continúa `PENDIENTE_CERTIFICACION`; no genera órdenes.
8. **Tema claro/oscuro:** icono global de sol/luna junto a campana y tuerca, selector duplicado en Configuración, persistido en `localStorage` del navegador; tema oscuro azul marino de alto contraste. No escribe preferencias al Master.

## Autorización administrativa y Google Sheets

La cuenta de servicio anterior (inicialmente Lector) puede reutilizarse como Editor del **único archivo** `KAIROS_V5_MASTER`. El propietario ya decidió ese esquema y lo autorizó. Las dos variables JSON pueden contener la **misma cuenta de servicio**, pero los permisos de lectura y escritura de Google ya no están separados para esa identidad. Solo compartir el documento con ese correo como Editor, no otorgar permisos IAM globales de Google Cloud.

Variables requeridas en Render:

| Variable | Uso |
|---|---|
| `KAIROS_GOOGLE_SHEET_ID` | ID exacto del Master |
| `KAIROS_GOOGLE_SERVICE_ACCOUNT_JSON` | JSON de cuenta Google con lectura |
| `KAIROS_GOOGLE_WRITER_JSON` | JSON de cuenta Google con permisos Editor (puede ser igual al anterior) |
| `KAIROS_SETTINGS_ADMIN_KEY` | Secreto administrativo, largo y distinto al acceso web |
| **`KAIROS_SESSION_SECRET`** | **NUEVO en v1.1.0:** valor secreto aleatorio de mínimo 32 bytes, distinto a los anteriores, para firmar cookies de sesión |
| `KAIROS_WEB_USER`, `KAIROS_WEB_PASSWORD` | Acceso HTTP Basic existente |
| `BINANCE_MCP_URL`, `HYPERLIQUID_MCP_URL` | Mercado en vivo por MCP |
| `KAIROS_SHEETS_CACHE_SECONDS` | 60 recomendado |

No pegar secretos en el chat ni en GitHub, no incluir JSON de credenciales en el ZIP. Al cargar `/settings`, los datos siguen disponibles en **solo lectura** sin sesión administrativa. Para guardar: ir a `/admin/login`, introducir allí la clave de administración **una vez**, sin exponerla en Settings; cookie HttpOnly Secure SameSite Strict con duración de hasta 30 minutos y petición POST con token CSRF. La autenticación Basic **NO** autoriza escritura por sí sola. El usuario puede cerrar sesión desde Settings.

**El botón Guardar** llama `/api/settings/save` exclusivamente, con el `snapshot_id` esperado. El servidor recompone los datos de Google, valida todo, bloquea cambios en órdenes/fills/BSI, registra en `18_SETTINGS_AUDITORIA`, publica nuevo `snapshot_id` en `01_CONTROL`, registra en `10_HISTORIAL`, invalida caché y revalida la versión publicada. Si el snapshot cambió, se rechaza. El código ya contiene las pruebas unitarias, pero la escritura real aún debe verificarse en Render con una **modificación inocua previamente autorizada**. No probar cambiando balances ficticiamente.

## Cómo desplegar

1. Conserva copia o commit de KairosWeb v1.0.0 actual. **No desplegar con secretos copiados a GitHub.**
2. Descomprime el ZIP y sube **los archivos de la carpeta `KairosWeb_v1.1.0_CANDIDATE/` a la raíz** del repositorio. Mantener `templates/`, `static/` y `tests/`. Elimina solo el viejo código que fue sustituido; sin snapshots locales como fuente operativa.
3. En Render → Environment verifica el nuevo `KAIROS_SESSION_SECRET` y el resto de variables. El archivo `render.yaml` las declara como `sync:false`; NO las rellena.
4. Despliega el commit. Comprueba `/health` (`version: 1.1.0-rc1`), `/api/sheets-status` (`status: OK`, snapshot válido), `/api/portfolio`, `/api/alerts/unread`, `/settings`, `/admin/login` y `/api/settings/pivots/preliminary` (puede tardar, es consulta MCP; no escribirá en Master).
5. Primero prueba tema claro/oscuro, navegación y cálculo visual. Después marca todas las alertas como leídas **solo si realmente quieres descartarlas de la campana**; verifica acuses en `17_ALERTAS_LECTURAS`.
6. Si deseas probar publicación real, autoriza previamente un cambio legítimo pequeño, verifica el historial y vuelve a consultar KairosGPT. No generes revisiones ficticias del portafolio.

## Estados no certificados

BSI SELL **BLOQUEADO**, O2/Fibonacci C1/C2 históricos **no certificados**, TradingBot **WATCH** sin conciliación QF, simulaciones Forecast **no ejecutables**, BTC NEVER SELL y HODL protegido. Los pivotes MCP no certifican Elliott ni habilitan LIMIT. No se modificó la hoja en esta fase.

## Pruebas

- `python -m pytest -q` — **53 PASS** (incluye el contrato Google Sheets, costos, seguridad documental, 1H, candidatos HYPE, excepciones SUI/PUMP y Forecast).
- `node tests/test_settings_format.js` — PASS.
- `node tests/test_forecast_segments.js` — PASS.
- `node --check static/*.js` individual y `python -m compileall` — PASS.
- Jinja2 parseo de plantillas — PASS.
- **Pendiente de validar:** endpoints HTTP en Render, firma real de sesión mediante Flask, la apariencia visual en navegadores, accesibilidad completa y las escrituras reales. No declarar liberación de producción hasta completar estas pruebas.
