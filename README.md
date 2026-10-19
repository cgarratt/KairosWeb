# KairosWeb v2.0.16 — paquete para GitHub

**Release completo** acumulado desde v2.0.15. Contrato Google Sheets **schema_version=5.0.0** sin cambios. Conservar rutas `static/`, `templates/`, `tests/` y `render.yaml`. Actualización de código **no equivale** a despliegue en GitHub/Render.

## Cambios v2.0.16

### Modo Órdenes (fase 1; propuestas SIN ejecución)

- Resumen «Próximas órdenes por Token»: columnas **USDT compra** y **Unidades venta** desde la propuesta seleccionada. Una extensión SELL sin tamaño aprobado muestra **POR DEFINIR** y no inventa unidades.
- Backlog «Backlog de Ordenes Compra / Venta»: filtro **Nivel** combinado con Exchange, Tier, Operación y Token desplegable.
- BUY estructurales: presupuesto por tramo y balanceo secuencial con token INFRA, target y QF; BUY Balance se limita asimismo a déficit y objetivo. SELL Balance respeta Exchange libre, BTC NEVER SELL y custodia protegida.
- El motor no crea órdenes ni altera fills; el nombre «Backlog» designa propuestas hipotéticas.

### Modo Compras (simulación local)

- Los 4 porcentajes del «Resumen de compras» son **editables**; al cambiar uno, se reajustan proporcionalmente los otros tres, sumando siempre **100.00%**.
- El porcentaje inicial de O2/O4 proviene de los parámetros aprobados del último Master PUBLICADO. «Restaurar porcentajes del Master» revierte cambios locales. **No se escriben** cambios a Google Sheets.
- Se actualizan tarjetas USDT C1–C4, matriz de precios, pesos post-compra, distribución por token y liquidez proyectada al cambiar porcentajes o slider.
- El importe teórico se distribuye al 100% entre los cuatro tramos; las compras efectivas simuladas siguen acotadas por INFRA, déficit, balanceo secuencial y USDT disponible menos QF. El excedente no asignable permanece en USDT.
- Los ajustes interactivos en Compras **no constituyen órdenes reales** y no representan automáticamente nuevas propuestas en Órdenes sin volver a calcular con los parámetros publicados.

## Verificación de despliegue

1. Descomprimir el ZIP y reemplazar los archivos del repositorio, respetando sus rutas. No publicar el ZIP cerrado como sustituto del código fuente.
2. Commit / push y desplegar Render; nunca incluir credenciales en el repositorio.
3. Abrir `/health` y comprobar `version=2.0.16`, `status=UP`, `release_assets.consistent=true`.
4. Revisar en Compras valores iniciales publicados, edición de mezcla (por ejemplo C1 20→50), conservación 100%, gráficos y «Restaurar»; en Órdenes, verificar columnas, filtro Nivel y ausencia de ejecución.
5. La verificación HTTP en producción y el funcionamiento de proveedores MCP privados se deben comprobar **después del despliegue**; los tests locales no los certifican.

**Datos:** solo Google Sheets ORIGINAL `KAIROS_V5_MASTER` PUBLICADO y proveedores MCP Spot; los ZIP no son fuentes de inventario ni precios. No se alteran Google Sheets, GitHub, Render o exchanges por crear este archivo.

**Integridad:** paquete de 99 archivos (menos de 100), con `RELEASE_MANIFEST_v2.0.16.json` y `SHA256SUMS.txt`.
