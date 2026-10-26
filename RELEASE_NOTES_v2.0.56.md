# KairosWeb v2.0.56 — Semáforo de Órdenes

- Estado visual rojo NO APLICA, ámbar PROPUESTA, azul PARCIAL y verde EJECUTADO.
- PARCIAL solo se calcula cuando un fill ya conciliado en 05_ORDENES/06_FILLS tiene atribución expresa `ASOCIACION_AUTORIZADA:<NIVEL>` en su registro de 26_ORDENES_GESTION. Nunca se asignan compras MANUAL a O2C2 automáticamente.
- El presupuesto del nivel es distinto del déficit global de ponderación del token.
- No se generan fills, transferencias ni escrituras al MASTER. Los niveles sin presupuesto no se convierten en compras.
- La ausencia de PLUME O2C2 por falta de asignación en el motor permanece bajo diagnóstico: no se inventa una propuesta ni se imputa su compra manual.
