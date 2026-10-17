"""Acceptance checks for v1.7.0: presentation-only upgrades, no financial mutation."""
from pathlib import Path
from html.parser import HTMLParser
import re
from unittest.mock import patch
from kairos_sheets_features import settings_data
from test_sheets_features import demo_master

ROOT=Path(__file__).resolve().parents[1]

class FiboHeadings(HTMLParser):
    def __init__(self):
        super().__init__()
        self.inside=False
        self.headings=[]
        self.attrs=[]
        self.depth=0
    def handle_starttag(self,tag,attrs):
        if tag=='thead' and not self.inside:
            self.inside=True
        elif self.inside and tag=='th':
            self.depth+=1
            self.attrs.append(dict(attrs))
            self.headings.append('')
    def handle_data(self,data):
        if self.inside and self.depth:
            self.headings[-1]+=data
    def handle_endtag(self,tag):
        if tag=='th' and self.depth:
            self.depth-=1
        elif tag=='thead':
            self.inside=False

def test_forecast_header_short_but_canonical_tooltips_preserved():
    html=(ROOT/'templates/forecast.html').read_text()
    segment=re.search(r'<h2>Asignación USDT para referencias Fibonacci O2</h2>.*?(?=</section>)',html,re.S).group()
    parser=FiboHeadings();parser.feed(segment)
    assert parser.headings==['Token','Precio 38.2%','USDT','Precio 50%','USDT','Precio 61.8%','USDT','Precio 78.6%','USDT','Total USDT']
    assert [x.get('title') for x in parser.attrs[1:]]==[
      'O2C1 · Fib 38.2%','O2C1 · USDT','O2C2 · Fib 50%','O2C2 · USDT',
      'O2C3 · Fib 61.8%','O2C3 · USDT','O2C4 · Fib 78.6%','O2C4 · USDT',
      'Total compras O2 · USDT']

def test_settings_visual_order_uses_original_parameter_index_for_saving():
    js=(ROOT/'static/settings_master.js').read_text()
    assert "O2:['382','500','618','786']" in js
    assert "O4:['382','500','618','786']" in js
    assert "O3:['1618','2618','3618','4618']" in js
    assert "O5:['1618','2618','3618','4618']" in js
    assert 'renderOrder=rows.map((entry,index)=>({entry,index}))' in js
    assert 'for(const {entry,index} of renderOrder)' in js
    assert 'input.dataset.index=String(index)' in js
    with patch('kairos_sheets_features._remote_data',return_value=demo_master()):
        state=settings_data()
    assert len([r for r in state['sections']['parameters'] if r['key'].startswith('FORECAST_O2_FIB_')])==4

def test_forecast_edit_has_no_network_write_code():
    html=(ROOT/'templates/forecast.html').read_text()
    scripts='\n'.join((ROOT/'static'/p).read_text() for p in ['forecast_fibo_plan.js','forecast_segments.js'])
    assert 'fetch(' not in html and 'fetch(' not in scripts
    assert '/api/settings/save' not in html+scripts
    assert "addEventListener('input'" in html
    assert 'simulación independiente de Google Sheets' in html
    assert 'Simulación local; no modifica el Master.' in html
