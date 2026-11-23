(() => {
  'use strict';
  const {positions, pivots} = JSON.parse(document.getElementById('forecast-input').textContent);
  const chart = document.getElementById('forecast-chart');
  const status = document.getElementById('forecast-chart-status');
  const select = document.getElementById('forecast-token');
  const table = document.getElementById('forecast-projections');
  const names = ['O1', 'O2', 'O3', 'O4', 'O5'];
  const decimal = new Intl.NumberFormat('es-PE', {maximumFractionDigits: 12});
  const currency = new Intl.NumberFormat('es-PE', {minimumFractionDigits: 2, maximumFractionDigits: 2});
  const {wavePath} = window.KairosForecastFibo;
  const rows = new Map(pivots.map(pivot => {
    const wave = wavePath(pivot, {o2: .618, o3: 1.618, o4: .5, o5: 1.618});
    const prices = wave.values && wave.state !== 'ESTRUCTURA_INCOMPATIBLE'
      ? wave.values.slice(1) : names.map(() => null);
    return [pivot.token, prices];
  }));

  function cell(row, label, value, privacy) {
    const line = document.createElement('div');
    const caption = document.createElement('small');
    const content = document.createElement('span');
    caption.textContent = label + ' ';
    content.textContent = value;
    if (privacy) content.dataset.private = privacy;
    line.append(caption, content);
    row.append(line);
  }

  for (const position of positions) {
    const tr = table.insertRow();
    const name = document.createElement('th');
    name.scope = 'row';
    name.textContent = position.token;
    tr.append(name);
    const quote = position.token === 'HYPE' ? 'USDC' : 'USDT';
    for (const price of rows.get(position.token)) {
      const td = tr.insertCell();
      cell(td, 'Precio', price === null ? 'N/D' : decimal.format(price) + ' ' + quote);
      cell(td, 'Unidades', decimal.format(position.units), 'units');
      cell(td, 'Monto', price === null ? 'N/D' : currency.format(price * position.units) + ' ' + quote, 'money');
    }
  }

  function draw() {
    const token = select.value;
    const prices = rows.get(token) || [];
    chart.hidden = !prices.some(price => Number.isFinite(price));
    if (chart.hidden) {
      status.textContent = token ? token + ' · Sin anclas semanales suficientes para proyectar.' : 'Sin tokens activos.';
      return;
    }
    const quote = token === 'HYPE' ? 'USDC' : 'USDT';
    status.textContent = token + ' · Precio por onda en ' + quote;
    chart.setAttribute('aria-label', status.textContent);
    const ctx = chart.getContext('2d');
    const min = Math.min(...prices);
    const span = Math.max(...prices) - min || 1;
    const x = i => 65 + 117 * i;
    const y = price => 265 - 208 * (price - min) / span;
    ctx.clearRect(0, 0, chart.width, chart.height);
    ctx.lineWidth = 4;
    ctx.strokeStyle = '#3b91e4';
    ctx.beginPath();
    prices.forEach((price, i) => i ? ctx.lineTo(x(i), y(price)) : ctx.moveTo(x(i), y(price)));
    ctx.stroke();
    const textScale = parseFloat(getComputedStyle(chart).getPropertyValue('--kairos-text-scale')) || 1;
    ctx.font = (23 * textScale) + "px system-ui";
    ctx.textAlign = 'center';
    ctx.fillStyle = getComputedStyle(chart).color;
    prices.forEach((price, i) => {
      ctx.fillText(names[i], x(i), 312);
      ctx.fillText(decimal.format(price), x(i), y(price) - 14, 113);
    });
  }
  select.addEventListener('change', draw);
  window.addEventListener('kairos:text-size', draw);
  draw();
})();
