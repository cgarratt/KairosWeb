"""The portfolio-physical reserve must not be replaced by a 25%-of-P reference."""
from pathlib import Path
from types import SimpleNamespace
from jinja2 import Environment, FileSystemLoader

ROOT=Path(__file__).resolve().parents[1]
class Request: path='/mode/balancer'

def render(trading=7225, cash=27520, reserve=0):
    env=Environment(loader=FileSystemLoader(ROOT/'templates'), autoescape=True)
    env.globals.update(request=Request(),nav_modes=[],url_for=lambda endpoint,**kw:'/static/'+kw.get('filename','') if endpoint=='static' else '/settings')
    cur=SimpleNamespace(P=83828,cash=cash,floor=33531,gap=0,reserve=reserve,operating=cash-trading,operational_25=20957,trading=trading,current_cash_capacity=reserve,projected_cash_capacity=reserve)
    payload=SimpleNamespace(current=cur,snapshot_note='SYNTHETIC',sell_total=0,buys=[],sells=[],buy_with_sales=[],buy_chart=[],sell_chart=[],buy_cash_after=0,buy_total=0,sell_cash_after=0,limitations='TEST')
    return env.get_template('balancer.html').render(payload=payload,master='2.0.7')

def test_budget_uses_cash_less_qf_not_25_percent_p():
    html=render()
    assert 'Presupuesto Compras</span><strong>$20,295</strong>' in html
    assert 'Reserva Trading</span><strong>$7,225</strong>' in html
    assert 'Reserva Balancer estimada</span><strong>$0</strong>' in html
    assert '73.7% USDT físico' in html
    assert '26.3% USDT físico' in html
    assert '$20,957' not in html
    assert 'Las bolsas nominales exceden' not in html

def test_balancer_is_subset_not_double_counted():
    html=render(reserve=1200)
    assert 'Presupuesto Compras</span><strong>$20,295</strong>' in html
    assert 'Reserva Balancer estimada</span><strong>$1,200</strong>' in html
    assert 'Incluida en Compras; no sumar otra vez' in html
    assert 'Componente Balancer incluido en el presupuesto Compras' in html

def test_zero_cash_no_divide_by_zero():
    html=render(cash=0,trading=0)
    assert 'Presupuesto Compras</span><strong>$0</strong>' in html
