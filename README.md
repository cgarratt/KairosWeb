# Kairos Web v3.9 — Balancer, Compras y Ventas

Mantiene la arquitectura de v3.8 y sus conexiones MCP.

## Cambios

- Balancer: el monto USDT referencial por token se muestra según la bolsa **nominal** de 5% P, aunque el gasto habilitado sea cero. Conserva WATCH cuando el piso de liquidez impide compras. NO considerar referenciales como órdenes disponibles.
- Compras: slider de 0% a 15% de P (40% P - 25% P del capital operativo), montos C1/C2 recalculados inmediatamente en proporción 60%/40% con límites por déficit estimado. Reserva Trading y piso USDT se informan separadamente. Los montos del slider son **simulaciones teóricas**, no uso real de caja.
- Ventas: slider del objetivo de USDT desde 40% hasta 100%, predeterminado 40%; simulación de ventas según exceso de peso y unidades Exchange declaradas. BTC NEVER SELL; no afecta Core/HODL.
- Escenarios y tablas recalculados en el navegador. No modifica ninguna orden o estado de custodia.

## Límites pendientes

Snapshot del 15 de octubre; pendiente de reconciliación de fills, órdenes LIMIT/SELL y transferencias confirmadas. Las propuestas de Compra no incluyen precios aprobados de O2/O4. El slider de Ventas utiliza cantidades Exchange declaradas sin restar SELL pendientes. La capacidad de compra real debe proteger el piso de 40% USDT y reservas verificadas.

## Despliegue

Reemplazar los archivos del repositorio KairosWeb por el contenido de esta carpeta. Mantener las variables Render actuales.
