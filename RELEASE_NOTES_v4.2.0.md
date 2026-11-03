# KairosWeb v4.2.0

Retira TOTAL2 de Balancer, Compras y Ventas. Elimina el cliente y contrato TOTAL2 Web, el endpoint de actualización y el botón asociado. La Web no requiere el puente MCP TOTAL2 ni alertas TradingView.

Dos velocímetros compactos en una fila: BTC/USDT RSI con RSI-MA y BTC/USDT Stoch RSI K/D. Balancer utiliza cierres diarios; Compras/Ventas semanas UTC completas lunes–domingo. Mismos parámetros: RSI Wilder 14, SMA RSI 14 y StochRSI 14/14/3/3. N/D sin agujas cuando no hay serie válida. El detalle mantiene fuente y cierre Lima/UTC.

Reglas técnicas conservadas: comprar si RSI<30 y RSI>MA y K>D; vender si RSI>70 y RSI<MA y K<D; otras combinaciones válidas esperar. BTC NEVER SELL bloquea la venta. Las recomendaciones no alteran cálculos de candidatos, presupuestos, caja, custodia, anclas ni órdenes.

Históricos requeridos: 250 cierres diarios o 80 semanas completas. Cargar preferiblemente 999 días. No hay llamadas adicionales al navegar y no se requiere un nuevo MCP. La documentación de releases anteriores es histórica.

Instalación: seguir README.md. No se ha desplegado en GitHub/Render ni desactivado alertas remotas en TradingView desde este trabajo.
