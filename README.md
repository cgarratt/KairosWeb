# KairosWeb v2.0.14 — release GitHub

**Base:** KairosWeb v2.0.13. Este ZIP contiene el proyecto completo; preservar rutas `static/`, `templates/` y `tests/` al reemplazar archivos en GitHub. No instalar o guardar credenciales en el ZIP. Google Sheets sigue siendo la fuente única de saldos, liquidez, custodia, parámetros y estados de pivotes. Spot exclusivamente MCP.

## Cambios acumulados

### Modo Compras · Matriz de precios Fibo - Onda 2
- Título actualizado y cabeceras P1/P2 simplificadas. Se conservan los semáforos de estado exclusivamente junto a **P1/P2**.
- Cuatro columnas nuevas de **% Peso**, una por tramo: peso en la manga cripto calculado después de las compras hipotéticas acumuladas hasta ese tramo, revalorizando unidades con los precios del escenario. NO representa el peso actual al Spot.
- Los precios Fibo ya no muestran círculos de desviación. Las celdas verdes solo significan que una vela diaria cerrada posterior a la fecha de P2 tuvo un mínimo <= al nivel. Ámbar = mínimo histórico posterior a P2 a menos del 1%; no indica que el Spot actual esté cerca, ni un fill ni permiso de ejecución.
- Restricciones existentes de Compras inalteradas: P1 semanal fechado puede ser PROPUESTO/VALIDADO/CONFIRMADO, P2 máximo semanal cerrado posterior, déficit INFRA y QF protegida, sin órdenes automáticas.

### Modo Ventas
- Tarjeta **Objetivo USDT** ahora indica **importe monetario objetivo ($) y porcentaje entre paréntesis**, con patrimonio Spot publicado en el escenario. Solo modifica presentación; no altera el motor SELL, Core ni BTC NEVER SELL.

### Modo Forecast
- Título **Simulación - Ondas Elliott**.
- Se retira la columna independiente Estado de la tabla Cycle Low a O5; se conservan los candados/estados junto al precio del pivote VALIDADO/CONFIRMADO y la protección efectiva del motor.

### Modo Órdenes (FASE 1)
- Título **Listado de próximas órdenes a ejecutar**, siempre señalado como listado hipotético NO colocado ni autorizado.
- Tabla consolidada de filas: evita seis tablas extensas organizadas por exchange/origen. Selección rápida: Todas, Precios O2, Binance, KuCoin, Hyperliquid, T1/T2/T3 y tokens individuales como Precios VIRTUAL.
- Filtros combinables: Exchange, origen, grupo O2/O3/O5/extensión 1W/rebalanceo, Tier, BUY/SELL, distancia y token, más limpiar filtros y contador de resultados.
- Semáforos de cercanía y badges BUY/SELL, BALANCE/ESTRUCTURA y estado. Colores de distancia **no son señales de ejecución**. Resumen técnico por token se mantiene.
- Limitaciones de seguridad: sin `place/cancel`, sin fills inventados; BALANCE sin LIMIT; SELL estructural sin tamaño aprobado; HYPE USDC macro no se compara con Binance USDT Spot.

## Despliegue y comprobaciones
1. Reemplazar los archivos del repositorio GitHub por el contenido **descomprimido** del ZIP, preservando `templates/`, `static/`, `tests/` y `render.yaml`.
2. Desplegar Render sin introducir claves en el repositorio.
3. Abrir `/health`: esperar `version=2.0.14`, `status=UP`, `release_assets.consistent=true`.
4. Comprobar Compras (semáforos P1/P2, 4 pesos post-compra, histórico post-P2), Ventas (importe objetivo), Forecast (título y tabla) y Órdenes (combinar vistas como O2 + Binance y T1 + KuCoin).
5. Confirmar visualmente los resultados con el Master/MCP reales en Render; las pruebas locales no certifican esa integración remota.

**Control de paquete:** menos de 100 archivos incluyendo `RELEASE_MANIFEST_v2.0.14.json` y `SHA256SUMS.txt`. No se modifican automáticamente el Master, las órdenes ni la custodia.
