"""Development: alert bell directional emphasis and source-mode evidence."""
from pathlib import Path

from kairos_sheets_features import _alert_origin_mode, alert_inbox

ROOT=Path(__file__).resolve().parents[1]


def test_prefer_explicit_origin_and_known_modes():
    for key,mode in [('BALANCER','Balancer'),('TradingBot','TradingBot'),('COMPRAS','Compras'),('VENTAS','Ventas')]:
        label,identified=_alert_origin_mode({'modo_origen':key,'tipo_alerta':'BREAK_ALCISTA','regla_clave':'STRUCTURE'})
        assert (label,identified)==(mode,True)


def test_unambiguous_rules_only_and_breaks_have_no_invented_tradingbot_mode():
    assert _alert_origin_mode({'tipo_alerta':'BREAK_ALCISTA','regla_clave':'BREAK_4H'})==('Alertas',False)
    assert _alert_origin_mode({'tipo_alerta':'BREAK_BAJISTA','regla_clave':'STRUCTURE'})==('Alertas',False)
    assert _alert_origin_mode({'tipo_alerta':'BREAK_BAJISTA','regla_clave':'TB_SHORT_4H_1H'})==('TradingBot',True)
    assert _alert_origin_mode({'tipo_alerta':'NIVEL_PROXIMO','regla_clave':'O2C3'})==('Compras',True)
    assert _alert_origin_mode({'tipo_alerta':'NIVEL_TOCADO','regla_clave':'O5V2'})==('Ventas',True)
    assert _alert_origin_mode({'tipo_alerta':'BALANCER_ACCION'})==('Balancer',True)
    assert _alert_origin_mode({'tipo_alerta':'BSI_ACCION'})==('BSI',True)


def test_backend_exposes_mode_and_source_resolution_in_same_event():
    run=['corrida_id','marco']
    fields=['evento_id','corrida_id','marco','tipo_alerta','regla_clave','token','creado_utc','accion_sugerida','clave_senal','modo_origen']
    data=[
        ['b','r','4H','BREAK_BAJISTA','TB_SHORT_4H_1H','PLUME','2026-10-18T08:27:00Z','Revisar estructura','PLUME|4H|BREAK',''],
        ['a','r','4H','BREAK_ALCISTA','STRUCTURE','HBAR','2026-10-18T12:19:00Z','Revisar estructura','HBAR|4H|BREAK',''],
        ['e','r','4H','BREAK_ALCISTA','STRUCTURE','BTC','2026-10-18T12:20:00Z','Revisar estructura','BTC|4H|BREAK','VENTAS'],
    ]
    blocks={'runs':[run,['r','4H']], 'events':[fields,*data], 'receipts':[['evento_id','leido_utc']]}
    result=alert_inbox(blocks)
    found={r['id']:r for r in result['records']}
    assert found['b']['mode']=='TradingBot' and found['b']['mode_identified']
    assert found['a']['mode']=='Alertas' and not found['a']['mode_identified']
    assert found['e']['mode']=='Ventas' and found['e']['mode_identified']
    assert all(not item['is_trade_ready'] for item in found.values())


def test_ui_includes_directional_badges_and_removes_informativa():
    js=(ROOT/'static/alert_bell.js').read_text()
    css=(ROOT/'static/alerts_settings.css').read_text()
    assert 'event-bull' in js and 'event-bear' in js
    assert 'BREAK_ALCISTA' in js and 'BREAK_BAJISTA' in js
    assert 'alert-mode' in js and 'mode_identified' in js
    assert "'INFORMATIVA'" not in js
    for token in ('.alert-event-type.event-bull','.alert-event-type.event-bear',':root[data-theme="dark"] .alert-event-type.event-bull'):
        assert token in css
    assert "'events': \"'16_ALERTAS_EVENTOS'!A1:V2000\"" in (ROOT/'kairos_sheets_features.py').read_text()
