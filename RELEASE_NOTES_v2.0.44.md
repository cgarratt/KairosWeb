# KairosWeb v2.0.44 — Hotfix órdenes abiertas y reservas

- `01_CONTROL.ordenes_activas_declaradas` puede ser positivo si coincide con el número de órdenes pendientes verificables de `05_ORDENES`.
- Órdenes `PENDIENTE` sin Exchange Order ID son admisibles solo con referencia local determinística y evidencia. No se fabrican IDs de exchange.
- Las órdenes abiertas BUY reservan USDT y SELL reservan unidades; HYPE/USDC sin conversión verificada bloquea conservadoramente el presupuesto BUY simulado.
- Duplicados, compromisos inconsistentes, ejecuciones parciales sin conciliación, BTC SELL y sobreasignación siguen bloqueados.
- Los FILLED históricos conciliados continúan como evidencia sin duplicar inventario.
- El MASTER no se modifica; no se envían órdenes. Render y conciliación remota pendientes.

Validación local: 252 pruebas Python aprobadas, 2 omitidas, 9 suites JavaScript aprobadas.
