# KairosWeb v2.0.39 · Objetivos de gestión en una sola pantalla

## Cambios

- Configuración → **Objetivos de gestión** consolida la estructura jerárquica del portafolio en una sola vista: (1) Cripto / Liquidez; (2) T1/T2/T3 dentro de Cripto; (3) USDT / Reserva Balancer / ReservaTrading dentro de Liquidez; (4) HODL/Core/Exchange en cada Tier.
- Cada uno de los seis grupos exige suma del **100%** en interfaz y servidor. La publicación requiere doble confirmación administrativa, ID del snapshot publicado, evidencia, validación completa, auditoría y homologación contable atómica de Google Sheets.
- Los pesos por Tier recalculan los objetivos por token conservando las proporciones internas de cada Tier; 12 targets cripto siguen sumando 100%. No se modifica clasificación Tier ni cantidades físicas de custodia.
- Custodia por Tier se guarda en `04_CUSTODIA`; los 12 objetivos de tokens se guardan en `02_POSICIONES`. Los cuatro objetivos derivados del capital se mantienen en `08_INTEGRAL` sin alterar sus montos históricos registrados. Los subporcentajes de liquidez, todavía no existentes en versiones anteriores del MASTER, se publican en `12_PARAMETROS_KAIROS` como tres parámetros nuevos `PORTFOLIO_LIQ_*_FRACTION` (sumados al 100%). No se necesita modificar el esquema 5.0.0.
- El primer formulario usa del MASTER el objetivo del reparto histórico (Cripto vs. Liquidez), los pesos T1/T2/T3 y custodias; mientras no exista objetivo formal de subliquidez, se muestran **70/20/10 únicamente como borrador** a partir de la tabla de referencia del usuario. No es una política aprobada hasta publicarse.
- Los porcentajes de ReservaTrading y Reserva Balancer son **metas de planificación**: no sustituyen saldos físicos (`03_LIQUIDEZ`), no transfieren USDT, no sobrescriben la fórmula operativa `BALANCER_RESERVE_FORMULA` ni `STRUCTURAL_USDT_TARGET` y no activan órdenes. La reserva física QF sigue protegida una sola vez.
- Las secciones históricas de edición desagregada se conservan como contrato backend para compatibilidad con herramientas previas, pero ya no se repiten en la navegación de Configuración.

## Validaciones locales

- Pytest: 231 aprobadas, 2 omitidas; subcasos parametrizados 4 correctos.
- Node: 9 suites JavaScript correctas.
- Jinja: 14 plantillas analizadas.
- `/health`: marcadores del nuevo editor unificado y su motor de publicación.
- ZIP con un máximo de 100 archivos, hashes SHA256 verificados tras extracción.

## Pendiente

No se hizo escritura en MASTER ni despliegue GitHub/Render. Después de instalar verificar `/health` v2.0.39, Configuración → Objetivos de gestión, la vista previa, y la publicación administrativa contra un entorno de prueba con credenciales de edición antes de operar sobre el MASTER real. `KAIROS_SESSION_SECRET` debe mantenerse estable.
