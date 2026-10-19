# KairosWeb v2.0.17 — Release completo GitHub

**Versión de aplicación:** 2.0.17. **Schema Master:** 5.0.0 (sin cambio). Partir del código de este ZIP completo, desplegando su contenido descomprimido en GitHub; conservar la estructura de carpetas (`static/`, `templates/`, `tests/`). No usar este ZIP, imágenes ni instantáneas locales como fuente para balances o cotizaciones: solo Google Sheets original PUBLICADO + MCP Spot.

## Cambios desde v2.0.16

### Compras: slider como porcentaje de liquidez

- El slider va de **0% a 100% del USDT disponible para Compras**, no del patrimonio total. La liquidez máxima es USDT físico menos Reserva Trading QF una sola vez. A 0%, presupuesto USDT $0; a 100%, todo el disponible elegible como presupuesto *teórico*.
- El capital del slider llena las cestas **secuencialmente O2C1 (Fib 38.2%) → O2C2 (50%) → O2C3 (61.8%) → O2C4 (78.6%)**, sin pasar a la siguiente antes de completar el cupo de la anterior. Los cupos se calculan con los porcentajes aplicados a la totalidad de USDT disponible, no al importe parcial del slider.
- El editor de porcentajes permite redactar los cuatro valores **sin modificar automáticamente los demás**. Al sumar exactamente 100.00% se activa «Aplicar porcentajes»; también se puede «Restaurar porcentajes del Master». Solo afectan esta simulación y no escriben al Master.
- Se mantienen sincronizados tarjetas, matriz Fibonacci, pesos simulados y gráficos inferiores con la distribución seleccionada. El enlace a Forecast mantiene su escala de patrimonio mediante conversión independiente.
- Compras efectivas hipotéticas: solamente tokens INFRA (según la banda vigente), límite por déficit/target, rebalanceo secuencial y QF protegida. Un importe teórico sin compra elegible permanece en USDT. Pivotes PROPUESTO solo habilitan simulación, **nunca órdenes reales**.

### Órdenes (sin cambios desde v2.0.16)

- Las propuestas BUY / SELL siguen siendo *simuladas*. Resumen con USDT compra y unidades venta, y backlog con filtro Nivel, Exchange, Tier, Operación y Token.
- Ventas limitadas al Exchange libre; BTC NEVER SELL, HODL/Core protegidos. Precio LIMIT mostrado no es orden enviada.

## Instalación y verificación

1. Descomprimir el ZIP y reemplazar los archivos en el repositorio GitHub. Hacer Commit/Push y desplegar Render. No subir contraseñas ni tokens al repositorio.
2. Consultar `/health`: debe indicar `version: 2.0.17`, `status: UP`, y `release_assets.consistent: true`.
3. Comprobar Compras con 0%, 50% y 100% de USDT disponible, secuencia C1→C4, edición fija de mezcla (p.ej. 50/20/20/10), opción Aplicar y Restaurar, pesos y gráficos.
4. Comprobar que el slider de Ventas sigue basado en su objetivo patrimonial y que Órdenes no envía operaciones.
5. Comprobar los conectores MCP de producción por separado, en especial Hyperliquid HYPE/USDC: pasar pruebas locales no implica acceso operativo desde Render.

**Integridad:** manifiesto de todos los archivos con SHA-256 y `SHA256SUMS.txt`; ZIP con un máximo de 99 archivos. Construir este release **no despliega** ni modifica Google Sheets, GitHub, Render, exchange, órdenes o fills.
