# KairosWeb v3.0.29 — Precio y estado propios de cada token en Órdenes

## Causa y corrección
La generación de compras usaba una variable de un bucle anterior: comparaba los objetivos de todos los tokens con el Spot del último token y consultaba también su estado. Cuando PEPE quedaba al final, casi todos los objetivos eran descartados por compararse con su precio de escala muy inferior. La corrección de nomenclatura de v3.0.28 no resolvía este defecto.

Cada fila usa ahora su propio token, precio Spot, modo O2/O4 y estado del escalón. En una reproducción local con las entradas históricas de diagnóstico, antes solo se generaba PEPE O2C4 por $305.64; tras el arreglo aparecen 15 propuestas BUY financiadas. Estos valores son evidencia de regresión, no una ejecución financiera actual ni una promesa de número de órdenes en producción.

Se conservan nomenclatura O2C2/O2C3, filtro de importe $0, recibos reales, combos, guardado global y reglas de estados/custodia/liquidez vigentes. No modifica MASTER ni envía órdenes.

## Pruebas y despliegue
155 pruebas Python y 10 comprobaciones JavaScript aprobadas. Las nuevas regresiones usan activos con precios de distinta escala, cambian el orden de los tokens, separan estados por token/escalón y comparan importes del motor Python con JavaScript bajo las mismas entradas y presupuesto. Incluye las pruebas anteriores del recorrido de la ruta y renderizado de la tabla. Integridad de assets y ZIP verificada. Sin prueba visual de navegador ni acceso al despliegue real.

Descomprimir y reemplazar el contenido del repositorio, conservando static/ y templates/. Desplegar en Render y comprobar /health con versión 3.0.29. KairosGPT v1.3.15 sigue siendo compatible. Pendiente de despliegue.

## Historial anterior

# KairosWeb v3.0.28 — Órdenes O2 y filtro de importe cero

- Los retrocesos alcistas genéricos usan los identificadores O2C1–O2C4, igual que su distribución O2 publicada. Se corrige la pérdida de propuestas C2/C3 al aplicar el filtro del ciclo. O4 conserva O4C1–O4C4.
- Después de clasificar precios/estados, el listado omite las filas con importe $0.00, incluidas las de asignación Fibo cero. No modifica ni borra registros del MASTER. Las referencias SELL sin tamaño siguen mostrando N/D.
- Las órdenes reales con importe ejecutado registrado muestran importe/unidades de ejecución; si aún no hay ejecución usan lo previsto. Así se evitan filas con $0 cuando existe una transacción real acreditada. Si ambos importes son cero, no se muestran.
- Se conservan combos por fila, botón único Guardar cambios, transiciones por canal, PRI y todas las mejoras anteriores. No cambia el cálculo de compras, reservas, custodia ni conciliación.

## Instalación y validación
Descomprimir y reemplazar el contenido del repositorio existente, conservando static/ y templates/. Desplegar en Render y verificar /health con versión 3.0.28. KairosGPT v1.3.15 sigue siendo compatible y no requiere reemplazo.

146 pruebas Python y 10 comprobaciones JavaScript aprobadas. Incluyen regresión del recorrido generación → filtro de ciclo → clasificación → listado, renderizado O2C2/O2C3, exclusión de cero e integridad del historial. Sin prueba visual de navegador ni escrituras reales en MASTER. Pendiente de subir a GitHub y desplegar en Render.

## Historial anterior

# KairosWeb v3.0.27 — Combos y guardado global de estados

Acción usa un combo por orden editable: No aplica solo permite Propuesta; Confirmada solo permite Ejecutada. Propuesta se confirma con imagen en KairosGPT; Ejecutada y Parcial histórico no tienen controles de edición Web.

Un único botón Guardar cambios debajo de la tabla persiste todas las selecciones pendientes, incluso si un filtro oculta una fila. Seleccionar un estado no escribe en MASTER. Al elegir Ejecutada se abre una revisión de ID, importes, unidades, fees y evidencia; Validar datos solo prepara la selección y no guarda. Cancelar o cerrar esa revisión descarta la selección incompleta.

