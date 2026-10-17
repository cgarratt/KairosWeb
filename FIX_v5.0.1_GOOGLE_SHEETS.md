# Kairos Web 5.0.1 — Corrección del lector de Google Sheets

## Causa verificada

En el archivo **KAIROS_V5_MASTER**, los rangos de `05_ORDENES` y `06_FILLS` incluyen una nota explicativa en **A58**. El lector v5.0 interpretaba equivocadamente cualquier celda no vacía (incluyendo las notas) como una orden/fill y lanzaba `SheetDataError`, impidiendo cargar toda la aplicación.

## Corrección

- El lector acepta exclusivamente esas dos notas editoriales literales, y solo cuando la fila tiene las demás columnas vacías.
- Las órdenes/fills verdaderos, registros incompletos y notas desconocidas siguen provocando `DATA_ERROR` hasta conciliación; no se permiten inventarios ni fondos libres por inferencia.
- Se incluye `category` segura en `/api/sheets-status`, y se registra en logs sin revelar credenciales.
- `/health` reporta **5.0.1**. El contrato del snapshot sigue usando `schema_version=5.0.0` y `snapshot_id=KAIROS-2026-10-17-001`; no modifica Google Sheets ni parámetros.

## Instalación

Subir a GitHub **el contenido** de esta carpeta reemplazando la v5.0 (puedes subir solo `google_sheets_master.py`, `app.py` y opcionalmente los tests si ya tienes todo lo demás de v5.0). Realizar commit y desplegar latest commit en Render. No cambiar ni compartir las claves JSON.

1. `/health` debe devolver `version: 5.0.1`.
2. `/api/sheets-status` debería devolver `status: OK`, `source: GOOGLE_SHEETS`, 12 tokens, 112 o más parámetros y reparto O5 30/70.
3. Si permanece DATA_ERROR, comunicar **solo `category`** (sin contenido de variables de entorno) para localizar el siguiente bloqueo.
4. Probar `/api/portfolio` y la pantalla principal, después de cargar un snapshot válido.

**No se ha validado la autenticación privada de Google/Render en este entorno local.** Este parche corrige una causa demostrada en el esquema de Google Sheets vigente; si persiste una falla de credenciales, la nueva categoría ayuda a identificarla sin filtrarlas.
