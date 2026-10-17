# KairosWeb v1.4.0 — Fibonacci de compras/ventas por onda

**Estado:** Release empaquetado, pruebas locales superadas. **No desplegado a Render.**
**Origen:** v1.3.0; no altera KairosGPT, datos reales ni el snapshot publicado de Google Sheets.

## Cambios

1. **Compras O2/O4**: cada onda congela como techo **25% del patrimonio total P de esa onda** (cripto Spot + USDT físico, incluyendo QF una sola vez). Se utilizan solo los USDT realmente elegibles, **sin tocar la reserva Quantfury**, mostrando déficit si falta caja. El 25% no significa 25% de la liquidez. Distribución de cuatro retrocesos Fib **38.2, 50, 61.8, 78.6%** que suman exactamente **100% de ese presupuesto**. Una etapa no alcanzada NO se considera fill ni consume USDT.
2. **Ventas O3**: cuatro extensiones **1.618, 2.618, 3.618, 4.618**, distribución de referencia **40/30/20/10%** sobre unidades elegibles congeladas en Exchange libre, excluyendo BTC, Core/HODL. La simulación no continúa ventas dirigidas a la meta cuando los USDT alcanzan el objetivo publicado (actualmente 40% de P). Los tramos no alcanzados se conservan.
3. **Ventas O5**: cuatro extensiones análogas, distribución base **20/20/30/30%** del pool congelado de **Exchange y Core estratégico elegible**, siempre excluyendo BTC y HODL bloqueado. **No aplica el límite del 40% USDT a la liquidación final.** Los ingresos netos O5 siguen la regla aprobada **30% compra propuesta BTC / 70% USDT**; la simulación admite un selector hipotético alternativo sin editar esa regla del Master.
4. **Settings**: cuatro nuevos parámetros de Forecast en **Reglas y ventas O3/O5**. Muestran porcentajes con sumatoria 100 y fuente/estado. **No se añade nada al Google Sheet durante el despliegue.** Al modificar por primera vez una distribución desde Settings, la publicación administrativa (sesión activa, evidencia, validación y auditoría) crea su entrada `FORECAST_O{2,3,4,5}_FIB_ALLOCATION` en `12_PARAMETROS_KAIROS` junto con la revisión auditada. Los valores base actuales se presentan aunque la fila aún no exista. La lectura de parámetros en otros chats no está instalada automáticamente por este ZIP.
5. **Forecast interactivo**: nuevas 16 entradas de porcentaje (4 por onda), para simular sin modificar el Master; los resultados de la tabla O2, simulación integral de ventas/compras y capturas de custodia se recalculan. Si la distribución no suma 100, las tablas anteriores se ocultan. La tabla independiente de custodia **Post-O5** se retira; se conserva la sección **Composición final Post-O5**, incluyendo solo como hipótesis terminal la liquidación de Core/Exchange restante.
6. **Fibo 78.6%**: nueva referencia operacional del simulador, conservando el valor histórico 78.2% solo como legado/evidencia; `forecast_math` ahora proporciona `ref786` sin destruir `ref782` histórico.
7. **O1 preliminar**: después de recuperar candidatos archivados desde `07_PIVOTES`, la página Pivotes solicita automáticamente máximos posteriores a CL que faltan, token por token y en segundo plano. Conserva correcciones manuales/valores oficiales; nunca declara pivotes certificados. El MCP puede fallar o tardar: se muestran avisos individuales sin inventar resultados.

### Restricciones importantes

- Todo es **escenario hipotético**. No crea, modifica, cancela ni confirma operaciones, fills o transfers.
- BSI SELL sigue BLOQUEADO y TradingBot sigue WATCH donde corresponda.
- Los niveles O2 se derivan de referencias C1/C2 históricas **no certificadas**, sin reemplazar pivotes Elliott aprobados.
- Las compras O2/O4 se suman a Exchange, y la custodia Forecast hace transferencias **solo virtuales**; BTC NEVER SELL y HODL protegido.
- La revisión de Google Sheets se publica solo mediante Settings y autorización administrativa explícita. No hay fallback a snapshots JSON/imágenes.
- El post-cierre O5 es una **hipótesis de liquidación terminal** distinta de haber alcanzado todas las extensiones. No inferir que se vendieron tramos no alcanzados en la realidad.

## Pruebas

- `PYTHONPATH=. python -m pytest -q tests`: **97 PASS**, incluyendo provisión diferida de políticas y rechazo de repartos incorrectos.
- `node tests/test_forecast_segments.js`, `node tests/test_settings_format.js`, `node tests/test_forecast_fibo_v14.js`: PASS.
- `python tests/browser_forecast_v14.py`: PASS en Chromium sin web externa ni escritura, 12 tokens, cuatro tablas de custodia y 12 filas de composición; recalcula al cambiar porcentajes y niveles.
- `python -m compileall` y sintaxis JS: verificar durante empaquetado.

## Despliegue

1. Mantener una copia/rollback de la versión v1.3.0. Subir **contenido descomprimido** del ZIP a la raíz del repositorio, no el ZIP como archivo.
2. Conservar variables y secretos de Render de v1.3.0; no se requieren nuevas variables de entorno.
3. Desplegar y verificar `/health` → `version: 1.4.0`, `/api/sheets-status` → Master PUBLICADO, `/mode/forecast` → vista con asignaciones y cálculos dinámicos.
4. Validar visualmente compras O2/O4 al 25% de P, O3/O5 con todas las extensiones y exclusión BTC/HODL; validar modo Claro/Oscuro.
5. Para probar guardado de parámetros, modificar SOLO valores de simulación en Settings, describir evidencia y confirmar guardar; revisar que `12_PARAMETROS_KAIROS` y `18_SETTINGS_AUDITORIA` registren la versión; nunca probar cambiando unidades reales sin necesidad.

**NOTA**: ni Google Sheets ni Render se modificaron para construir este paquete. Equivalencia completa KairosGPT/KairosWeb Forecast avanzado no certificada todavía, por diferencias históricas de anclas y motor.
