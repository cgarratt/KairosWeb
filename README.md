# KairosWeb v2.0.9 — Release acumulativo compacto

Base: release v2.0.8 con todas las mejoras acumuladas; fase 1 de Órdenes y simulación con pivotes PROPUESTO integradas en v2.0.9.

## Funciones conservadas de v2.0.8
- Configuración: logos decorativos para los 12 tokens en Maestro de unidades, Objetivos/Tiers y tabla de Pivotes. PUMPFUN usa el logo PUMP. Sin logos artificiales en parámetros, tiers o venues.
- Balancer: "Presupuesto Compras" = USDT físico − Reserva Trading QF, sin confundir 25% P ni sumar otra bolsa Balancer a la caja.
- Compras: separar máximo USDT físico − QF, compra simulada elegible y liquidez sin asignar; no redistribuir cuotas bloqueadas. Slider inicia al máximo disponible.
- Pivotes: estados PROPUESTO / VALIDADO / CONFIRMADO; revisión masiva desde MCP con el único botón "Actualizar candidatos desde MCP", sin botones por token. VALIDADO exige evidencia semanal 5L/5R+BOS, CONFIRMADO solo mediante publicación administrativa posterior.
- Modo Compras: admite simular con extremos PROPUESTO, VALIDADO o CONFIRMADO de un impulso alcista semanal trazable (precio y fecha), sin permitir órdenes ejecutables solo por un estado PROPUESTO. N/D bloquea compras. O2/O4/retroceso genérico (porcentajes O2) conservan la lógica aprobada.
- Modo Ventas: SIN filtro de pivotes; Exchange libre, BTC NEVER SELL y HODL/Core protegidos.
- Forecast, gestión de alertas 1H/4H/1D, donut integral y demás funciones de v2.0.7 preservadas.

## Despliegue
Extraer el contenido del ZIP a la raíz del mismo repositorio GitHub (preservar `templates/`, `static/`, `tests/`). No subir credenciales, ni copiar ZIPs como datos financieros. En Render validar `/health` (`version=2.0.9`, `release_assets.consistent=true`) y probar las tres secciones de Configuración con logos, ambos modos y guardado autorizado de pivotes. **El ZIP no modifica automáticamente el Master ni ejecuta órdenes.**

## v2.0.9: Modo Órdenes (fase 1, solo lectura)
- Nueva página `/mode/ordenes`: dos estrategias independientes, `BALANCE` y `ESTRUCTURA`.
- Propuestas por Binance/KuCoin/Hyperliquid, por token, BUY/SELL y proximidad al objetivo.
- Estructura: BUY desde retrocesos semanales, SELL desde extensiones publicadas O3/O5 o impulso genérico correctamente identificado (sin llamar O3/O5 a proyecciones de 2 anclas).
- Balance: BUY/SELL por desviación, sin inventar precios LIMIT. Respeta Exchange libre, HODL/Core y BTC NEVER SELL.
- Ningún botón coloca/cancela órdenes; no se registran propuestas como fills o saldos. `05_ORDENES` / `06_FILLS` siguen reservados a operaciones reales verificadas.
- Es necesario validar la interfaz en Render, usando datos MCP y Master publicados. No habilitar fase 2 sin controles adicionales.
