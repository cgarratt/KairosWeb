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
