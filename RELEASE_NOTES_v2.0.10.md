# KairosWeb v2.0.10 — Protección de pivotes frente a MCP

**Base:** v2.0.9 + desarrollo acumulativo aprobado el 18/10/2026.
**Ámbito:** KairosWeb; KairosGPT se mantiene independiente.

## Corrección principal

- `Configuración → Pivotes → Actualizar candidatos desde MCP` solo puede renovar el precio, fecha y estado de anclas **PROPUESTO**.
- **VALIDADO** y **CONFIRMADO** conservan precio, fecha y estado frente a nuevos resultados MCP, revisiones negativas o errores de conexión.
- La protección también se aplica a **VALIDADO en borrador**: pulsar de nuevo «Actualizar» no revierte ni sustituye ese valor.
- Una rectificación de VALIDADO es una edición explícita en Configuración y necesita nueva evidencia y publicación administrativa. CONFIRMADO no puede alterarse por guardado ordinario; revisión administrativa formal pendiente.
- La comprobación MCP puede promover PROPUESTO a VALIDADO **en borrador**; nunca publica ni confirma automáticamente.

## Cambios acumulados preservados

- Órdenes Fase 1: propuestas de balance/estructura separadas; filtros por venue/token y objetivos semanales, sin colocar ni cancelar órdenes reales.
- Compras: simulación provisional con pares semanales trazables PROPUESTO/VALIDADO/CONFIRMADO; N/D sin compras; máximo físico menos ReservaTrading QF.
- Ventas ordinarias sin filtro de pivotes, BTC NEVER SELL y custodia protegida.
- Alertas 1H/4H/1D, donut de capital, y semáforos Fibonacci históricos.
- **VIRTUAL:** se excluye para el cálculo exploratorio de CL el mínimo bruto de la semana flash crash del **06–12/10/2025**. La exclusión no certifica ni crea un CL alternativo. El valor observado **$0.6291 el 19/12/2025** sigue pendiente de homologación humana. Sin anclas publicadas válidas: N/D.
- Se amplía `/health` para detectar archivos de la protección MCP y exclusión VIRTUAL, sin depender de coincidencias frágiles del HTML renderizado.

## Seguridad y operación

Solo lectura MCP / simulación: este paquete no cambia Google Sheets `KAIROS_V5_MASTER`, el snapshot, órdenes ni custodias. Ningún candidato constituye orden ejecutable.
No contiene credenciales privadas. No hace deploy directo a Render ni modifica GitHub.

## Despliegue y verificación

Extraer todos los archivos del ZIP a la **raíz** de GitHub conservando `templates/`, `static/` y `tests/`.
En Render verificar `/health`: `version=2.0.10`, `status=UP`, `release_assets.consistent=true`.
Luego abrir Configuración → Pivotes: revisar BTC VALIDADO, ETH CONFIRMADO y un tercer token PROPUESTO; consultar MCP y constatar que los primeros dos no cambian. No publicar pivotes durante una prueba de interfaz sin autorización.
Revisar Compras y Órdenes en modo simulación. Prueba funcional final en Render pendiente.
