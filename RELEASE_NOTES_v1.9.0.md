# KairosWeb v1.9.0 · Notas de entrega

**Base:** v1.8.0. **Schema Google Sheets:** `5.0.0` (sin modificación). **Alcance:** presentación y semáforo informativo del Forecast; no mueve posiciones, custodia, órdenes, fills, ni cambia políticas financieras.

## Cambios acumulados

1. **Mejora 42 — Cabecera:** debajo del logotipo/nombre se muestra exclusivamente `v1.9.0` (y de forma dinámica las versiones futuras). Se retira «Google Sheets Master · Spot por MCP».
2. **Mejora 43 — Semáforo Fibonacci O2:** en Forecast, las cuatro columnas **Precio** 38.2%, 50%, 61.8%, 78.6% pintan **verde** si el Spot observado está en/por debajo del nivel, o si en una evolución futura existe un mínimo post-O1 verificado; pintan **ámbar** si el Spot está a ≤1% **por encima** de un nivel no alcanzado. Sin color para precios N/D o más distantes. No pinta columnas USDT ni totales. Tooltips muestran el motivo. Las referencias O2 derivadas de anclas históricas son hipotéticas y **el verde por Spot no certifica un toque histórico post-O1**; si el precio bajó y rebotó, no se marca sin evidencia histórica explícita.
3. **Mejora 44 — Distribución de Liquidez:** las tres tarjetas se titulan exactamente **Presupuesto Compras**, **Reserva Balancer** y **Reserva Trading**. Se conservan importes, porcentaje calculado sobre **USDT físico**, cálculo 25% P, reserva QF y alerta de sobredemanda de caja. No se reformula la contabilidad de liquidez.

## Seguridad y compatibilidad

- Datos siempre desde `KAIROS_V5_MASTER` publicado y MCP Spot vigente; sin cambio de contrato ni desactivación de validaciones.
- BTC NEVER SELL, HODL/Core, QF y distribuciones O3/O5 permanecen iguales a v1.8.0.
- Forecast continúa **simulación sin escrituras al Master**, sin órdenes automáticas, ni certificación de Elliott.
- Semáforo no habilita operaciones. Se aplica con evidencia conservadora del Spot; no sustituye a un histórico certificado desde O1.
- No se realizan cambios en el Master, GitHub ni Render al generar el archivo; debe desplegarse explícitamente.

## Pruebas

- Regresión Python, suite JS, pruebas Chromium de Forecast, versión/labels y tabla ejecutiva.
- Pruebas de frontera del semáforo: N/D, toque exacto, spot por debajo, proximidad 1%, fuera de rango, mínimo post-O1 solo con evidencia explícita.
