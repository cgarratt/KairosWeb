/* Pure, deterministic mark-to-market scenario projection; no hypothetical fills. */
(function (root) {
  'use strict';
  const STAGES = [
    {name:'O1 → O2', from:1, to:2, tag:'Corrección O2'},
    {name:'O2 → O3', from:2, to:3, tag:'Impulso O3'},
    {name:'O3 → O4', from:3, to:4, tag:'Corrección O4'},
    {name:'O4 → O5', from:4, to:5, tag:'Impulso O5'}
  ];
  function amount(n){return Number.isFinite(n) && n>=0 ? n : 0;}
  function buildForecastSegments(waves, tokens, cash) {
    if (!Array.isArray(waves) || !Array.isArray(tokens) || !Number.isFinite(cash) || cash < 0) {
      throw new Error('SCENARIO_INPUT_INVALID');
    }
    const bySymbol = new Map(waves.map(w => [w.token, w]));
    return STAGES.map(stage => {
      const rows = tokens.map(token => {
        const wave = bySymbol.get(token.token);
        const valid = Boolean(wave && Array.isArray(wave.values) &&
          [wave.values[stage.from], wave.values[stage.to]].every(n => Number.isFinite(n) && n > 0));
        const spot = Number(token.price);
        if (!Number.isFinite(spot) || spot <= 0) throw new Error('INVALID_SPOT_'+token.token);
        const units = Number.isFinite(token.units) ? Number(token.units) : Number(token.current_usdt) / spot;
        if (!Number.isFinite(units) || units < 0) throw new Error('INVALID_HOLDINGS_'+token.token);
        const start = valid ? wave.values[stage.from] : spot;
        const end = valid ? wave.values[stage.to] : spot;
        return {
          token: token.token, units: units,
          start_price: valid ? start : null, end_price: valid ? end : null,
          price_for_valuation_start: start, price_for_valuation_end: end,
          start_usdt: units * start, end_usdt: units * end,
          delta_usdt: units * (end - start),
          state: !valid ? 'SPOT_FIJO_ND' : wave.state === 'SOLAPAMIENTO O4 / O1' ? 'RECUENTO_INVALIDO' : 'SIMULADO',
          projection_available: valid
        };
      });
      const points=[];
      for(let step=0;step<=4;step++){
        const fraction=step/4;
        const crypto=rows.reduce((sum,r)=>sum+r.units*(r.price_for_valuation_start+(r.price_for_valuation_end-r.price_for_valuation_start)*fraction),0);
        points.push({progress_pct:100*fraction, crypto_usdt:crypto, liquidity_usdt:cash, portfolio_usdt:crypto+cash});
      }
      const first=points[0], last=points[points.length-1];
      return {
        ...stage, rows, points,
        missing:rows.filter(r=>!r.projection_available).map(r=>r.token),
        invalid:rows.filter(r=>r.state==='RECUENTO_INVALIDO').map(r=>r.token),
        total:{start_crypto:first.crypto_usdt,end_crypto:last.crypto_usdt,
          liquidity:cash,start_portfolio:first.portfolio_usdt,end_portfolio:last.portfolio_usdt,
          delta:last.portfolio_usdt-first.portfolio_usdt}
      };
    });
  }
  const api={STAGES,buildForecastSegments};
  root.KairosForecastSegments=api;
  if(typeof module==='object' && module.exports) module.exports=api;
})(typeof globalThis !== 'undefined' ? globalThis : this);
