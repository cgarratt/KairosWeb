# KairosWeb v2.0.56 — Semáforo de Órdenes

- Estado visual rojo NO APLICA, ámbar PROPUESTA, azul PARCIAL y verde EJECUTADO.
- PARCIAL solo se calcula cuando un fill ya conciliado en 05_ORDENES/06_FILLS tiene atribución expresa `ASOCIACION_AUTORIZADA:<NIVEL>` en su registro de 26_ORDENES_GESTION. Nunca se asignan compras MANUAL a O2C2 automáticamente.
- El presupuesto del nivel es distinto del déficit global de ponderación del token.
- No se generan fills, transferencias ni escrituras al MASTER. Los niveles sin presupuesto no se convierten en compras.
- La ausencia de PLUME O2C2 por falta de asignación en el motor permanece bajo diagnóstico: no se inventa una propuesta ni se imputa su compra manual.


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


# KairosWeb v2.0.58 · Liquidez simplificada y configuración integrada

Cambios aprobados:
- Gestión de liquidez: total USDT, barra seccionada y tres categorías excluyentes: Compras O2/O4, Reserva Balancer y Reserva Trading real. Importes con dos decimales y porcentajes sobre liquidez física. Se retiran de esta sección patrimonio, metas, topes y déficits. Los límites financieros del motor se conservan.
- Objetivos de gestión: campos editables para Tope Balancer y Tope Trading, leídos de los parámetros aprobados de MASTER (inicialmente6%/3%). Se publican atómicamente junto con los demás objetivos, con autorización administrativa, vista previa y auditoría existentes. También se conservan en Parámetros.
- Integridad: topes independientes0..100%, ambos presentes, sumas de Cripto/Liquidez, Tiers, reparto base de liquidez y custodias igual100%. Las categorías reales deben sumar liquidez física y no tener saldos negativos. QFreal no se reduce automáticamente por cambiar un tope.
- Navegación: Portafolio → Balancer → Compras → Ventas → Órdenes → Forecast.

Comprobaciones:49 pruebas dirigidas y8subpruebas aprobadas, render Jinja del reporte Balancer y sintaxis JavaScript válidos. Se conservan siete fallos generales heredados del release anterior: dos contratos de autenticación de Alertas, tres verificaciones de versión antigua y dos botones de órdenes retirados. No se certificó inspección visual mediante navegador en este entorno.

Paquete para GitHub: excluye únicamente pruebas y cachés; conserva todos los archivos de ejecución. Descomprimir y cargar TODO el contenido en la raíz del repositorio, incluidas static y templates. Se requiere desplegar este release en Render; después, los parámetros pueden cambiarse sin nuevo deploy. Comprobar /health versión2.0.58 e integridad de assets. No incluye credenciales ni datos del portafolio.

KairosGPT permanece en1.3.11; este release solo cambia KairosWeb y la validación de publicación desde su menú Configuración. No envía órdenes, transfiere custodia ni modifica saldos por sí mismo.


# KairosWeb v2.0.59 · Donut de liquidez y editor único de reservas

- Gestión de liquidez: donut con liquidez total en el centro. Categorías excluyentes Compras O2/O4, Reserva Balancer y Reserva Trading real, con importe USDT y porcentaje. Sin topes, metas o déficits en esta sección. QFreal se conserva íntegro; sin duplicar Balancer ni QF.
- Configuración → Objetivos de gestión → Reservas y topes del portafolio es el único lugar donde se editan los topes de ambas reservas. Publicación conjunta con las demás metas y auditoría existente.
- Configuración → Parámetros conserva ambos topes como consulta de los valores publicados en MASTER. No aparecen inputs editables. El servidor rechaza intentos de actualizar esos topes a través de la sección Parámetros.
- Las descripciones de consulta muestran el porcentaje actual de MASTER, sin texto fijo6%/3%. No se modifican valores publicados a partir de capturas de borradores.
- Se conservan topes independientes0..100%, presencia de ambos, sumas al100% de los repartos, partición física de caja y protección de QF. Se conserva el cálculo financiero de v2.0.58.
- Conserva navegación Portafolio → Balancer → Compras → Ventas → Órdenes → Forecast y el historial de órdenes.

Comprobaciones:52 pruebas dirigidas y8subpruebas aprobadas, incluyendo render del donut, caso caja cero, integridad y bloqueo de la vía duplicada de edición. Sintaxis JavaScript válida. Suite general conserva siete fallos heredados sin relación con estos cambios; no se certificó inspección visual con navegador en este entorno.

Instalación:descomprimir y subir todo el contenido a la raíz del repositorio, incluidas static y templates. Este paquete de carga excluye únicamente pruebas y cachés y tiene menos de100archivos. Desplegar en Render y verificar /health versión2.0.59 y assets consistentes. Esta entrega no realiza despliegues remotos ni cambios de saldos, custodia u órdenes.

KairosGPT permanece en v1.3.11; no necesita actualizarse por estos cambios de interfaz. Los valores financieros se leen del MASTER PUBLICADO y las cotizaciones vigentes al ejecutar el motor.


# KairosWeb v2.0.60 · Custodia con umbral de materialidad

Basado en v2.0.59. Mantiene donut de liquidez, edición única de topes desde Objetivos de gestión, consulta dinámica en Parámetros y navegación Órdenes antes de Forecast.

- Balancer: cada transferencia Exchange→HODL o Exchange→Core solo se propone si las unidades a mover son estrictamente mayores al5% del TOTAL de unidades del token (HODL+Core+Exchange). Se aplica por movimiento, no sobre el saldo Exchange ni sobre valor USDT.
- Movimientos menores o exactamente iguales al5% se consideran aceptables y se omiten. Sus unidades no se transfieren virtualmente: la distribución posterior únicamente incluye los movimientos visibles.
- La vista identifica variaciones menores aceptadas y distingue brechas residuales superiores al umbral. Conserva custodia protegida, BTC NEVER SELL, reservas SELL y conservación de unidades.
- Ninguna propuesta altera saldos, órdenes ni custodia real. El MASTER no se modifica por generar el reporte.

Validación:71 pruebas dirigidas aprobadas, integración del reporte Balancer y render Jinja verificados, sintaxis JavaScript válida. Se mantienen los siete fallos generales documentados del release anterior (contratos antiguos de autenticación de Alertas, aserciones de versión y botones retirados de Órdenes); no se certifica inspección visual mediante navegador en este entorno.

Instalación:descomprimir y subir todo el contenido a la raíz del repositorio, incluidas static y templates. Paquete de carga con menos de100archivos; excluye pruebas y cachés. Desplegar en Render y comprobar /health versión2.0.60 y release_assets.consistent=true. Este paquete no ejecuta el despliegue remoto. KairosGPT se mantiene en1.3.11.
