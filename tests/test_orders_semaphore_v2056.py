from orders_inbox import annotate_authorized_coverage

def test_partial_only_when_explicitly_authorized_and_reconciled():
    base={'token':'PLUME','venue':'KuCoin','side':'BUY','stage':'O2C2','usdt':500.}
    manual={'token':'PLUME','venue':'KuCoin','lado':'BUY','estado':'EJECUTADA','conciliacion':'CONCILIADA_EN_05','importe_ejecutado':300.,'observaciones':'Compra MANUAL'}
    assert annotate_authorized_coverage([base.copy()],[manual])[0]['display_status']=='PROPUESTA'
    manual['observaciones']='ASOCIACION_AUTORIZADA:O2C2 por usuario'
    got=annotate_authorized_coverage([base.copy()],[manual])[0]
    assert got['display_status']=='PARCIAL' and got['remaining_usdt']==200.
    manual['conciliacion']='PENDIENTE_CONCILIACION'
    assert annotate_authorized_coverage([base.copy()],[manual])[0]['display_status']=='PROPUESTA'

def test_no_aplica_and_full():
    zero={'token':'PLUME','venue':'KuCoin','side':'BUY','stage':'O2C2','usdt':0.}
    assert annotate_authorized_coverage([zero],[])[0]['display_status']=='NO_APLICA'
    full={'token':'PLUME','venue':'KuCoin','side':'BUY','stage':'O2C2','usdt':300.}
    evidence={'token':'PLUME','venue':'KuCoin','lado':'BUY','estado':'EJECUTADA','conciliacion':'CONCILIADA_EN_05','importe_ejecutado':300.,'observaciones':'ASOCIACION_AUTORIZADA:O2C2'}
    assert annotate_authorized_coverage([full],[evidence])[0]['display_status']=='EJECUTADA'
