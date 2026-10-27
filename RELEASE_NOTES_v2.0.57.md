# KairosWeb v2.0.57 · Topes de reservas

Basado en v2.0.56. Conserva las órdenes y sus estados de la versión anterior.

- Configuración → Parámetros permite editar BALANCER_MAX_PORTFOLIO_FRACTION y TRADING_MAX_PORTFOLIO_FRACTION como porcentajes 0–100. Se publican en MASTER con el flujo administrativo y auditoría existentes.
- Balancer efectivo=min(liquidez física × porcentaje Balancer, portafolio Spot × tope Balancer, caja no QF). Descontar compromisos reales una sola vez. Redondear máximos hacia abajo a centavos.
- Trading objetivo=min(liquidez física × porcentaje Trading, portafolio Spot × tope Trading). Mostrar saldo QF real, objetivo, techo y exceso por separado. QF real nunca se reduce automáticamente ni se convierte su exceso en caja libre.
- P=cripto valorizado con Spot vigente + liquidez física, contando QF una sola vez. Falta de valoración, topes incompletos o sin aprobación bloquea el presupuesto nuevo. El campo C172 es una base previa al tope Spot.
- La capacidad condicional Balancer con ventas propias también queda limitada por el techo sobre P; ninguna venta simulada acredita caja real.
- Balancer, Compras/Forecast y Órdenes (que consume Balancer) usan la misma entrada budgets_from_master. Nuevos topes se leen en cada valoración. Después de instalar este release, cambiar sus porcentajes en Configuración no requiere nuevo deploy.
- Settings muestra la base de liquidez y los topes publicados, sin presentar una valoración Spot almacenada como vigente. Balancer muestra los importes efectivos con Spot MCP actual.

Validación: 39 pruebas dirigidas aprobadas y comprobación del reporte Balancer y render Jinja con MASTER fresco. Suite general: 249 aprobadas, 7 fallos ya presentes en v2.0.56 (la base reproduce exactamente esos 7: dos contratos de autenticación de Alertas, tres aserciones de versión antigua y dos controles de órdenes retirados). Sin regresiones nuevas detectadas. Sintaxis JavaScript validada.

Instalación: sustituir el contenido del repositorio por estos archivos conservando secretos de Render fuera de Git. Comprobar /health: versión 2.0.57 e integridad de assets. Esta entrega no realiza un deploy remoto.
