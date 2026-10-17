# KairosWeb · Ajuste Forecast por balanceo dinámico (v1.8.0)

Implementado en la copia local de desarrollo basada en **v1.7.0**. Incluido en el release v1.8.0; NO se ha desplegado ni escrito en Google Sheets.

## Motor

- Ventas O3: para cada extensión Fibonacci calcula presupuesto sobre el pool elegible congelado, distribuye ventas dando prioridad a la sobreponderación de cada activo contra targets de la manga cripto **ex-USDT**, usando optimización con límite de unidades disponibles en Exchange. BTC NEVER SELL; HODL/Core no vendibles en O3. Se detiene al objetivo estructural de USDT del Master.
- Recompras O4: al alcanzar cada retroceso, recalcula posición actual y déficits a los targets después de O3, nuevas unidades BTC y tramos O4 anteriores. Despliega primero a infraponderados elegibles y después distribuye excedente según target. Se limita al presupuesto máximo 25% P de la onda, caja libre física y reserva QF.
- O5: sigue como salida de ciclo, sin tratar de forzar targets de acumulación ni limitar liquidaciones finales por objetivo USDT 40%. Solo Exchange/Core elegible, BTC NEVER SELL y HODL protegido.
- Split de fondos de venta: parámetros **APROBADOS** obtenidos dinámicamente del `12_PARAMETROS_KAIROS`, en cada carga, validados como fracciones complementarias que suman 100% por separado. La última consulta real observó O3=30% BTC/70% USDT y O5=50% BTC/50% USDT; NO se codifican como constantes de ejecución.
- Simulación hipotética SIN operaciones, SIN escritura/guardado en Google Sheets. BTC compra hipotética tras SELL sigue siendo distinta de cualquier fill real.
- Se muestra peso actual, target y desvío ±pp por token y etapa. Un balance exacto puede ser estructuralmente imposible si BTC está sobreponderado (NEVER SELL), HODL/Core está bloqueado, liquidez/QF no disponible, o faltan niveles de precio.

## Componentes cambiados

- `app.py`: validación y payload de los dos splits oficiales independientes.
- `static/forecast_balance.js`: algoritmo puro de compra/venta según drift y capacidad elegible.
- `templates/forecast.html`: uso secuencial de nuevo motor, información de split solo lectura y drift por onda.
- `tests/test_forecast_balance.js`, `tests/test_forecast_balance_upgrade.py`, `tests/browser_forecast_balance_upgrade.py`: controles de invariantes y flujo en navegador.
- `tests/browser_forecast_v14.py`: fixture actualizado con ambas cuotas para compatibilidad con pruebas anteriores.

## Tests ejecutados

- `pytest -q`: 119 passed, 3 subtests passed.
- `node tests/test_forecast_balance.js`: PASS.
- `python tests/browser_forecast_v14.py`: PASS.
- `python tests/browser_release_v17.py`: PASS.
- `python tests/browser_forecast_balance_upgrade.py`: PASS.

El ZIP v1.8.0 se entrega para despliegue autorizado por el usuario; no se realizó un deploy.