El guardado es secuencial por orden, no una transacción única del lote. Los éxitos se retiran de la cola antes de avanzar. Si una escritura falla o no puede verificarse, se detiene, informa cuántas órdenes se guardaron y exige recargar/revisar historial antes de reintentar. No hay reintento automático ni duplicación intencional de eventos reconocidos. Conservar autenticación administrativa, CSRF, control de snapshot/revisión y validación del servidor.

No cambia reglas financieras, la conciliación independiente ni el contrato de estados v3.0.26. KairosGPT v1.3.15 sigue siendo compatible; no requiere reemplazarlo otra vez por este cambio de interfaz.

Pruebas: 140 Python aprobadas y 10 comprobaciones/escenarios JS. Plantilla renderizada en pruebas; sin prueba visual de navegador ni escrituras MASTER reales. Pendiente despliegue en GitHub/Render. Paquete Web de 99 archivos.

## Historial anterior

# KairosWeb v3.0.26 — Estados por canal y PRI ampliado

## Reglas vigentes
1. No aplica → Propuesta.
2. Propuesta → Confirmada exclusivamente en KairosGPT con imagen de transacción verificada, ID y datos reales.
3. Confirmada → Ejecutada exclusivamente en KairosWeb, validando o editando los datos (ID, unidades, importes, fees y evidencia).
4. Ejecutada es terminal en Web.
5. Un prompt explícito del usuario en KairosGPT permite corregir cualquier estado de una orden existente, conservando evidencia y contabilidad y auditando la instrucción. Web no admite esa excepción aunque el cliente intente enviar flags internos.

Parcial histórico se conserva, pero no es opción seleccionable en Web. Clasificación automática No aplica por meta Fibo cero o precio inadmisible sigue siendo una vista efectiva y no borra el historial. Reabrir no obliga a asignar liquidez si el nivel sigue siendo inelegible.

El estado no equivale a conciliación: se guardan eventos append-only y evidencia. Un cambio de estado no revierte, duplica ni acredita fills, inventario o caja. Se mantienen las validaciones de snapshot/revisión, duplicados, caja, Exchange/Tier y BTC NEVER SELL. Prompt que cambia estado de una ejecución conciliada conserva sus recibos e inventario; no libera caja ficticia.

## PRI ampliado
Identifica exposición y monto cripto, token de mayor peso y token más sobreponderado, su porcentaje frente a la meta, exceso referencial en USD y desviación en pp. El exceso se calcula con la cartera cripto sin liquidez; no constituye importe ejecutable de venta. Sin cambios a fórmula o umbrales PRI.

## Instalación y pruebas
Reemplazar el código en GitHub y desplegar en Render. Cambios de estado requieren sesión administrativa y credencial writer configuradas. No se escribió MASTER durante preparación. 140 pruebas Python aprobadas y 7 comprobaciones JS; sintaxis comprobada. Renderizado de plantilla verificado en tests; sin prueba visual de navegador ni escritura real.

## Historial anterior (reglas sustituidas por las vigentes arriba)

# KairosWeb v3.0.25 — Base del umbral Balancer corregida

## Regla autorizada
Umbral = (liquidez física total − Quantfury) / valor actual del portafolio Spot.
Se evalúa ANTES de descontar reservas y compromisos. Estrictamente por debajo del umbral configurable: liberar únicamente la reserva Balancer no comprometida hacia O2/O4. En igualdad o por encima: asignación Balancer normal, respetando porcentaje, tope y caja libre. Umbral 0 desactiva el bloqueo.

Las órdenes confirmadas siguen descontándose de los presupuestos gastables; no se cancelan ni se liberan compromisos. QF permanece protegido. No se cambian saldos reales, unidades ni parámetros en MASTER. El fondo condicional tras ventas sigue incluyendo los ingresos hipotéticos una sola vez. Los importes de categorías conservan el total físico.

Configuración muestra la fórmula corregida. Se mantiene el identificador BALANCER_MIN_O2_O4_PORTFOLIO_FRACTION para conservar el valor configurable existente; no requiere migración de parámetro. El metadato nuevo non_qf_liquidity_usdt identifica la base; baseline_o2_o4_usdt se conserva como alias de compatibilidad.

