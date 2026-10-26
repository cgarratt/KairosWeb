# KairosWeb v2.0.52 — Órdenes exclusivas del ciclo

- Órdenes muestra únicamente BUY O2C1–O2C4 / O4C1–O4C4 y SELL O3V1–O3V4 / O5V1–O5V4.
- Se excluyen visualmente MANUAL y REBALANCEO, sin borrarlos del MASTER ni cambiar sus compromisos contables.
- La API administrativa de gestión rechaza nuevas escrituras fuera de esos niveles.
- Conserva filtros, estados y controles de ejecución manual y conciliación.
- No envía operaciones a exchanges ni modifica saldos.
