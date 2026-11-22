# KairosWeb 4.6.7

Portafolio de solo lectura para snapshots publicados con fills históricos aún sin orden vinculada. La lectura conserva los controles de saldos, posiciones y custodia. Los fills no certificados se muestran como pendientes y no liberan compromisos. El total queda pendiente si la caja no está conciliada.

Descomprimir en la raíz del repositorio privado de KairosWeb y desplegar con el `render.yaml` incluido. Conservar variables de entorno y verificar `/health` (versión 4.6.7, HTTP 200), inicio de sesión, Portafolio y Actualizar Spot. Confirmar el bloqueo de Compras, Balancer y Órdenes mientras corresponda. Si el despliegue falla, volver al commit anterior.

El ZIP se probó en local con una lectura del MASTER y un lote de precios sintético. No modifica Sheets ni despliega Render por sí mismo.
