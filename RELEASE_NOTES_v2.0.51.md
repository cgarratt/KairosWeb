# KairosWeb v2.0.51 — Hotfix CANCELLED en MASTER

- El lector reconoce órdenes BUY CANCELLED sin ID remoto cuando consta `CANCELACION_DECLARADA_USUARIO_2026-10-26` y `NO_VERIFICADA_API`, evidencia original, precio e importe válidos y cero unidades ejecutadas.
- Las órdenes CANCELLED no consumen reserva BUY ni alteran saldos. Se conservan como historial y no se infiere cancelación verificada por API.
- Las órdenes FILLED siguen requiriendo enlace válido con 06_FILLS; las PENDIENTE siguen reservando presupuesto y requieren evidencia.
- Corrige `ORDERS_FILLS_RECONCILIATION_REQUIRED` tras la publicación de las 14 cancelaciones declaradas.
- Sin escritura en MASTER, sin órdenes remotas y sin cambios de precios.
