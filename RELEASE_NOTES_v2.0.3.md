# KairosWeb v2.0.3 — Estados de ponderación en Fibonacci O2

Sobre la versión v2.0.2. En Compras, cada precio Fibonacci O2C1–O2C4 incluye etiqueta **SOBRE / INFRA / NEUTRAL**. El estado usa el peso de cada token dentro de la manga cripto ex-USDT **antes de asignar el USDT de ese escalón** (con las compras simuladas previas ya incorporadas), comparándolo con su target y la banda ±DRIFT_BAND_PP vigente del Master publicado. No se obtiene el indicador a partir del USDT asignado ni del Spot aislado.

Conserva el semáforo del nivel Spot/USDT; rojo en la pareja solo cuando el presupuesto es cero y el token está SOBRE según la banda, evitando contradicciones con la etiqueta. Nivel Fibonacci N/D no muestra etiqueta de estado. Los detalles del desvío (pp) están en el tooltip del indicador. No se actualizan órdenes, fills, posiciones ni Google Sheets. 

**Estado:** candidato para validación en Render, no desplegado.
