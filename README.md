# KairosWeb v2.0.8 — Release acumulativo compacto

Base: v2.0.7 HOTFIX1 + desarrollo acumulativo de liquidez, presupuesto y estados PROPUESTO → VALIDADO → CONFIRMADO.

## Nuevo en esta versión
- Configuración: logos decorativos para los 12 tokens en Maestro de unidades, Objetivos/Tiers y tabla de Pivotes. PUMPFUN usa el logo PUMP. Sin logos artificiales en parámetros, tiers o venues.
- Balancer: "Presupuesto Compras" = USDT físico − Reserva Trading QF, sin confundir 25% P ni sumar otra bolsa Balancer a la caja.
- Compras: separar máximo USDT físico − QF, compra simulada elegible y liquidez sin asignar; no redistribuir cuotas bloqueadas. Slider inicia al máximo disponible.
- Pivotes: estados PROPUESTO / VALIDADO / CONFIRMADO; revisión masiva desde MCP con el único botón "Actualizar candidatos desde MCP", sin botones por token. VALIDADO exige evidencia semanal 5L/5R+BOS, CONFIRMADO solo mediante publicación administrativa posterior.
- Modo Compras: ambos extremos del último impulso alcista deben estar VALIDADO o CONFIRMADO en el Master publicado y coincidir con estructura semanal 1W; PROPUESTO bloquea compras. O2/O4/regreso alcista genérico (porcentajes O2) conservan lógica aprobada.
- Modo Ventas: SIN filtro de pivotes; Exchange libre, BTC NEVER SELL y HODL/Core protegidos.
- Forecast, gestión de alertas 1H/4H/1D, donut integral y demás funciones de v2.0.7 preservadas.

## Despliegue
Extraer el contenido del ZIP a la raíz del mismo repositorio GitHub (preservar `templates/`, `static/`, `tests/`). No subir credenciales, ni copiar ZIPs como datos financieros. En Render validar `/health` (`version=2.0.8`, `release_assets.consistent=true`) y probar las tres secciones de Configuración con logos, ambos modos y guardado autorizado de pivotes. **El ZIP no modifica automáticamente el Master ni ejecuta órdenes.**
