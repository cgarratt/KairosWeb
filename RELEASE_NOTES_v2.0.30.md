# KairosWeb v2.0.30 — Confiabilidad operativa B05–B08

**Base:** v2.0.29. **MASTER:** KAIROS_V5_MASTER original; `schema_version=5.0.0`. **Operación:** lectura/simulación, sin órdenes ni transferencias remotas.

## B05 — Tres niveles de salud independientes

- `GET /health`: **liveness económico** para Render; indica servidor, integridad del release y el resultado **cacheado** del último diagnóstico. No dispara nuevas consultas externas, no revela URLs/tokens y no confunde servidor `UP` con conectividad MCP.
- `Configuración → Estado de conexiones MCP`: incluye botón de diagnóstico integral y una respuesta legible con estados de servidor, proveedores y módulos.
- `GET /api/health/diagnostics`: requiere autenticación HTTP Basic existente; ejecuta lecturas read-only en paralelo de Google Sheets (`force=True`), Binance Spot MCP (12 tokens) y Hyperliquid Spot MCP (HYPE). Informa `server`, `operational_providers`, `functional_modules`, marca temporal y códigos de error seguros. Devuelve 503 si la comprobación revela una dependencia no disponible.
- El estado de los módulos verifica **dependencias de datos**, no prueba de todas las rutas ni certificación de trading; TradingBot sigue WATCH y BSI SELL sigue bloqueado según política.

## B06 — Error explícito en Portafolio

- Si Binance MCP o el cálculo de valoración falla, se muestra `DATA_ERROR` visible con origen, categoría, ID de incidente, hora UTC de consulta, último Spot válido (solo metadato) y snapshot/corte de Sheets. Se descartan **todos los cálculos Spot del intento fallido**; no se reciclan precios antiguos ni se mezcla P&L parcial con el nuevo snapshot.
- Los logs mantienen tipo de excepción, ID y categoría, no detalles potencialmente sensibles de credenciales o respuesta.

## B07 — Homologación vinculada al snapshot

- Se lee **solo para diagnóstico** `13_CONTROL_HOMOLOGACION` además de las hojas obligatorias del contrato v5.0.0.
- Se comparan referencias de `PASS` para `01_CONTROL PUBLICADO` y `03_LIQUIDEZ QF UNA VEZ` contra el `snapshot_id` y USDT del MASTER actual. Si difieren, el panel muestra `STALE` y los códigos correspondientes; si no hay datos, `NOT_VERIFIED`.
- `PASS` documental histórico **no pasa a certificación vigente**. No se modifican Sheets, saldos, fills ni parámetros. Un control viejo no anula un snapshot de posiciones válido.

## B08 — Capital histórico identificado como tal

- El donut histórico muestra `HISTÓRICO NO SPOT`, `08_INTEGRAL` y la referencia de fecha presente en las notas del MASTER. Si la nota contiene 16/10 sin año, se señala que el año no está especificado, **sin inventarlo**.
- La valoración actual queda en los KPI y el donut allocation Spot; el capital histórico y LOST no se suman otra vez.

## Validación local

- **197 tests Python OK, 2 omitidos**; incluye nuevos casos B05–B08 y el contrato existente.
- **9 suites JavaScript OK**.
- **12 plantillas Jinja parseadas**; sintaxis Python válida.
- Manifiesto SHA256 del release y extracción ZIP verificados.
- **No se efectuó prueba HTTP real de Flask/FastMCP** en este entorno: falta instalar esas dependencias. La conexión Google Sheets actual se inspeccionó por el conector del chat, no mediante el servicio Render desplegado.
- **GitHub/Render:** pendientes de publicación, smoke test y validación del diagnóstico autenticado en producción.

## Verificación posterior al despliegue

1. `/health`: `version=2.0.30`, `release_assets.consistent=true`, servidor `UP`; `deep_check_status=NOT_CHECKED` antes de activar diagnóstico profundo.
2. Autenticarse y consultar `/api/health/diagnostics`; revisar las tres fuentes y estados de módulos, sin asumir que `DEPENDENCIES_OK` equivale a ejecución real certificada.
3. `/mode/portafolio`: comprobar el aviso `HOMOLOGACION STALE` si el MASTER conserva referencias previas y la etiqueta `HISTÓRICO NO SPOT`.
4. Simular un proveedor Spot caído en staging: comprobar `DATA_ERROR`, código de incidente y ausencia de valores parciales.
5. No se envía, modifica ni cancela ninguna orden; no se cambia la custodia.
