# KairosWeb v2.0.22 · Portafolio (layout aprobado)

Se implementan cuatro filas de gráficos tras los cuatro KPI de la sección `/mode/portafolio`:

1. Izquierda: **Composición del capital histórico** (donut 08_INTEGRAL). Derecha: **Allocation por token**, donut y leyenda ordenada (12 tokens + USDT físico una sola vez).
2. Izquierda: **Rentabilidad histórica del portafolio** (rango 7D/30D/90D/VTD/ALL). Derecha: **Resultado no realizado por token** (barras horizontales compactas).
3. Izquierda: **Distribución por categoría** (T1/T2/T3 real vs objetivos). Derecha: **Composición del portafolio** (12 tokens real vs objetivos, sin USDT).
4. Ancho completo: **Seguimiento del portafolio**: histórico certificado de patrimonio/liquidez, valor/costo abierto/PnL actual y detalle de conciliación por segmentos desplegable.

## Fuentes y seguridad de datos

- Inventario/costo/USDT/cuotas/targets: Google Sheets MASTER ORIGINAL `PUBLICADO`, schema 5.0.0. Precios SOLO Binance Spot MCP; ningún valor de captura/ZIP para saldos/precios.
- Donut de 13 componentes incluye USDT físico una vez (QF ya forma parte de ese importe); el donut histórico separa pérdida realizada de patrimonio vivo.
- Observaciones temporales: SOLO `21_PRI_HISTORIAL` con registro de valoración completa, positiva, conciliada y estado `OK`/`VALIDADO`/`CERTIFICADO`/`COMPLETO`. Excluye `DATA_ERROR_PARCIAL`, registros no certificados y puntos incompletos.
- Los registros actuales pueden ser insuficientes para construir línea histórica; en ese caso se muestra **Historial insuficiente**, sin inventar una rentabilidad. Los valores de patrimonio histórico no constituyen rentabilidad ajustada por aportes/retiros. Para una rentabilidad neta real futura se requieren flujos conciliados; los PnL y costos abiertos históricos no se infieren retroactivamente.
- Presupuesto O2C2 en KPI: únicamente referencia teórica del USDT operativo y porcentaje O2C2 publicado/aprobado; NO acredita orden o fill.
- No cambia configuración, snapshot, órdenes ni custodias del MASTER. Conserva Balancer custodia (v2.0.21), Ventas optimizadas, Compras/Forecast, Alertas y Órdenes.

## Despliegue

ZIP para extraer en raíz de repositorio y desplegar Render manualmente. Verificar `/health` con `version=2.0.22`, `release_assets.consistent=true` y claves `portfolio_layout_v2022` / `portfolio_allocation_v2022`. `status=UP` no certifica accesibilidad Google Sheets ni cotizaciones MCP, que siguen sujetas a validación por solicitud.
