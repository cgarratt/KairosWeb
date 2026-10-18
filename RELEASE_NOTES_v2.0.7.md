# KairosWeb v2.0.7 · Release acumulativo desde v2.0.6

- Modo Compras filtra la pareja de **dos últimos pivotes semanales completos y técnicamente válidos** (low→high, 5L/5R + cierre BOS alcista). No admite máximos diarios, semanas en curso o inversion Fib histórica.
- Si corresponde al CL→O1: O2; si O2→O3: O4; de lo contrario RETROCESO_ALCISTA con pesos O2 del Sheet publicado (actualmente 20/30/40/10).
- Simula compras secuenciales por escalón y conserva la porción USDT de tokens bloqueados sin redistribuir. Token bloqueado = $0 en los cuatro tramos. Etiqueta por token y motivo en tabla, junto a los semáforos y spot.
- Ventas ordinarias, Forecast hipotético y Balancer **sin el filtro**.
- Se conserva 2.0.6: donut histórico, lector pivotes CL/O1–O5, validación CL, campana 1H/4H/1D, seguridad de Settings, Render sin alteraciones.
- No se publica nada en Sheets ni se ejecutan órdenes. Versionado 2.0.7; `/health` revisa archivos críticos de la implementación.
- Pruebas locales completas y manuales en Render recomendadas antes de declararlo certificado en producción.

## HOTFIX 1 — chequeo /health (18/10/2026)

Corrige el control de integridad del editor de CL. El atributo HTML `data-cl-review-token` es creado en tiempo de ejecución mediante `verify.dataset.clReviewToken` en `static/settings_master.js`, por lo que no está presente como texto literal en ese archivo. `/health` ahora verifica el identificador de código real, sin dejar de exigir que todos los demás archivos y marcadores estén presentes. Ningún cambio en cálculos, órdenes, reservas ni Google Sheets.
