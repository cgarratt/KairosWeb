# Kairos Web v4.0

- Balancer: compara USDT para compras con reserva actual y con ventas simuladas; no se consideran fills.
- Compras: techo del slider = USDT físico menos Reserva Trading; precios C1/C2 marcados Pendiente hasta integrar anclas aprobadas; distribución C1/C2 referencial 60/40.
- Ventas: slider 0–40% (por defecto 40%); tabla de inventario HODL/Core/Exchange, por Tier.
- Todas las propuestas son simulaciones. No se ejecutan órdenes ni se presume inventario libre de reservas sin conciliación.

Despliegue: reemplazar archivos raíz del repositorio, conservar variables Environment y desplegar en Render.


## v4.0.1 hotfix
La heurística de INVALID_URL ahora sólo aplica a errores realmente relacionados con el formato de la URL. El diagnóstico informa exception_type sin incluir secretos. Nueva ruta autenticada `/api/mcp-config-check` para comprobar esquema, host, path y comillas sin revelar direcciones. No modifica reglas de inversión ni datos.
