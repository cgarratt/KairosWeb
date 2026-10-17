# KairosWeb v1.0.0 — Candidato previo a liberación (tres cambios)

Este paquete reemplaza **KairosWeb v1.0.0 anterior** como candidato de versión. Parte de la fuente auditada v1; no actualiza KairosGPT ni despliega Render por sí solo. El esquema compartido de `KAIROS_V5_MASTER` sigue siendo **5.0.0**.

## Cambios implementados

1. **Navegación directa.** Eliminada página/ruta `/modes` y botón «Modos Kairos». En el header global aparecen únicamente los modos definidos/habilitados en `MODE_DEFS`/`ENABLED_MODE_SLUGS` de `app.py`. Al publicar un modo nuevo se añade al listado central, por lo que aparecerá en todas las vistas; nunca se añade un enlace manual por página. Endpoint informativo `/api/modes` continúa disponible.
2. **Campana de Alertas 1H.** Consulta exclusivamente `15_ALERTAS_RUNS` (corridas con marco `1H`) y `16_ALERTAS_EVENTOS`, conserva fecha `creado_utc`, token, estado, certificación y **acción literal**. Solo muestra IDs no leídos, conforme a `17_ALERTAS_LECTURAS`. Refresca una vez por minuto sin atribuirle ejecución real de órdenes. Marcar como leído agrega un acuse en Sheets; no toca ni borra los eventos originales. No hay SQLite ni ingest puente anterior.
3. **Configuración (tuerca).** Ruta `/settings`, visible en el header junto a la campana, y endpoints `/api/settings/{data,preview,publish}`. Secciones implementadas: Maestro de unidades/costos, Objetivos/Tier, Custodia por Tier, Liquidez, Parámetros de Balancer/Compras/Ventas/O3/O5/TradingBot/Alertas, y Pivotes **pendientes de certificación**. No se permiten ediciones genéricas a celdas arbitrarias. Requiere evidencia, vista previa firmada de validez 15 min, confirmación de publicación, autorización administrativa y nueva versión en `01_CONTROL` y `10_HISTORIAL`. Registra cada cambio antiguo/nuevo en `18_SETTINGS_AUDITORIA`.

### Google Sheets original

`KAIROS_V5_MASTER` — spreadsheet ID `1_tG5FK_u0biVZm2iXaK6fJi1enBYJYLAG6txkpTgsy8`.

**Pestañas nuevas creadas directamente en el original:** `17_ALERTAS_LECTURAS` y `18_SETTINGS_AUDITORIA`. Solo contienen cabeceras, sin alterar `PUBLICADO` ni saldos. Son necesarias para activar acuses persistentes y auditar Settings.

### Seguridad: separar lectura de escritura

La cuenta existente `kairos-web-reader@kairos-web-v5.iam.gserviceaccount.com` **debe permanecer como Lector**. Para las dos acciones de escritura, crea una **segunda cuenta de servicio** (por ejemplo `kairos-web-editor`), concede a ese correo **Editor únicamente sobre `KAIROS_V5_MASTER`**, genera su JSON en Google Cloud y configúralo como secreto en Render. **Nunca pegues las claves privadas en ChatGPT ni GitHub**.

Variables de entorno adicionales en Render:

| Variable | Propósito |
| --- | --- |
| `KAIROS_GOOGLE_WRITER_JSON` | JSON completo de la **segunda** cuenta Google con Editor en el Master. Sin esta variable el sistema queda en consulta y no puede registrar lecturas ni publicar cambios. |
| `KAIROS_SETTINGS_ADMIN_KEY` | Contraseña adicional larga, aleatoria y distinta de `KAIROS_WEB_PASSWORD`, ingresada en el formulario de Configuración (solo memoria de esa página). |

Se conservan `KAIROS_GOOGLE_SHEET_ID`, `KAIROS_GOOGLE_SERVICE_ACCOUNT_JSON`, `KAIROS_SHEETS_CACHE_SECONDS`, los dos MCP y la autenticación web ya configurada.

