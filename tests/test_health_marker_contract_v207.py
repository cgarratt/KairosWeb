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
