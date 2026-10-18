"""Regression: MCP must not change already VALIDADO or CONFIRMADO pivots."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def test_mcp_only_updates_proposed():
    script = (ROOT / 'static/settings_master.js').read_text(encoding='utf-8')
    assert "if(field==='cycle_low'&&current.cl_status!=='PROPUESTO')continue" in script
    assert "if(field!=='cycle_low'&&current[field+'_status']!=='PROPUESTO')continue" in script
    assert "if(field==='cl_date'&&current.cl_status!=='PROPUESTO')continue" in script
    assert "if(field!=='cl_date'&&current[field.replace('_date','')+'_status']!=='PROPUESTO')continue" in script
    assert "if(rec[field]!=='PROPUESTO')continue" in script
    assert "if(statusInput?.value!=='PROPUESTO')continue" in script
    assert "select.value!=='PROPUESTO'" in script
    assert "select.value='PROPUESTO'" in script  # only for a previous PROPUESTO
    assert "El MCP nunca reemplaza ni degrada un VALIDADO o CONFIRMADO" in script


def test_backend_retains_confirmed_and_needs_admin_evidence_for_validated():
    script = (ROOT / 'kairos_sheets_features.py').read_text(encoding='utf-8')
    assert "pivote CONFIRMADO inmutable" in script
    assert "requiere revisión MCP semanal 5L/5R+BOS válida" in script
    assert "necesita evidencia MCP semanal firmada para VALIDADO" in script
