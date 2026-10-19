# KairosWeb 2.0.12 · Compras P1/P2 y semáforos

**Base:** KairosWeb v2.0.11 + mejoras acumuladas de Compras (sin cambios en el Master). **Tipo:** release de código para GitHub, pendiente de validación HTTP y visual en Render.

## Cambios

1. Modo Compras: P1 acepta `PROPUESTO`, `VALIDADO` o `CONFIRMADO` para **simulaciones únicamente** cuando el precio y la fecha coinciden con el mínimo de una semana cerrada UTC. El P1 archivado MCP es sólo PROPUESTO; no certifica pivotes ni convierte histórico antiguo en ancla automáticamente.
2. P2: mayor máximo semanal cerrado posterior a P1 (precio superior), aunque sea PROPUESTO. Si falta cualquiera de los extremos, no existen semanas comparables o hay conflicto con ancla CONFIRMADO, bloquear simulación por token y mantener su cuota en USDT.
3. Tabla Fibonacci de Compras: precios y fechas de P1/P2, ambos con círculo de estado: rojo PROPUESTO, ámbar VALIDADO, verde CONFIRMADO. Distinto del color de fondo de toques históricos.
4. Restricción de balanceo: simular compras solo INFRA, hasta déficit de target por escalón; no duplicar liquidez, proteger QF y BTC NEVER SELL. Ventas ordinarias permanece **sin filtro semanal**.
5. Órdenes fase 1 solo propuestas; precio/importe no se convierte en orden de exchange. Sin modificar fills, custodias o Google Sheets automáticamente.
6. Diagnóstico `/health`: comprobar plantilla P1/P2 y motor de selección para detectar despliegues parciales.

## Validación

Incluye pruebas de regresión y manifiesto SHA-256. El despliegue en Render, conexión real MCP y sesión admin se validan por separado antes de certificar producción.
