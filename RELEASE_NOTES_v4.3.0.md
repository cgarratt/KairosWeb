# KairosWeb v4.3.0 · Valores, ADX y resumen de operaciones

Base v4.2.0. RSI, RSI-MA, K y D visibles con dos decimales en sus tarjetas. Tercera tarjeta ADX Wilder (14), con valor, aguja y referencia de umbral 23. Balancer 1D, Compras/Ventas 1W; solo cierres UTC completos.

ADX mide fuerza, no dirección. La interpretación aplicada del nuevo umbral es: ADX <=23 → NEUTRAL; ADX >23 confirma COMPRAR/VENDER únicamente si las reglas RSI/Stoch originales se cumplen. Si no hay alineación, ESPERAR. Datos necesarios ausentes → N/D. Se compara sin redondear. BTC NEVER SELL sigue bloqueando cualquier venta técnica de BTC. No se genera dirección automáticamente solo por superar 23.

ADX se calcula desde los máximos, mínimos y cierres del mismo proveedor que alimenta el RSI (históricos KuCoin primario/Binance respaldo). Semanas: máximos y mínimos reales de los siete días cerrados, cierre del domingo y apertura del lunes UTC. No se sustituye high/low por el cierre. Faltan OHLC válidos: ADX N/D, conservando RSI/Stoch cuando son válidos. No se requiere modificar MCP.

Resumen técnico: explicación de señal y condiciones que faltan. Resumen de operaciones Balancer: compras con caja actual, ventas por composición, compras condicionales tras ventas y cantidad de movimientos de custodia propuestos. Escenarios independientes: no sumar compras actuales y condicionales. Compras/Ventas: resumen actualizado con el slider, presupuesto, asignación, remanente, caja posterior, token, tramos/unidades o prioridad/etapa según modo. Los resúmenes monetarios conservan el control de privacidad.

La señal BTC aporta contexto y no se presenta como señal individual de cada altcoin. Los motores existentes de asignación no cambian; las propuestas siguen sujetas a INFRA/SOBRE, caja no QF, compromisos, topes Exchange/Tier y protección Core/HODL. Sin escritura en MASTER ni órdenes a exchange.

Instalar: descomprimir el paquete de despliegue y subir su contenido a la raíz del repositorio Web existente. Conservar variables/secretos; desplegar en Render. Verificar /health version 4.3.0 y release_assets.consistent=true. Actualizar históricos en Configuración y recargar las tres páginas. No hace falta instalar un nuevo MCP ni activar TradingView. TOTAL2 sigue retirado.

Pruebas locales y límites: ver VALIDACION_RELEASE_v4_3.json. Sin comprobación visual en navegador, datos de cuenta privados ni despliegue remoto. Parámetros ADX (14) y umbral 23 corresponden al contexto técnico de esta versión, no a una publicación de política financiera en MASTER.

Fuente de la distinción fuerza/dirección: https://www.tradingview.com/support/solutions/43000589099-average-directional-index-adx/
