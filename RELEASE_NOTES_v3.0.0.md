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
