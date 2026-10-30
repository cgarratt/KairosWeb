# KairosWeb v3.0.16 — Fibo con asignación 0%

Las propuestas de compra de un escalón Fibo cuya asignación publicada es 0% se muestran NO APLICA, con USD 0 y unidades 0. Se aplica a O2/O4 con sus propios porcentajes. No se proponen como próxima acción ni alerta cercana. En Compras se muestra NO APLICA · 0% y no se pueden reactivar mediante un ajuste local de la simulación.

Las propuestas persistidas mantienen su evento histórico y se presentan con estado efectivo NO APLICA según la configuración vigente. No se modifican filas del MASTER por consultar una pantalla. Si vuelve a habilitarse el escalón, se evalúan como PROPUESTA con las guardas vigentes de Spot y ponderación.

Órdenes CONFIRMADAS, PARCIALES y EJECUTADAS conservan su registro real. CANCELADA se reserva para una cancelación real acreditada; esta versión no cancela órdenes en exchange. Compras manuales y Balancer permanecen independientes.

Validación local: 18 pruebas Python y 7 casos JavaScript. Sin despliegue, escritura en MASTER ni prueba visual en navegador. Conserva el flujo de estados de v3.0.15.
