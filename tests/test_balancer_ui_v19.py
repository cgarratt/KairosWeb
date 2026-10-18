"""Ensure Balancer presentation has exactly the short labels and preserves the basis."""
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parents[1]
class Req:path='/mode/balancer'

def test_live_jinja_balancer_percent_and_short_labels():
    env=Environment(loader=FileSystemLoader(ROOT/'templates'),autoescape=True)
    env.globals.update(request=Req(),nav_modes=[],url_for=lambda endpoint,**kw:'/static/'+kw.get('filename','') if endpoint=='static' else '/settings')
    cur=SimpleNamespace(P=84276,cash=27500,floor=33710,gap=6210,reserve=0,operational_25=21069,trading=7225,current_cash_capacity=0,projected_cash_capacity=0)
    payload=SimpleNamespace(current=cur,snapshot_note='SYNTHETIC',sell_total=0,buys=[],sells=[],buy_with_sales=[],buy_chart=[],sell_chart=[],buy_cash_after=0,buy_total=0,sell_cash_after=0,limitations='TEST')
    html=env.get_template('balancer.html').render(payload=payload,master='1.9.0')
    for text in ['Presupuesto Compras','Reserva Balancer estimada','Reserva Trading','$20,275','73.7% USDT físico','26.3% USDT físico','no sumar otra vez']:
        assert text in html,text
    assert 'Presupuesto compras O2/O4 · máximo 25% P (no acumulativo)' not in html
