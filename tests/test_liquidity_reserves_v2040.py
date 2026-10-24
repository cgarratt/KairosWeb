"""Financial contract; exclusively synthetic test values, not user balances."""
import pytest
from liquidity_reserves import calculate_budgets, allocation_from_master, LiquidityPolicyError

def test_no_certified_balancer_assignment_is_zero_buy():
    x=calculate_budgets(1000,200)
    assert x['balancer_max']==0 and x['compras_max']==800
    assert x['status']=='PENDIENTE_ASIGNACION'

def test_shared_liquidity_no_double_counting():
    x=calculate_budgets(1000,200,balancer_allocated=160)
    assert x['weekly_uncommitted']==640
    assert x['balancer_uncommitted']==160
    assert x['compras_max']==800
    assert x['weekly_uncommitted']+x['balancer_uncommitted']+x['qf_protected']==1000

def test_weekly_consumption_may_extend_into_balancer():
    x=calculate_budgets(1000,200,balancer_allocated=160)
    spend=700
    weekly_spend=min(spend,x['weekly_uncommitted'])
    bal_spend=spend-weekly_spend
    assert (weekly_spend,bal_spend)==(640,60)
    assert spend<=x['compras_max']

def test_spot_sales_not_credited_until_real_fill():
    x=calculate_budgets(1000,200,balancer_allocated=160,conditional_sell_proceeds=300)
    assert x['balancer_max']==160
    assert x['balancer_with_sales_conditional']==460
    assert x['usdt_physical']==1000

def test_contract_fail_closed():
    with pytest.raises(LiquidityPolicyError):calculate_budgets(100,101)
    with pytest.raises(LiquidityPolicyError):calculate_budgets(100,10,balancer_allocated=91)
    with pytest.raises(LiquidityPolicyError):calculate_budgets(100,10,buy_commitments=91)

def test_only_approved_explicit_assignment():
    assert allocation_from_master({}) is None
    assert allocation_from_master({'BALANCER_RESERVE_ASSIGNED_USDT':{'value':500,'status':'PENDIENTE'}}) is None
    assert allocation_from_master({'BALANCER_RESERVE_ASSIGNED_USDT':{'value':300,'status':'APROBADO'}})==300

# v2.0.41: percentage of physical USDT is the canonical dynamic envelope.
def _approved_split(balancer=.2):
    return {
        'PORTFOLIO_LIQ_USDT_FRACTION':{'status':'APROBADO','value':.8-balancer},
        'PORTFOLIO_LIQ_BALANCER_FRACTION':{'status':'APROBADO','value':balancer},
        'PORTFOLIO_LIQ_TRADING_FRACTION':{'status':'APROBADO','value':.2},
        'BALANCER_RESERVE_ASSIGNED_USDT':{'status':'PENDIENTE_ASIGNACION','value':0},
    }

def test_dynamic_assignment_uses_total_physical_cash_and_not_nonqf():
    p=_approved_split()
    assert allocation_from_master(p,22795.,4225.)==4559.
    assert allocation_from_master(p,1000.,200.)==200.
    assert allocation_from_master(p,1200.,200.)==240.
    b=calculate_budgets(22795.,4225.,balancer_allocated=allocation_from_master(p,22795.,4225.))
    assert b['balancer_max']==4559.
    assert b['weekly_uncommitted']==14011.
    assert b['compras_max']==18570.
    assert b['balancer_max']+b['weekly_uncommitted']+b['qf_protected']==22795.

def test_derivation_blocks_any_qf_invasion_and_bad_split():
    p=_approved_split(balancer=.9)
    p['PORTFOLIO_LIQ_USDT_FRACTION']['value']=0.0
    p['PORTFOLIO_LIQ_TRADING_FRACTION']['value']=0.1
    with pytest.raises(LiquidityPolicyError,match='invade QF'):
        allocation_from_master(p,1000.,200.)
    p=_approved_split();p['PORTFOLIO_LIQ_BALANCER_FRACTION']['status']='PENDIENTE'
    assert allocation_from_master(p,1000.,200.) is None
    p=_approved_split();p['PORTFOLIO_LIQ_USDT_FRACTION']['value']=.72
    with pytest.raises(LiquidityPolicyError,match='100%'):
        allocation_from_master(p,1000.,200.)

def test_auto_assignment_ui_and_dark_theme_contract():
    from pathlib import Path
    root=Path(__file__).resolve().parents[1]
    js=(root/'static/settings_master.js').read_text()
    css=(root/'static/theme.css').read_text()
    assert 'balancer-derived-amount' in js
    assert 'usdt_physical_actual' in js
    assert 'data-goal-cash' not in js
    for selector in ('[data-theme="dark"] .goal-card','[data-theme="dark"] .goal-preview','[data-theme="dark"] .goal-field input'):
        assert selector in css
