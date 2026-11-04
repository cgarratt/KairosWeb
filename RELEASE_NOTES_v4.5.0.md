# KairosWeb 4.5.0

Retira de Balancer, Compras y Ventas el contexto de mercado (RSI, Stoch RSI, ADX, Spot/STH/EMA), la recomendación conjunta BTC y el resumen adicional de operaciones mostrado en la captura. Retira también sus controles, recursos y endpoint de actualización STH.

Conserva simuladores, tablas originales, referencias de ondas, restricciones y cálculos de caja, compras, ventas y custodia. No modifica MASTER ni envía órdenes. No requiere actualizar los MCP.

## Despliegue

Descomprimir el ZIP y sustituir el contenido del repositorio Web, eliminando los archivos retirados indicados abajo. Conservar la configuración privada del entorno. Desplegar en Render mediante el procedimiento habitual del repositorio. Verificar /health y las tres páginas después del despliegue.

Archivos retirados: balancer_daily.py, adx_context.py, btc_references.py, glassnode_references.py, templates/_balancer_daily.html, static/balancer_daily.js y static/balancer_daily.css.

Este paquete es un release de código validado localmente; no acredita despliegue remoto ni conciliación contable.
