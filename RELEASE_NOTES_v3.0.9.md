# KairosWeb v3.0.9 — Protección de pivotes publicados

- Los candidatos históricos MCP no modifican los valores ni fechas CL/O1–O5 de 07_PIVOTES, incluso con estado PROPUESTO.
- La interfaz muestra candidatos MCP solo como información de referencia; edición y publicación siguen siendo acciones administrativas explícitas.
- Protege los cambios locales aún sin publicar frente a respuestas MCP asíncronas.
- Regresión específica: SUI, PUMPFUN y VIRTUAL conservan O1 posterior a CL tras cargar candidatos.
- Sin modificación de MASTER, saldos, pivotes ni órdenes.
