# KairosWeb v2.0.7 · GitHub release compacto

Se basa íntegramente en v2.0.6 y conserva donut, campana multiframe, pivotes publicados y verificación CL. **Nueva regla exclusiva Compras:** filtro previo de los últimos dos pivotes semanales 1W 5L/5R+BOS formando LOW→HIGH; O2/O4 o RETROCESO_ALCISTA con pesos O2 por defecto. Si no hay estructura válida, compra 0; caja bloqueada NO se redistribuye. Ventas ordinarias no exige pivotes. Las semanas incompletas no cuentan. HYPE usa Hyperliquid Spot HYPE/USDC.

Para subir: extraer archivos a la raíz de GitHub, conservando estructura templates/ static/ tests/. No subir secretos. Desplegar en Render y validar `/health` = 2.0.7 y `release_assets.consistent=true`; probar Compras (tokens sin BOS deben mostrar BLOQUEADO y $0) y Ventas sin cambios. Las señales técnicas simuladas **NO** certifican órdenes ni fills. Sin cambios al Master, exchanges o cuentas.
