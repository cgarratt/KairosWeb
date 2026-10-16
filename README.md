# Kairos Web v4.0.2 — estabilidad de conexión MCP

Parche sobre v4.0.1. Sin cambios de política de portafolio ni de interfaz.

- Registra en Render `http_status` HTTP real para errores httpx.HTTPStatusError, incluso anidados en ExceptionGroup.
- Los logs contienen solo ID, proveedor, tipo y código HTTP; nunca URL/token/cabeceras/trazas con secretos.
- `/api/mcp-diagnostics` devuelve `diagnostic.http_status` cuando está disponible.
- Una sola petición de mercado en vuelo por proceso. Caché de 30 segundos con `observed_at` original; no ofrece cotizaciones caducadas como LIVE.
- Gunicorn pasa a 1 worker y 8 threads para compartir caché en el plan Free.

## Instalación
Copiar contenido de esta carpeta a la raíz del repo KairosWeb; commit/push a main. Mantener variables de entorno de Render. Después probar `/api/mcp-diagnostics`, `/api/portfolio`, `/mode/balancer`, `/mode/compras` y `/mode/ventas`.

## Nota
Un 502/503/504 de Render o del MCP necesita revisión operativa del servicio remoto; el parche registra el HTTP exacto y no promete resolver errores upstream.

## Ajuste v4.0.3 — Reserva Balancer

- Reserva Balancer actual = max(0, USDT físico consolidado − 25% P − Reserva Trading QF).
- No se aplica mínimo de liquidez 40% ni techo 5% P al cálculo de esa reserva.
- Reserva con ventas sugeridas = reserva actual + ventas brutas sugeridas (escenario hipotético).
- El piso 40% permanece como indicador aparte, sin restringir este cálculo.
- Los montos siguen siendo referenciales hasta reconciliar LIMIT, reservas y comisiones.


## v4.0.4 Compras a dos etapas

- El slider mantiene máximo = (USDT consolidado − QF) / patrimonio.
- Etapa 1: aporte para corregir infraponderaciones; si alcanza, se diluyen sobrepesos SIN vender.
- Etapa 2: resto del presupuesto asignado proporcionalmente a los targets entre TODOS los tokens.
- Columna diferenciada por etapa y presupuestos C1/C2 estimados.
- No equivale a orden ejecutable; el límite de 40% sigue como aviso, no como techo del simulador.
- C1/C2 todavía sin anclas verificadas.

## v4.0.5 Ventas
- Slider inicia en porcentaje de USDT actual y termina en 40%; si ya supera 40%, inicia en 40% para mantener rango válido.
- Eliminada la tabla de inventario Tier/Custodia.
- Candidatos SELL incluyen peso actual, objetivo y peso post-venta sobre manga cripto tras descontar ventas del denominador.
- Sin ejecución automática, BTC NEVER SELL y unidades Exchange limitan ventas hipotéticas.


## v4.0.6 — Slider de Ventas

- Mínimo: porcentaje USDT actual del portafolio.
- Máximo: 70% USDT (o liquidez actual si supera 70%, para no invertir el rango).
- Valor inicial: 40% cuando el porcentaje actual sea menor, de lo contrario el actual.
- Recalcula propuestas SELL, unidades y pesos post-venta; BTC NEVER SELL, Exchange disponible y simulación sin ejecución.
