"""Proportional deficit allocation constrained by settled USDT per venue.
Pure simulation: no transfers, exchange orders, or Master writes.
"""
from math import isfinite

TOKEN_VENUES = {'BTC':'Binance','ETH':'Binance','SOL':'Binance','LINK':'Binance',
 'HBAR':'Binance','ONDO':'Binance','SUI':'KuCoin','PUMP':'KuCoin','PUMPFUN':'KuCoin',
 'PLUME':'KuCoin','VIRTUAL':'KuCoin','PEPE':'KuCoin','HYPE':'Hyperliquid'}

def amount(value):
    if isinstance(value,bool):raise ValueError('Invalid venue cash/deficit')
    x=float(value)
    if not isfinite(x) or x<0:raise ValueError('Invalid venue cash/deficit')
    return x

def free_venue_cash(physical, *, protected=None, commitments=None, quarantined=()):
    """Inputs are disjoint: protected does not include reserved BUY again.
    Unknown location of protected cash must be resolved by caller, never guessed.
    Quarantined venues are zeroed, not subtracted twice from the global budget.
    """
    if not isinstance(physical,dict):raise ValueError('Venue cash required')
    protected=protected or {};commitments=commitments or {}
    for mapping in (physical,protected,commitments):
        if not isinstance(mapping,dict):raise ValueError('Venue amounts required')
        for value in mapping.values():amount(value)
    if any(v not in physical and amount(x)>0 for m in (protected,commitments) for v,x in m.items()):
        raise ValueError('Protected/committed cash has no physical venue')
    result={}
    for venue,value in physical.items():
        free=amount(value)-amount(protected.get(venue,0))-amount(commitments.get(venue,0))
        if free < -1e-7:raise ValueError('Venue overcommitted: '+venue)
        result[venue]=0. if venue in quarantined else max(0.,free)
    return result

def proportional_by_venue(gaps, venues, cash, budget):
    """Allocate simultaneously by deficit, with per-token and venue ceilings.
    When one venue binds, redistribute only to remaining funded deficits.
    No ranking by drift; invariant to input ordering. Missing venue gets zero.
    """
    gaps=[amount(x) for x in gaps];budget=amount(budget)
    if len(gaps)!=len(venues):raise ValueError('Venue/token mismatch')
    if not isinstance(cash,dict):raise ValueError('Venue free cash required')
    free={v:amount(x) for v,x in cash.items()};alloc=[0.]*len(gaps)
    for _ in range(len(gaps)+len(free)+2):
        remaining=max(0.,budget-sum(alloc))
        room=[max(0.,gaps[i]-alloc[i]) if free.get(v,0)>1e-10 else 0. for i,v in enumerate(venues)]
        total=sum(room)
        if remaining<=1e-10 or total<=1e-10:break
        take=min(remaining,total);proposals=[take*x/total for x in room]
        demand={v:sum(proposals[i] for i,w in enumerate(venues) if w==v) for v in set(venues)}
        delta=[p*min(1.,free.get(venues[i],0)/demand[venues[i]]) if demand[venues[i]]>0 else 0. for i,p in enumerate(proposals)]
        if sum(delta)<=1e-10:break
        for i,x in enumerate(delta):alloc[i]+=x
        for v in free:free[v]=max(0.,free[v]-sum(delta[i] for i,w in enumerate(venues) if w==v))
    return alloc,free


def cash_from_snapshot(snapshot):
    physical=snapshot.get('liquidity_venues_USDT')
    qf=amount(snapshot['trading_real_fixed_USDT'])
    protected={'Quantfury':qf} if qf else {}
    quarantined={x['venue'] for x in snapshot.get('foreign_quote_pending',[])}
    return free_venue_cash(physical,protected=protected,
        commitments=snapshot.get('reserved_buy_usdt_by_venue',{}),quarantined=quarantined)


def funding_venue(token, venue):
    # Published cash is USDT; Hyperliquid Spot HYPE settles in USDC.
    # Conversion/transfer needs separately verified inputs, not a 1:1 assumption.
    return None if token=='HYPE' and venue=='Hyperliquid' else venue
