# KairosWeb v2.0.9 — Órdenes consolidadas, Fase 1

## Incluye, acumulativamente
- Todas las funciones operativas y de presentación de v2.0.8: Compras con pares semanales PROPUESTO/VALIDADO/CONFIRMADO aptos **solo para simular** (N/D bloqueado), Ventas sin filtro de pivotes, estado CL/O1–O5, liquidez QF protegida, alertas 1H/4H/1D y donut integral.
- Nueva pestaña **Órdenes**: bandeja única de propuestas **NO COLOCADAS** dividida en Balance de portafolio y Estructura de precio.
- Balance: BUY/SELL por ponderación; los SELL respetan Exchange libre, custodia protegida y BTC NEVER SELL; no inventar LIMIT de venta si Balancer no lo define.
- Estructura 1W: BUY LIMIT propuestos por retrocesos Fibonacci de pivotes; SELL por extensiones O3/O5 con anclas publicadas o extensión genérica semanal si existe pareja trazable, sin llamar a esta última onda Elliott certificada.
- Proximidad ±1% (estado informativo); objetivos ya superados no son futuras órdenes; tabla de referencia más cercana por token o N/D.
- Venue declarativo Binance / KuCoin / Hyperliquid (HYPE macro cotiza USDC); no confundir con saldos privados o conciliación.
- Inspección en `/health` de código, plantilla y filtros del nuevo módulo para detectar despliegues parciales.

## No implementado en fase 1
- Colocación, cancelación o edición de LIMIT en exchanges.
- Acceso a cuentas privadas, reserva real de caja, acreditación de fills.
- Tamaño o monto de ventas estructurales sin política autorizada. Permanecen POR DEFINIR.

## Despliegue y pruebas
- Subir todos los archivos de este ZIP a la raíz del repositorio GitHub, conservando `templates/`, `static/` y `tests/`; **no subir credenciales**.
- Confirmar Render `/health`: `version=2.0.9`, `status=UP`, `release_assets.consistent=true`.
- Probar `/mode/ordenes`: filtros, parejas Precio/Spot, estrategias independientes, 12 tokens, N/D cuando falten pivotes, protección de BTC y QF.
- La release es código para desplegar, no un despliegue ni certificación automática en producción.
