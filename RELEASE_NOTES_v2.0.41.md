# KairosWeb v2.0.41 — Reserva Balancer automática y Configuración oscura

## Funcional
- Liquidez Balancer aprobada: `ROUND(USDT_físico_total × PORTFOLIO_LIQ_BALANCER_FRACTION, 2)`; **20%** vigente. QF contado una vez, siempre protegido y sin crear USDT.
- La asignación se obtiene de porcentajes APROBADOS del MASTER y se recalcula al cambiar USDT físico o mezcla. Si faltan o son inválidos, no se inventa saldo ejecutable.
- Compras consume primero caja semanal y luego Balancer disponible; Balancer usa solo su porción y ventas propias realmente acreditadas.
- Desaparece el segundo input de asignación manual de USDT. Se visualiza automáticamente el monto derivado y los importes físicos de referencia.
- El panel de objetivos ahora respeta el tema oscuro, incluidos formularios y avisos.

## Seguridad
- No modifica saldos, posiciones, liquidaciones o órdenes; conserva protecciones BTC NEVER SELL, HODL/Core y QF.
- El MASTER debe tener aprobadas y conciliadas las tres claves de mezcla. La fila legada `BALANCER_RESERVE_ASSIGNED_USDT` puede tener fórmula dependiente del saldo y porcentaje aprobados, no duplicar dinero.
- Realizar pruebas de `/health`, Configuración, Balancer, Compras y selector de tema en Render después del despliegue.
