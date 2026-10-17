# KairosWeb v2.0.2 — Compras O2 secuenciales

Cada tramo O2C1–O2C4 revaloriza las posiciones con los precios de su escenario, incorpora unidades de compras simuladas anteriores, recalcula déficits y distribuye únicamente su tramo de presupuesto. No se contabiliza doble gasto. Los activos que pasan de sobreponderados a infraponderados pueden recibir USDT en niveles posteriores. Sin pivotes válidos no se simulan fills para ese token; esa parte de la caja queda sin gastar. Los semáforos se determinan por tramo. No ejecuta órdenes ni escribe al Master.
