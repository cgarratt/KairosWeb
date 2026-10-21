# KairosWeb v2.0.21 — Custodia Balancer

Nueva sección en `/mode/balancer`: por cada token y componente HODL/Core/Exchange se muestra unidad actual, ideal nominal `04_CUSTODIA`, y propuesta alcanzable sin retirar Core/HODL, más tabla de movimientos Exchange→HODL/Core. Las cifras de inventario se toman únicamente del MASTER nativo PUBLICADO `02_POSICIONES`; no se cargan desde ZIP.

Garantías: no sale custodia protegida, no se transfieren unidades automáticamente, no se mezclan con compras/ventas hipotéticas, no se cambian saldos ni fills. Cualquier orden SELL sin conciliar bloquea lectura operativa del MASTER.

El ZIP es código para GitHub; no publica automáticamente Render.

## Compatibilidad corregida

El panel de custodia se renderiza exclusivamente si `payload.custody_comparison` está presente. Las vistas con datos legados mantienen presupuesto, compras y ventas sin fallos de plantilla. Compatibilidad verificada con la regresión completa.
