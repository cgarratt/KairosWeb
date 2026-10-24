# KairosWeb v2.0.40 — Liquidez compartida con QF protegida

## Alcance
- Tres bolsas contables: USDT semanal O2/O4, Reserva Balancer y ReservaTrading QF.
- Compras: `max(0, USDT físico − QF − compromisos verificados)`; consume primero semanal, luego Balancer.
- Balancer: compras limitadas exclusivamente a `BALANCER_RESERVE_ASSIGNED_USDT` APROBADO (menos compromisos), más ingresos de ventas propias **solo tras fill**. Ingresos simulados aparecen por separado y no se acreditan.
- Gestión del portafolio: editar porcentajes objetivo sin suplantar los saldos; agregar campo separado para asignar USDT a Balancer, con aprobación administrativa y validación `0 <= asignación <= USDT operativo`.
- Candado conservador: si el Master no tiene asignación Balancer APROBADA, Balancer BUY es USDT 0 hasta publicar el importe. Compras mantiene el presupuesto global no-QF.
- BTC NEVER SELL, HODL/Core, límites Exchange/Tier, pivotes y ninguna orden automática permanecen iguales.

## Despliegue
- MASTER schema 5.0.0 permanece igual. Activar nueva política del presupuesto en `12_PARAMETROS_KAIROS` con publicación auditada, sin escribir unidades/saldos.
- Tras desplegar, ingresar a Configuración → Objetivos de gestión y publicar un importe Balancer; el porcentaje de reserva por sí solo **no asigna** fondos.
- Verificar `/health` y escenarios Balancer/Compras en Render. Entorno local no reemplaza validación MCP real.
