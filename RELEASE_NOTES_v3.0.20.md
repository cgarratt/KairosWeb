# KairosWeb v3.0.20 — Compras Balancer con ventas

Corrige la condición de reserva Balancer 0 por umbral O2/O4: solo desactiva la reserva/capacidad inicial financiada con liquidez existente. No anula el reciclaje condicionado de ingresos por ventas simuladas.

Compras con ventas = reserva Balancer libre permitida + ingresos de ventas simuladas, una sola vez. El tope porcentual del portafolio limita la reserva inicial, no esos ingresos reciclados. La asignación sigue recalculando pesos después de las ventas, comprando únicamente INFRA y respetando déficit/caja. Si no hay INFRA o se cubre todo el déficit, el sobrante queda sin asignar.

Los USD3694 de la captura son referencia bruta, no ingreso neto certificado. Descontar comisiones y diferencias de ejecución al conciliar. Antes del fill, el monto solo existe en el escenario Con ventas; no cambia liquidez física, QF, inventario, snapshot ni compromisos. No se envían órdenes.

Conserva pivotes BTC semanales5L/5R de v3.0.19 y clasificación de órdenes v3.0.18. Compatible con KairosGPT v1.3.13 aplicando el módulo idéntico incluido en compat/kairos_gpt/liquidity_reserves.py; copiar sobre ese archivo del paquete GPT, sin sustituir el resto. La actualización del módulo requiere instalación, no ocurre por generar este ZIP.

Validación actual:9 pruebas de reserva/asignación condicionada y8 de pivotes5L/5R, ejecutadas sin Flask; compilaciónPython verificada. Suitecompleta y prueba visual no repetidas. Los resúmenes de versiones2.x se consolidan en HISTORIAL_RELEASES_v2.md para mantener menos de100archivos. Pendiente de desplegar en Render; ningún MASTER modificado.
