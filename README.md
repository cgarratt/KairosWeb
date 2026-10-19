# KairosWeb v2.0.13 — release completo para GitHub

Este paquete reemplaza v2.0.12 y conserva las funciones existentes: Configuración y autenticación administrativa, Compras, Ventas, Balancer, Forecast, Alertas, Portafolio Integral y Órdenes fase 1 (solo propuestas).

## Novedad v2.0.13 · Forecast / Trayectoria Ciclo por Token

- **CL, O1, O2, O3, O4 y O5** con estado `VALIDADO` o `CONFIRMADO` en el Master `07_PIVOTES` se muestran con **precio fijo** en la trayectoria, la tabla de ondas y el modelo de valorización.
- La gráfica identifica un punto fijo por estado: VALIDADO en ámbar, CONFIRMADO en verde, junto con el estado y candado. Solo las etapas `PROPUESTO` pueden recalcularse con selectores de escenario.
- Se da prioridad a **precios publicados del Master** frente a candidatos MCP y derivaciones Fibonacci locales. Forecast no escribe pivotes ni certifica nuevas ondas.
- Un pivote protegido sin precio o una estructura incompatible produce un estado de advertencia, no una corrección silenciosa.
- El diagnóstico `/health` verifica presencia de los componentes que inmovilizan los pivotes en Forecast, además de los controles anteriores.

## Funciones conservadas de releases previos

- Compras permite P1 `PROPUESTO`/`VALIDADO`/`CONFIRMADO` para **simulación**, siempre que coincida con mínimo 1W UTC cerrado y fechado. P2 es el máximo semanal cerrado posterior a P1. Semáforos P1/P2: rojo/ámbar/verde.
- Compras respeta INFRA, déficit frente al target, distribución secuencial y reserva QF. Ventas ordinarias **no exige** pivotes. BTC NEVER SELL.
- Configuración exige autenticación administrativa una vez por sesión; mantiene autorización de publicación. Tooltips desactivados en móviles, presentes en escritorio.
- Órdenes continúa **fase 1 / solo propuestas**: no hay endpoint de colocación/cancelación ni inferencia de fills.

## Despliegue

1. Descomprimir este ZIP y sustituir el contenido del repositorio GitHub, preservando las rutas y los directorios `static/`, `templates/` y `tests/`.
2. No subir credenciales, archivos `.env` ni claves; conservar variables de entorno de Render.
3. Tras desplegar, verificar `/health`: `status=UP`, `version=2.0.13`, `release_assets.consistent=true` y presencia de los tres nuevos indicadores `forecast_*`.
4. Probar **Forecast / Trayectoria Ciclo por Token** con al menos una onda publicada como VALIDADO y otra CONFIRMADO: modificar selectores O2–O5; esas ondas deben conservar exactamente su precio, mientras PROPUESTO puede variar. Comprobar tabla, gráfica y valoraciones.
5. Las pruebas locales están detalladas en `RELEASE_NOTES_v2.0.13.md`; **la integración HTTP real en Render aún requiere comprobación**.

Fuente de datos operativa: Google Sheets ORIGINAL `KAIROS_V5_MASTER`, snapshot `01_CONTROL` PUBLICADO y `schema_version=5.0.0`, más MCP autorizado. El ZIP no contiene inventarios ni precios operativos y no escribe cambios en Google Sheets.

**Límite de GitHub:** paquete compacto de menos de 100 archivos incluyendo manifiesto y SHA-256.
