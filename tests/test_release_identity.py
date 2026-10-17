import ast
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def test_web_product_version_is_independent_of_sheets_schema():
 text=(ROOT/"app.py").read_text()
 sheet=(ROOT/"google_sheets_master.py").read_text()
 assert 'APP_VERSION = "1.1.0-rc1"' in text
 assert "'version':APP_VERSION" in text
 assert "ctrl.get('schema_version')!='5.0.0'" in sheet
 assert (ROOT/'templates/base.html').read_text().count('KairosWeb') >= 1

def test_unsafe_snapshot_fallback_is_absent():
 text=(ROOT/'app.py').read_text()
 assert 'snapshot_master_2026' not in text
 assert 'config.json' not in text
