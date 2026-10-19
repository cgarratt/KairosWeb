# KairosWeb v2.0.18 — Semáforo Fibonacci por peso post-compra

## Alcance

Release sobre v2.0.17; se modifica únicamente la **visualización** del resultado de simulaciones de Compras en la matriz Fibonacci (y controles de integridad); no se cambian precios Fibonacci, generación de propuestas, ventas, presupuesto del slider, porcentajes de cestas o conexión a datos.

## Criterio exacto

- Sin USDT positivo visible en un token/cesta (importes que se redondean a `$0.00` incluidos), **no colorear** ningún campo de la tríada Precio, % Peso y USDT.
- Con compra simulada visible positiva, calcular peso *después de la compra* para ese token en la valoración del tramo, comparar con el target de la manga cripto del Master; clasificar desviación en **pp**.
- Verde: `postWeightPP - targetPP >= 0`, ámbar: `-1 <= driftPP < 0`, rojo: `driftPP < -1`.
- El tooltip de la tríada informa compra hipotética, peso post-compra, peso objetivo y desviación en pp; sin señales falsas de fills.
- Ya **no** se usan velas o mínimos históricos post-P2 para elegir el color. Los semáforos P1/P2 (PROPUESTO/VALIDADO/CONFIRMADO) siguen independientes y sin alteración.
- La semántica de colores no altera INFRA ni la elección de tokens: sólo afecta celdas del resultado. La protección QF, límite de déficit y elegibilidad siguen implementados en el simulador secuencial.

## Pruebas

- Python `python -m pytest -q`, JS `node tests/*.js` individualmente, sintaxis JS, compilación Python, Jinja, marcadores `/health`, manifiesto SHA-256; verificar el resultado real en el entorno de despliegue.
- Casos de borde: USDT 0, redondeo < $0.005, postWeight indefinido, justo en target, -1 pp exacto, inferior a -1 pp y valores de simulación reales de 4 tramos.

## Despliegue

ZIP completo para GitHub, no modifica Google Sheets, GitHub, Render, exchanges ni órdenes al ser creado. El usuario realiza el commit/despliegue por separado.
