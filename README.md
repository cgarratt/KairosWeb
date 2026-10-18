# KairosWeb v2.0.5 RELEASE

Aplicación web independiente de KairosGPT. Contrato Google Sheets `schema_version=5.0.0`.

**Guía y cambios:** [`RELEASE_NOTES_v2.0.5.md`](RELEASE_NOTES_v2.0.5.md). Para actualizar GitHub, extrae el ZIP **en la raíz del repositorio** y reemplaza tanto `app.py` como `templates/` y `static/`. No cargar solo archivos Python ni un ZIP como archivo aislado.

Verificación posterior en Render: `/health` debe mostrar `version=2.0.5`, `status=UP` y `release_assets.consistent=true`. En `/mode/compras` verificar el atributo `data-o2-ui-version=2.0.5` y los círculos en precios Fibonacci.

No contiene credenciales ni ejecuta órdenes. Las simulaciones no alteran el inventario PUBLICADO.

## Paquete compacto para GitHub
Esta distribución conserva la versión **2.0.5** sin cambios funcionales. Se han separado las notas y las pruebas históricas de los archivos necesarios para actualizar GitHub. El ZIP debe descomprimirse antes de subir su **contenido** (no el ZIP en sí) a la raíz de `cgarratt/KairosWeb`, incluidas `templates/` y `static/`. Los archivos previos que ya existan en GitHub no se eliminan por la carga; puedes archivarlos o borrarlos posteriormente mediante un commit separado.

**Pendiente para un futuro release:** el gráfico donut de capital histórico, no incluido en esta edición de empaquetado.
