# KairosWeb v1.1.0 RC2.1 — hotfix de inicio de sesión administrativo

## Hallazgo

La URL `/admin/login` entregaba `Origen no autorizado` (HTTP 403) al **enviar el formulario POST**, sin evaluar la contraseña. La comprobación original exigía `Origin` o `Referer` comparables con `request.host_url`. Dado el `Referrer-Policy: no-referrer` y algunas combinaciones de navegador/proxy, esas cabeceras pueden faltar, tener `Origin: null`, o reflejar el host interno de Render.

## Corrección

- Añadido `admin_origin.py`: valida explícitamente Origin/Referer y metadatos `Sec-Fetch-Site`, contemplando el hostname externo configurado por Render. No acepta orígenes externos.
- Formulario `/admin/login` con token CSRF aleatorio ligado a la sesión (cookie HttpOnly, Secure, SameSite Strict), obligatorio en **todos** los POST y de un solo uso.
- Si las cabeceras de procedencia están ausentes, solo el POST **de inicio de sesión** con CSRF válido puede usar la vía alternativa; los endpoints de escritura sin CSRF no adquieren ese privilegio.
- `Referrer-Policy: same-origin`: navegador puede enviar Referer a rutas propias, sin enviarlo a terceros.
- Se conserva la clave de administración, la validación del token CSRF de Settings, el control del snapshot PUBLICADO y las restricciones financieras.

## Instalación

Reemplazar `app.py`, `templates/admin_login.html` y agregar `admin_origin.py` en la raíz del repositorio desde el ZIP de hotfix. Guardar los cambios en GitHub, desplegar en Render y abrir `/health`: `version: 1.1.0-rc2.1`.

Luego abrir `/admin/login` **desde la misma web** y pulsar Iniciar sesión. Tras ingresar la clave administrativa configurada en Render, deberá redirigir a `/settings` con sesión activa. Si aparece «Sesión de acceso caducada», recargar `/admin/login` antes de volver a enviar.

**No publicar cambios financieros para probar el acceso.** Comprobar primero en `/api/settings/data` que `is_admin` sea verdadero. La primera escritura debe ser un cambio legítimo autorizado.

No se requieren nuevos secretos ni modificaciones a Google Sheets o KairosGPT. En despliegues proxy no estándar se admite opcionalmente `KAIROS_PUBLIC_ORIGIN=https://tu-dominio-confirmado`, nunca URLs ajenas.

## Pruebas locales

`python -m pytest -q`: 65 pruebas pasan.

`node tests/test_settings_format.js` y `node tests/test_forecast_segments.js`: PASS. `node --check static/*.js`: PASS. Plantillas Jinja y sintaxis Python: PASS.

**Pendiente de confirmar:** flujo HTTP completo en Render; este entorno no tiene Flask/FastMCP instalados para la prueba de integración en servidor.