## Homologación GPT
El módulo compat/kairos_gpt/liquidity_reserves.py es idéntico al Web. Reemplazar liquidity_reserves.py en KairosGPT 1.3.13 con este archivo para aplicar la misma corrección. El parche no se instala automáticamente.

## Entrega
Descomprimir y reemplazar los archivos en GitHub, luego desplegar en Render. Release pendiente de despliegue externo. Preserva todos los cambios v3.0.24, incluyendo prioridad MASTER, PRI y estados de órdenes.

## Verificación
90 pruebas Python aprobadas (suite completa), compilación Python y sintaxis de settings_master.js. Casos del umbral: por debajo, igualdad, por encima, QF excluido, compromisos conservados, ejemplo de captura con valor de portafolio sintético, reciclaje de ventas y paridad del módulo GPT. No se hizo escritura sobre MASTER real ni validación visual de navegador.

## Historial anterior

# KairosWeb v3.0.24 — Mejoras acumuladas

## Cambios
- PRI: explicación simple y dinámica debajo del indicador, identificando los dos componentes con mayor aporte al resultado real del modelo (exposición, concentración o drift). No modifica el cálculo ni los umbrales.
- Compras: título exacto «Disponible compras».
- Órdenes: un solo indicador junto al texto del estado; conciliación separada, sin segundo semáforo ni códigos internos en Acción.
- Botón Cambiar estado para propuestas y órdenes editables; modal con combo y Guardar estado.
- Propuesta admite No aplica, Confirmada, Parcial y Ejecutada. No aplica puede reactivarse explícitamente. Confirmada y Parcial permiten completar ejecución; Ejecutada permanece terminal.
- Las recomendaciones aún no registradas generan Propuesta y el estado elegido en una sola escritura. Control de snapshot/revisión, sesión administrativa, CSRF, deduplicación y topes de caja/Exchange/Tier conservados.
- Confirmación requiere ID, tamaño e importe real y evidencia; ejecución exige fills incrementales y comisiones. Campos de ejecución vacíos por defecto: no se infieren fills del presupuesto sugerido.
- No aplica se conserva en el historial y bloquea nuevas asignaciones. Los estados de compra reales siguen bloqueando reasignación del mismo nivel.

## Alcance financiero
El registro actualiza el estado y la evidencia en 26_ORDENES_GESTION de MASTER. No concilia automáticamente 02_POSICIONES, 03_LIQUIDEZ, 05_ORDENES ni 06_FILLS. Unidades y liquidez requieren conciliación independiente con la transacción real; la interfaz lo indica. No se ejecutan operaciones en exchanges. Aclaración respecto a una respuesta anterior: guardar el estado no equivale a conciliar inventario y caja.

## Instalación y verificación
Descomprimir y reemplazar el código del repositorio; desplegar en Render. Requiere la sesión administrativa y KAIROS_GOOGLE_WRITER_JSON existentes para escribir estados. No es necesario un cambio de esquema MASTER. El paquete conserva los parches compatibles de GPT de releases anteriores; la nueva interfaz de órdenes corresponde a KairosWeb.

87 pruebas Python aprobadas (suite completa incluida en este paquete), compilación Python y sintaxis JS comprobadas. Renderizado de plantilla con controles verificado por prueba; no se hizo prueba visual de navegador ni escritura contra MASTER real. Pendiente subir a GitHub y desplegar en Render.

## Historial previo

# KairosWeb 3.0.23 — Pivotes MASTER prioritarios

Los pares publicados CL/O1, O2/O3 y O4/O5 se usan como P1/P2 para simular compras. Se conserva precio, fecha y estado del MASTER sin exigir coincidencia con MCP y sin mostrar discrepancias. Un par completo no requiere consultar históricos MCP. Si falta P2, MCP puede proponerlo conservando P1 publicado. No se modifican pivotes ni se ejecutan órdenes. Continúan las validaciones de cronología, precios positivos, P2>P1 y elegibilidad de órdenes/Spot/liquidez. No se elevan estados de pivotes.

SUI publicado: P1=0.6359 / P2=1.2938. Regla general para todos los tokens, sin excepciones por token.

Instalar reemplazando el código de GitHub y desplegar en Render. No cambia MASTER. Pendiente despliegue externo.

## Historial anterior

