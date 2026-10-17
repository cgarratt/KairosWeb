# KairosWeb v2.0.0 — Release candidato

- Fibonacci O2 trasladado de Forecast al final de Compras, después de Distribución y Liquidez post-escenario.
- Spot MCP añadido después de Token.
- Color verde/ámbar aplicado a ambas celdas de precio y USDT si la asignación de ese tramo es positiva. Rojo en ambas cuando no existe asignación y el token está sobreponderado.
- Retiradas las notas amarillas Etapa 1/Etapa 2 y Alcance de simulación en Compras.
- Slider Compras disponible hasta USDT físico - reserva trading QF, sin techo fijo de 25% P.
- Forecast conserva trayectoria y simulaciones de ondas, pero no duplica la tabla de compras.
- Datos reales y precios requieren Google Sheets PUBLICADO y MCP en Render. Sin modificación de fuentes, órdenes o custodia.
- No desplegado automáticamente; verificar visualmente en Render antes de declarar producción.
