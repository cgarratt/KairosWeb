# KairosWeb v4.6.2 — Compras por ciclo

P1/P2 se seleccionan por parejas canónicas del mismo ciclo, nunca por el mínimo más reciente:
- O2: CL/O1. Un O2 propuesto no desplaza CL.
- O4: O2/O3 publicados, fechados y coherentes. O3 propuesto permite solo escenario O4 propuesto.
- O2 confirmado sin O3: fase O3 en desarrollo, sin nueva asignación.
- O4 confirmado: fase O5 en desarrollo, sin nueva asignación.
- O5 confirmado: ciclo completo; requiere nuevo ciclo con CL/O1 revisados.
- Cronología o estructura inválida bloquea el token. No se reemplazan anclas publicadas con máximos MCP.

La tabla muestra fase, pareja y rol de P1/P2. El selector recalcula la fase al cargar el MASTER; no vigila continuamente ni publica pivotes. PROPUESTO no certifica Elliott ni habilita órdenes reales. Elegibilidad estructural no equivale a asignación: siguen aplicando INFRA, estados, caja y límites.

Validación: 15 pruebas unitarias, comprobación de selección en 12 tokens con pivotes publicados leídos en esta sesión; sin valoración Spot. Forecast CL/O1 sin cambios. Se conserva la simulación integral y sus selectores Fibo de v4.6.1. No modifica el MASTER ni cambia estados de órdenes.

Instalación: descomprimir y reemplazar archivos en la raíz del repositorio Web v4.6.1; desplegar en Render. Sin cambios MCP ni variables de entorno. El paquete incluye la copia compat del selector; no instala instrucciones del Proyecto GPT.

Despliegue remoto y comprobación visual en producción pendientes.