# KairosWeb v3.0.22 — Indicador junto al objetivo

Se mueve únicamente el indicador desde USD al precio objetivo Fibo. USD queda solo como importe. Se conservan title/aria-label, leyenda inferior y claves numéricas de ordenación para precio, peso, USD y total. Sin cambio de cálculos, estados o MASTER.

Verificación: sintaxis del JavaScript de la plantilla y ubicación del indicador/claves numéricas. Sin prueba visual ni despliegue remoto.

## Antecedente UI v3.0.21 (ubicación del indicador sustituida por v3.0.22)

# KairosWeb v3.0.21 — Tabla Fibo e importes ordenables

USD por escalón muestra solo importe e indicador; se retira el texto visible PROPUESTA/EJECUTADA/NO APLICA. Se mantiene el estado/motivo en title y aria-label. Debajo se añade leyenda compacta de indicadores, distinta del fondo de celda por peso post-compra.

Ordenación de USD, Total USD, precios y pesos usa data-sort-value con el valor numérico original. No analiza símbolos, comas, porcentajes ni texto del estado. Conserva precisión interna, compara números en ambos sentidos, mantiene0 como importe válido y N/D como vacío. No cambia la asignación, clasificación, umbral, ventas condicionadas ni pivotes5L/5R.

Verificado:11 comprobaciones de valores/orden ascendente/descendente; sintaxis del sorter y del JavaScript embebido de la plantilla. No se repitió la suite completa ni prueba visual en navegador. No se modificó MASTER. Pendiente de desplegar. Compatible con GPT1.3.13 y el parche de liquidez de v3.0.20.

## Homologación KairosGPT
Copiar compat/kairos_gpt/buy_weekly_policy.py sobre buy_weekly_policy.py del paquete KairosGPT 1.3.13 para aplicar la misma prioridad MASTER. El archivo es idéntico al selector Web. Esta entrega no instala el parche automáticamente.

Validación: 9 pruebas de prioridad MASTER, 9 de reciclaje de ventas y 8 de pivotes BTC; compilación Python. No se probó navegador ni despliegue.

# KairosWeb v3.0.19 — Pivotes BTC semanales 5L/5R

Corrige el gráfico Portafolio: antes usaba 2 semanas a cada lado; ahora exige extremos estrictos con 5 semanas completas a la izquierda y 5 a la derecha. Se excluye la semana UTC en curso. Las ventanas con semanas faltantes no cuentan como confirmación. Empates no son extremos estrictos.

Se calculan sobre toda la historia disponible (incluidas semanas previas al CL) y se muestran desde la semana del CL publicado hasta la última semana cerrada. Se seleccionan los últimos tres extremos confirmados en orden temporal, sin sustituirlos por candidatos ni colapsar artificialmente extremos consecutivos del mismo tipo. Cada pivote informa confirmed_at_utc: apertura UTC del lunes posterior al cierre de la quinta semana derecha. Si hay menos de tres, se muestran solo los disponibles y el contador n/3.

No cambia el régimen SMA20 de tendencia ni publica pivotes Elliott/CL/O1–O5 en MASTER. Conserva reglas de órdenes y reservas de v3.0.18; compatible con KairosGPT v1.3.13.

Validación actual: 8 pruebas aisladas ejecutan la función de producción (no una copia de su algoritmo), cubren 2R/5R, quinto vecino, empate, últimos tres, historia pre-CL, huecos y semana actual. Compilación Python verificada. La suite completa de Flask no fue repetida en este entorno; falta prueba visual y despliegue remoto. No se cambiaron saldos ni órdenes.

# KairosWeb v3.0.20 — Compras Balancer con ventas

Corrige la condición de reserva Balancer 0 por umbral O2/O4: solo desactiva la reserva/capacidad inicial financiada con liquidez existente. No anula el reciclaje condicionado de ingresos por ventas simuladas.

Compras con ventas = reserva Balancer libre permitida + ingresos de ventas simuladas, una sola vez. El tope porcentual del portafolio limita la reserva inicial, no esos ingresos reciclados. La asignación sigue recalculando pesos después de las ventas, comprando únicamente INFRA y respetando déficit/caja. Si no hay INFRA o se cubre todo el déficit, el sobrante queda sin asignar.

