# KairosWeb v2.0.45 — HYPE quote-only pending order hotfix

- Permite órdenes pendientes BUY de HYPE en Hyperliquid con precio y presupuesto documentados, sin unidades observadas.
- Requiere marca PENDIENTE_ID_QTY_QUOTE_INSTRUMENTO y evidencia; no fabrica ID ni unidades.
- Conserva reserva separada USDC y bloqueo conservador de compras mientras no se concilie la cotización.
- Mantiene rechazos por duplicados, evidencia ausente, presupuesto no positivo y cantidades inconsistentes.
- Pruebas con 14 órdenes pendientes de estructura equivalente al MASTER: 11 Binance/KuCoin y 3 Hyperliquid.
- Sin escrituras al MASTER ni órdenes remotas.
