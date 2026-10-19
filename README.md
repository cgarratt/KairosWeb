# KairosWeb v2.0.12 — Release acumulativo para GitHub

Actualización completa sobre v2.0.10: **Configuración con acceso administrativo único** y **tooltips desactivados en móviles**. Se conserva la funcionalidad de Balancer, Compras, Ventas, Forecast, Órdenes (FASE 1, propuestas sin ejecución), Alertas, Portafolio Integral y editor de Pivotes.

## Cambios de v2.0.12
- Al entrar en `/settings` sin sesión administrativa, redirección a `/admin/login`. Un solo login autoriza todas las secciones de Configuración durante la cookie firmada vigente (hasta 30 minutos). Al cerrar/expirar sesión se requiere nueva autenticación. El enlace repetido de inicio de sesión se elimina de las subpáginas.
- `/api/settings/data` requiere sesión administrativa. La publicación continúa protegida por controles de autorización y CSRF; **el acceso Basic no concede permiso administrativo**.
- En móviles (ancho <= 680px o puntero grueso sin hover), botones y menús no muestran tooltips por toque ni `title` nativo. Escritorio conserva tooltips, y `aria-label` se mantiene para accesibilidad.
- `/health` incluye comprobaciones adicionales de acceso administrativo y comportamiento responsive para detectar despliegues parciales. No se cambia el contrato Google Sheets `schema_version=5.0.0`.

## Despliegue en GitHub / Render
1. Usar todos los archivos del ZIP, conservando directorios `templates/`, `static/`, `tests/` y la raíz (incluido `render.yaml`). Los archivos históricos ya excluidos pueden permanecer solo en el historial Git, no en el runtime.
2. **No publicar secretos** (JSON de cuentas Google, API keys, `.env`, tokens); las variables de entorno existentes de Render permanecen allí.
3. Tras desplegar comprobar `/health`: `version=2.0.11`, `status=UP`, `release_assets.consistent=true`.
4. En una sesión nueva verificar `/settings` -> `/admin/login`, login una vez, navegación entre pestañas, cerrar sesión y expiración. Comprobar tooltips en móvil y escritorio.
5. Los motores no ejecutan órdenes ni escriben datos por la mera visita o despliegue. Publicaciones administrativas de cambios de pivotes/posiciones requieren aprobación explícita.

## Pruebas
Ejecutar `python -m pytest -q` y las pruebas Node en `tests/*.js`. La comprobación HTTP real de autenticación/cookie en Render debe validarse después de desplegar. Ver `RELEASE_NOTES_v2.0.12.md`.

**Formato compacto:** 99 archivos como máximo (incluye manifiesto), carga a la raíz del repositorio.


## Release 2.0.12 · Compras con pivotes PROPUESTO

- Para simulación, P1 es el último mínimo semanal documentado (PROPUESTO/VALIDADO/CONFIRMADO), cotejado con una semana UTC completa. P2 es el mayor máximo semanal posterior a P1, mayor que P1. La pareja no requiere que P2 sea un pivote 5L/5R certificado.
- Con P1 o P2 N/D, fuera de historia cerrada o sin fecha, Compras bloquea el token (USDT $0). Los candidatos PROPUESTO no constituyen órdenes ejecutables.
- La tabla Compras exhibe P1 y P2 con precio y fecha y círculo rojo (PROPUESTO), ámbar (VALIDADO), verde (CONFIRMADO), distinto del fondo histórico Fibonacci.
- Conserva compra solo INFRA, límites de déficit, recálculo por escalón, caja no asignada en USDT y reserva QF. Ventas ordinarias sigue sin filtro de pivotes; BTC NEVER SELL.
- `/health` valida la presencia real de plantilla y motor P1/P2. No corregir autenticación ni omitirla para permitir órdenes.
- Código completo para la raíz de GitHub. Aplicar sin credenciales, sin escrituras automáticas a Google Sheets; validar Render tras push.