Los USD3694 de la captura son referencia bruta, no ingreso neto certificado. Descontar comisiones y diferencias de ejecución al conciliar. Antes del fill, el monto solo existe en el escenario Con ventas; no cambia liquidez física, QF, inventario, snapshot ni compromisos. No se envían órdenes.

Conserva pivotes BTC semanales5L/5R de v3.0.19 y clasificación de órdenes v3.0.18. Compatible con KairosGPT v1.3.13 aplicando el módulo idéntico incluido en compat/kairos_gpt/liquidity_reserves.py; copiar sobre ese archivo del paquete GPT, sin sustituir el resto. La actualización del módulo requiere instalación, no ocurre por generar este ZIP.

Validación actual:9 pruebas de reserva/asignación condicionada y8 de pivotes5L/5R, ejecutadas sin Flask; compilaciónPython verificada. Suitecompleta y prueba visual no repetidas. Los resúmenes de versiones2.x se consolidan en HISTORIAL_RELEASES_v2.md para mantener menos de100archivos. Pendiente de desplegar en Render; ningún MASTER modificado.

# Kairos v3 · 3.0.0

Paquete de KairosWeb listo para GitHub y Render. Sustituye 2.0.60 y acumula todos los cambios pendientes. KairosGPT conserva su versión y usa el mismo MASTER; este paquete no modifica sus instrucciones ni publica valores financieros.

## Cambios

- Gestión de liquidez: dos donuts, categorías y distribución por venue, con el mismo total de USDT físico y validación de conciliación.
- Actualizar Spot al lado derecho de la navegación. Hora abreviada HH:mm en America/Lima, con fecha completa en el tooltip.
- Los topes de reservas se muestran y editan exclusivamente en Gestión de Portafolio. Se retiran completamente de Parámetros.
- Publicación de objetivos: relectura de todas las celdas modificadas del MASTER antes de confirmar éxito; detectar discrepancias incluso con homologación CURRENT.
- La interfaz exige recargar el mismo snapshot publicado y propaga errores de recarga; evita confirmar un guardado no verificado.
- El alta de objetivos nuevos respeta el rango de lectura actual de parámetros en lugar del límite antiguo de 175 filas.
- Incluye topes configurables de reservas Balancer/Trading, controles de integridad y umbral de movimientos de custodia estrictamente mayor al 5% por token.

## Instalación

1. Descomprimir el ZIP y subir su contenido al repositorio existente conservando static/ y templates/. No subir el ZIP como único archivo. El paquete contiene menos de 100 archivos.
2. Conservar variables y credenciales existentes de Render. El servicio mantiene su nombre kairos-web y no requiere otro servicio.
3. Desplegar el commit en Render. /health debe informar version 3.0.0 y consistencia de assets.
4. Revisar ambas gráficas y la nueva ubicación de Spot. Abrir Configuración: los topes solo aparecen en Gestión de Portafolio.
5. Para un cambio de porcentajes deseado, guardar, validar y confirmar PUBLICAR. Verificar la nueva revisión y los valores del MASTER. La validación previa por sí sola no publica.

## Alcance de verificación

Pruebas locales con datos sintéticos y transporte Google simulado: publicación atómica, auditoría, relectura de porcentajes, rechazo de discrepancias, integridad de reservas, donuts y custodia. Se comprueba sintaxis JavaScript, plantillas Jinja y hashes del paquete.

No se dispone de acceso a los logs o al despliegue de Render. La causa concreta del incidente del usuario en producción no está confirmada. En el MASTER inspeccionado ya existen los tres parámetros del reparto de liquidez: el límite antiguo de filas no explica por sí solo ese caso. Las mejoras evitan una confirmación falsa y verifican persistencia. No se ejecutó una prueba de escritura real ni se cambiaron porcentajes en el MASTER.

La suite histórica conserva incompatibilidades conocidas de autenticación, versión antigua y botones retirados. No se declara la suite completa como aprobada. No se realizó verificación visual en navegador.

Resultado local de esta versión: 68 pruebas y 8 subtests aprobados; comprobaciones de JavaScript, plantillas y consistencia de assets aprobadas.
