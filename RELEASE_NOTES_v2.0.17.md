# KairosWeb v2.0.17 — Notas del release

## Alcance

Actualización sobre v2.0.16 enfocada en simulación de **Compras** sin modificar posiciones, liquidez real, parámetros oficiales, Forecast, ejecución de órdenes o contrato de Sheets `5.0.0`.

- **Slider de 0–100% de liquidez** (USDT físico − QF). Antes se expresaba como porcentaje de patrimonio P. Ahora 100% equivale al máximo USDT disponible para Compras; 0% equivale a $0.00.
- **Presupuesto secuencial**: el importe seleccionado llena cupo O2C1, luego O2C2, O2C3 y O2C4; cada cupo se calcula sobre el disponible total y el reparto porcentual aplicable. Nunca asignar simultáneamente los cuatro tramos al mover parcialmente el slider.
- **Editor de porcentajes de 4 niveles**: acepta escribir libremente y conserva los cuatro valores mientras se edita. Se aplican solo tras pulsar «Aplicar porcentajes» con suma exacta 100%; botón «Restaurar porcentajes del Master» para recuperar los pesos oficiales de inicio. Ninguna edición escribe al Master.
- **Reactividad**: tarjetas de cesta, matriz Fib, importes efectivos sujetos a balanceo, pesos y gráficos se actualizan al mover el slider o aplicar un reparto válido. Los importes no asignables quedan en USDT sin forzar tokens sobreponderados.
- **Sin regresión en Ventas**: su slider mantiene objetivo patrimonial. **Sin cambio en Órdenes**: fase 1 de propuestas con precios de referencia, ninguna orden transmitida al mercado.

## Salvaguardas

- Máximo liquidez = USDT físico − QF descontado una única vez; no se confunde presupuesto teórico con compras realmente simulables.
- Comprar solo INFRA, respetar déficit y target, pesos recalculados por tramo; CL/O1 propuestos nunca autorizan ejecución.
- BTC NEVER SELL, Core/HODL protegidos, HYPE macro únicamente Hyperliquid Spot HYPE/USDC; sin inventar fills ni transferencias.
- Se mantienen fuente original Master Google Sheets PUBLICADO y Spot MCP.

## Pruebas / despliegue

Verificar tests Python, JavaScript, 13 plantillas y controles `/health`; auditar hashes SHA-256 en el ZIP. Validación HTTP real en Render requiere despliegue posterior. ZIP completo con máximo 99 archivos.
