# KairosWeb v1.1.0 RC2 — Corrección de contraste en modo oscuro

**Motivo:** paneles informativos, notas y pistas visuales con fondos claros y texto heredado del tema oscuro, resultando ilegibles.

## Cambios
- Corrección global en `static/theme.css` para tarjetas y avisos de Dashboard, Balancer, Compras, Ventas, Forecast, TradingBot, Portafolio Integral y Settings.
- Notas de advertencia usan fondo oscuro ámbar y texto marfil legible; tarjetas informativas fondo azul marino y texto claro.
- Barras, tablas y totales dejan de tener franjas blancas incompatibles con el modo oscuro.
- El tema claro permanece sin modificar.
- No se modifican Google Sheets, la lógica de trading, las credenciales, las API ni las posiciones.

## Despliegue
Reemplazar `static/theme.css`, `templates/base.html` y `app.py` por los de RC2 (el HTML incluye versión en URL del CSS para evitar caché), o subir todo el paquete descomprimido. El `health` reflejará `1.1.0-rc2`.
Verificar en ambos temas Dashboard, Balancer, Compras, Ventas, Forecast y Portafolio Integral. No desplegado por el asistente.
