# KairosWeb v2.0.29 — Compactación Ventas y Spot MCP en Forecast

## Cambios

1. Eliminar la tabla secundaria de pesos antes/objetivo/después en `/mode/ventas`; conservar órdenes SELL con prioridad, pesos por orden, unidades y USDT. No modificar ni el motor matemático ni el objetivo USDT por defecto del MASTER.
2. Añadir al SVG de “Trayectoria del ciclo por token” en `/mode/forecast` una línea horizontal punteada con precio Spot actual del token seleccionado, leído del mismo payload Spot Binance MCP y hora de observación.
3. Escalar el eje Y con los niveles de CL/O1/O2/O3/O4/O5 más Spot válido, para representar correctamente precios fuera del rango hipotético.
4. Sin cotización válida: línea ausente, texto `Spot MCP N/D`. Los puntos Elliott, selectores y estados protegidos permanecen inalterados.
5. Nuevas pruebas para evitar regresiones y validación de `/health` orientada a recursos entregados.

## Restricciones

Solo UI informativa; sin acciones de trading, fills, movimientos de custodia o escrituras en Google Sheets. El precio Spot no sustituye un pivote del MASTER ni redefine retrocesos.

## Verificación local

- Python: 189 passed, 2 skipped.
- JavaScript: 9 suites passed (incluye pruebas de precio dentro/fuera de rango y precio ausente).
- Jinja: 12 plantillas parseadas.
- Integridad SHA256 de todos los archivos de código de la entrega.
- HTTP/Render: pendiente; este ZIP no publica automáticamente en GitHub.
