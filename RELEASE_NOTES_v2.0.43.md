# KairosWeb v2.0.43 — Órdenes: seguimiento y registro manual

**Tipo:** candidato de release, no instalado en GitHub ni Render. **MASTER v5.0.0** sin cambios por crear este ZIP.

## Cambio funcional

- Órdenes presenta ahora un registro persistente de estados **PROPUESTA → CONFIRMADA → PARCIAL → EJECUTADA**.
- Desde cada propuesta de Balance/Fibonacci el administrador puede **Registrar propuesta**. Desde el historial puede confirmar la orden colocada en el exchange, registrar fills parciales o registrar ejecución completa.
- Datos: exchange, token, BUY/SELL, tramo, origen, order ID, unidades previstas, importe previsto, unidades realmente ejecutadas por fill, USDT/USDC realmente empleados o recibidos, comisión en token/cotizada, evidencia y observaciones.
- Los registros viven en la nueva hoja **26_ORDENES_GESTION**, creada solo tras una escritura administrativa autorizada. Historial append-only con revisiones e identificadores únicos. Las órdenes FILLED anteriores siguen visibles y no se importan nuevamente.
- Escritura: requiere sesión administrativa adicional, CSRF válido, mismo origen, identidad Google con permiso de Editor, snapshot actual y versión de evento sin conflictos.
- Se rechazan orden Exchange ID duplicada, venta de BTC, sobreventa de unidades Exchange/Tier, desembolsos confirmados superiores a la caja publicada del venue, fills completos con cantidades inferiores a la orden, y cambios sin evidencia.
- `google_sheets_master` lee el nuevo historial opcional y **descuenta los importes BUY/SELL pendientes de la capacidad simulada**; conserva el esquema 5.0.0 y QF excluida. No se convierten USDC a USDT automáticamente.
- El registro no envía ni cancela operaciones en los exchanges. **EJECUTADA PENDIENTE_CONCILIACION** no modifica automáticamente las unidades reales de `02_POSICIONES`, caja de `03_LIQUIDEZ`, `05_ORDENES` ni `06_FILLS`: esos cambios requieren una conciliación verificable y una nueva publicación de snapshot. Esta separación impide duplicación de fills ya incorporados.

## Verificación

- Pytest: 250 aprobadas, 2 omitidas, 4 subpruebas adicionales.
- 9 suites JS aprobadas; 14 plantillas Jinja analizadas.
- Fuente actual `KAIROS_V5_MASTER`: no alterada por este release.
- Pruebas funcionales reales de autenticación/Google API/Render y conciliación extremo a extremo: pendientes.
- Propuesta de fase posterior: conciliación atómica de ejecuciones verificadas (05/06 + 02/03 + nuevo snapshot), cancelaciones y ajustes según LOT_SIZE/comisiones, **sin conexión para enviar órdenes remotas**.
