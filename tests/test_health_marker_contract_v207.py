"""Verify every /health build marker against the shipped asset bytes."""
import ast
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]

def test_release_health_markers_match_actual_assets():
    tree=ast.parse((ROOT/'app.py').read_text(encoding='utf-8'))
    func=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='_deployed_asset_status')
    block=next(n for n in func.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='critical' for t in n.targets))
    files=ast.literal_eval(block.value)
    for category,(relpath,markers) in files.items():
        source=(ROOT/relpath).read_text(encoding='utf-8')
        for marker in markers:
            assert marker in source, f'{category}: {relpath} is missing {marker!r}'


def test_deep_health_module_dependencies_do_not_claim_end_to_end():
    import copy
    source=ast.parse((ROOT/'app.py').read_text())
    func=copy.deepcopy(next(n for n in source.body if isinstance(n,ast.FunctionDef) and n.name=='_module_dependency_states'))
    func.decorator_list=[]
    ns={}
    exec(compile(ast.fix_missing_locations(ast.Module(body=[func],type_ignores=[])), '<extracted>', 'exec'),ns)
    states=ns['_module_dependency_states']({'sheets':{'status':'OK'},'binance':{'status':'OK'},'hyperliquid':{'status':'DATA_ERROR'}})
    assert states['portafolio']['status']=='DEPENDENCIES_OK'
    assert states['balancer']['status']=='DEPENDENCIES_OK'
    assert states['forecast']['status']=='BLOCKED_OR_PARTIAL'
    assert states['compras']['status']=='BLOCKED_OR_PARTIAL'
    assert all(m['scope']=='DEPENDENCY_READINESS_ONLY_NOT_END_TO_END' for m in states.values())


def test_authenticated_deep_health_probes_three_provider_categories():
    script=(ROOT/'app.py').read_text()
    assert "@app.route('/api/health/diagnostics')" in script
    assert "'/api/health/diagnostics'" in script  # sheet-binding exemption, not Basic-auth exemption
    assert 'ThreadPoolExecutor(max_workers=3)' in script
    assert "('sheets','binance','hyperliquid')" in script
    assert 'get_state(force=True)' in script
    assert "'server':{'status':'UP'" in script
    assert 'DEPENDENCY_READINESS_ONLY_NOT_END_TO_END' in script
    assert 'call_mcp(env,tool,{})' in script


def test_portfolio_diagnostic_template_has_no_raw_exception():
    template=(ROOT/'templates/portfolio_integral.html').read_text()
    assert 'id="portfolio-diagnostic"' in template
    assert 'portfolio_diagnostic.origin' in template
    assert 'portfolio_diagnostic.error_id' in template
    assert 'portfolio_diagnostic.last_valid_spot_utc' in template
    assert 'Distribución actual del capital' in template
    assert "capital_distribution['items']" in template
    assert 'HISTÓRICO NO SPOT' not in template
    assert 'homologation.status' in template
