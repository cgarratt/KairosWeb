# KairosWeb v2.0.15 — GitHub release

**Paquete completo** para reemplazar la fuente de KairosWeb desde v2.0.14. Mantener las rutas `templates/`, `static/`, `tests/` y `render.yaml`. La versión de producto es **2.0.15**; el contrato Google Sheets permanece en `schema_version=5.0.0`.

## Qué cambia

- **Compras:** título «Maestro de Precios - Retrocesos Fibo». El color histórico post-P2 es uniforme en **Precio, % Peso y USDT** para los cuatro escalones.
- **Liquidez y presupuesto:** un único máximo disponible `USDT físico − Reserva Trading QF`. El slider elige el presupuesto teórico sin descontar primero los tokens bloqueados; el 100% de ese presupuesto se reparte en Fib 38.2/50/61.8/78.6 según los parámetros **aprobados del Master**. **La ejecución hipotética** se limita a tokens INFRA y a sus déficits; lo que no pueda comprarse se mantiene en USDT, sin forzar exceso de target.
- **Órdenes, resumen:** título «Próximas órdenes por Token», columna «Nivel» inmediatamente después de «Origen» y descripción Fibonacci de C1/C2/C3/C4 y EXT1W1..4.
- **Órdenes, listado:** título «Backlog de Ordenes Compra / Venta»; filtros simplificados **Exchange, Tier, Operación y Token** (combo de los 12). Se retiran «Vista rápida», «Origen», «Grupo» y «Proximidad». «Limpiar filtros» restaura los cuatro selectores.
- **VIRTUAL y HYPE:** se agregan regresiones de la elegibilidad semanal bajo la estructura publicada de VIRTUAL y HYPE/USDC Spot. No modificamos pivotes ni suplimos información ausente del MCP. Cualquier fallo real de red o proveedor en Render requiere diagnóstico posterior a instalar este paquete.

## Restricciones que se mantienen

Compras usa P1 mínimo semanal fechado (PROPUESTO, VALIDADO o CONFIRMADO) y P2 máximo de las semanas completas posteriores; PROPUESTO habilita **solo simulación**, no LIMIT real. Solo INFRA, límite por déficit y QF protegida. No mezclar HYPE/USDC Spot macro con el precio Binance HYPEUSDT para medir distancia. BTC NEVER SELL, HODL/Core protegidos, Ventas ordinarias sin filtro pivotes. Toda la sección Órdenes sigue siendo **solo propuestas, sin ejecución**.

Google Sheets ORIGINAL `KAIROS_V5_MASTER`, `01_CONTROL` PUBLICADO, hojas de inventario y parámetros, y MCP actuales siguen siendo la única fuente de datos financieros. Los ZIP y capturas **no son datos de mercado ni de saldos**. El ZIP no modifica Sheets, GitHub o Render por sí solo.

## Instalación y comprobación

1. **Descomprimir** el ZIP y reemplazar los archivos del repositorio respetando la estructura. No subir un ZIP cerrado como sustituto de los archivos fuente.
2. Commit/Push y esperar el despliegue de Render. No incorporar credenciales al repositorio.
3. En `/health` verificar `version=2.0.15`, `status=UP` y `release_assets.consistent=true`.
4. Comprobar Compras (presupuesto teórico vs USDT asignable por INFRA), VIRTUAL (CL/O1/O2 nuevos del Master) y HYPE (Hyperliquid Spot HYPE/USDC); en Órdenes, comprobar combos de cuatro filtros y resumen por token. Revisar consola/logs y el mensaje de bloqueo en N/D si persistiera un fallo MCP.
5. No se ha realizado verificación HTTP de producción desde este entorno. No dar por certificados el despliegue ni la conexión privada MCP antes de hacerla.

**Control de paquete:** GitHub ZIP de 99 archivos (máximo autorizado: menos de 100) con `RELEASE_MANIFEST_v2.0.15.json` y `SHA256SUMS.txt`.
