# KairosWeb v4.6.3 · Compras proporcional por venue

Base v4.6.2. Mantiene selección dinámica CL/O1 en O2 y O2/O3 en O4.

- Distribución simultánea proporcional al déficit USD de INFRA elegibles, con techo por déficit y tramo. Sin ranking por drift ni prioridad por fila.
- Caja USDT libre por venue: QF protegida, compromisos BUY descontados una sola vez y cuarentenas conservadas. Respeta la extensión Balancer utilizable de Compras.
- Una caja decreciente compartida por los cuatro tramos. Si un venue limita, reducir proporcionalmente y redistribuir solo a déficits con caja en su propio venue.
- Mismo cálculo en tabla de Compras, propuestas estructurales de Órdenes y KairosGPT1.3.21.
- Tabla de caja inicial, asignación y remanente por venue; venue junto al token.
- Sin transferencias supuestas ni USDC=USDT. HYPE Spot Hyperliquid USDC no recibe asignación desde esta caja USDT sin financiación homologada.

## Instalación
Descomprimir el ZIP y reemplazar los archivos del repositorio conservando su estructura. No subir el ZIP como aplicación. Publicar/desplegar mediante el flujo GitHub/Render existente. No requiere cambiar schema, MCP, saldos ni pivotes. Después del despliegue comprobar versión4.6.3 y health/consistencia de assets; contrastar tabla Compras y Órdenes con el mismo snapshot/Spot.

## Validación
Pruebas de caja insuficiente, proporcionalidad, invariancia al orden, tramos secuenciales, compromisos/QF, estados y paridad Python/JavaScript. 120 escenarios deterministas adicionales dentro de la prueba de paridad. Compilación de Python/JS, render de plantilla y marcadores de assets.

Estado: SOURCE_RELEASE. Sin publicación GitHub ni despliegue remoto realizados desde este paquete. MASTER sin cambios. Ver VALIDACION_RELEASE_v4_6_3.json.