- Todos los endpoints salvo `/health` requieren Basic Auth de KairosWeb.
- POST exige origen mismo host HTTPS para evitar CSRF. Settings requiere clave administrativa adicional.
- El servidor firma la vista previa con HMAC y exige la misma propuesta al publicar; expira en 15 minutos.
- Escritura en Sheets usa `spreadsheets.batchUpdate` con controles previos y auditoría en la misma transacción.
- Se compara el `snapshot_id` esperado con el último publicado para evitar aplicar formularios viejos.
- Nunca se guardan claves privadas en el repositorio ni se muestran datos sensibles en logs HTTP.
- Relectura de snapshot después de publicar. Sin verificación: **DATA ERROR**, sin fallback JSON.

**Limitación de seguridad:** los permisos Google `Editor` habilitan tecnológicamente edición de todo el archivo mediante esa identidad; las restricciones de pestañas/columnas las implementa **KairosWeb**. Por eso debe ser cuenta separada, credenciales privadas y solo habilitarse tras revisar permisos del servicio. No se ha implementado RBAC multiusuario ni aprobaciones de dos personas.

### Qué no se autoriza en este release

- `05_ORDENES` y `06_FILLS`: no se editan desde Settings; requieren ledger de ejecuciones, comisiones, deduplicación y conciliación.
- `09_BSI`: solo consulta; BSI SELL continúa **BLOQUEADO** hasta homologación de baseline/HWM.
- `07_PIVOTES`: las modificaciones registradas quedan `PENDIENTE_CERTIFICACION`; no crean pivotes Elliot confirmados ni órdenes LIMIT.
- TradingBot: `WATCH`, no `READY` por inferencia.
- Cambios de unidades/liquidez requieren evidencia y fecha de corte; son declaraciones administrativas, **no** fills inferidos.
- La interfaz no aplica órdenes ni mueve custodia. Simulaciones siguen aisladas.
- El parámetro O5 inicial es **30% BTC / 70% USDT**; Settings admite revisión aprobada posterior siempre que sumen 100%, sujeta a que la política del proyecto KairosGPT no mantenga una constante incompatible.

## Despliegue de esta versión candidata

1. Mantén la versión anterior en Render mientras haces pruebas; conserva un ZIP/referencia del último commit que funciona.
2. Sube el **contenido** del directorio del paquete a la raíz del repositorio `KairosWeb` en GitHub. Si existía `templates/modes.html`, elimínalo. No subas un ZIP como archivo ejecutable.
3. Configura **solo cuando necesites escritura** las dos nuevas variables secretas en Render y comparte el Master con la segunda cuenta editora.
4. Realiza commit/deploy y valida: `/health` devuelve `version: 1.0.0`; `/api/sheets-status` mantiene snapshot publicado; `/api/alerts/unread` devuelve 1H no leídas; `/settings` ofrece los seis formularios.
5. Sin cuenta editora, la campana **lee** eventos pero el botón de marcar leído aparece deshabilitado. Configuración permite consultar; publicación bloqueada. Es intencional.
6. Con cuenta editora, prueba primero marcar una única notificación como leída; verifica fila nueva en `17_ALERTAS_LECTURAS`, sin alterar `16_ALERTAS_EVENTOS`.
7. En Configuración, haz una vista previa sobre una modificación permitida; comprueba que la previsualización **no escribe** en Google Sheets. No publiques cambios contables durante pruebas sin autorización y evidencia reales.

## Validación realizada en este entorno

- Pruebas Python de Google Sheets/controles: **38 PASS**.
- Prueba JavaScript de Forecast: **PASS**.
- Compilación Python, sintaxis JS y análisis de 10 plantillas Jinja: **PASS**.
- Consulta mediante conector autorizado a las pestañas originales: `15_ALERTAS_RUNS` 2 corridas 1H, `16_ALERTAS_EVENTOS` 15 eventos 1H sin leer; `17_ALERTAS_LECTURAS` y `18_SETTINGS_AUDITORIA` con cabeceras y 0 registros. No se editaron órdenes, filas de posiciones ni parámetros del Master.
- **No comprobado todavía:** HTTP del despliegue final Render, autorización de la segunda cuenta, publicación real por Settings, ni equivalencia total Forecast/TradingBot con KairosGPT. No declarar release certificado hasta pasar esas pruebas.
