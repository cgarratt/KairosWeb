# Kairos Web v3.7 — Balancer visual

- El modo Resumen se retira del menú; `/mode/resumen` redirige al dashboard.
- Balancer inicia con gestión de liquidez: USDT, 40% P, reserva teórica Balancer 5% P, bolsas C1/C2 separadas.
- BSI retirado de la vista Balancer.
- Tablas BUY y SELL con indicadores y cantidades referenciales, no ejecutables.
- Dos gráficos independientes de peso actual vs posterior hipotético.
- Limitación: faltan órdenes pendientes, fees, inventario libre conciliado y presupuestos ya gastados, por lo que no hay capacidad ejecutable certificada.

## Despliegue
Reemplazar archivos en la raíz del repositorio GitHub KairosWeb y desplegar Render, conservando todas las variables de entorno existentes.
