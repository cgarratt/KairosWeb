# KairosWeb v2.0.32 — Allocation 6+6 y unidades estimadas de venta

**Tipo:** release de interfaz sobre v2.0.31 (homologación automática conservada).

## Cambios

1. En `/mode/portafolio`, donut de allocation con **USDT en fila independiente** y leyenda de los 12 tokens dividida en **dos columnas de seis**, sin scrollbar vertical. Colores, valores Spot, porcentajes y 13 sectores del donut no cambian; QF se contabiliza una sola vez.
2. En `/mode/balancer`, sección **4. Candidatos de venta**, nueva columna **Unidades estimadas**. Usa `r.units` calculado por `overweight_sell_plan`; no vuelve a dividir utilizando otro precio ni modifica las restricciones. Filas sin valor de venta indican «—»; en el total no se agregan unidades de distintos activos.
3. `/health` verifica las dos nuevas marcas de la interfaz para detectar despliegues parciales.

## Seguridad y limitaciones

- Ventas y transfers siguen siendo propuestas. BTC NEVER SELL y HODL/Core protegidos. Cupos Tier (T1 30%, T2 70%, T3 100%), Exchange libre y reservas SELL sin cambios.
- Cantidades estimadas al Spot MCP: **no** son órdenes LIMIT ni cantidades ajustadas a reglas de lot size, comisiones o mínimos del exchange.
- Google Sheets `KAIROS_V5_MASTER` schema 5.0.0 sigue siendo fuente única de posiciones. El release no escribe Google Sheets ni realiza operaciones.
- La visualización se vuelve una columna en pantallas estrechas para evitar cortes; el reparto horizontal de seis y seis se conserva en escritorio.

## Verificación local

- Python: 206 pruebas aprobadas, 2 omitidas; pruebas específicas del render de 6+6, 13 sectores, USDT único y unidades de venta.
- JavaScript: 9 suites aprobadas.
- Jinja: 12 plantillas analizadas.
- ZIP: 99 archivos; SHA256 por archivo y extracción completa verificados.
- HTTP real en Render: **pendiente**. GitHub/Render: **no desplegado**.
