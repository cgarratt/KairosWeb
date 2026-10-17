"""1.2.0 regression: archived MCP candidates vs independently refreshable live candidates."""
import unittest
from pathlib import Path
from pivot_preload import TOKENS, ARCHIVE_A1, archive_candidates, review_result
from pivot_candidates import candidates_binance, candidates_hype

HERE=Path(__file__).resolve().parents[1]


def archive_rows():
    head=['Token','Mercado fuente','CH bruto','Fecha CH UTC','CL bruto','Fecha CL UTC',
          'O1 candidato','Fecha O1 UTC','O2 candidato','Fecha O2 UTC',
          'O3 candidato','Fecha O3 UTC','Fase exploratoria','CL seleccionado manual',
          'Estado','MCP herramienta','Excepción / nota']
    out=[head]
    for t in TOKENS:
        row=[t,f'{t}/USDT',5,'2025-09-15',2,'2026-02-01',3,'2026-06-01',2.5,'2026-08-01',None,None,'O1',None,
             'EXPLORATORY_ONLY','BINANCE MCP','No certificado']
        if t=='HYPE':row[1]='HYPE/USDC';row[10]=97.885;row[11]='2026-09-23';row[16]='O3 sin 5R; candidato'
        if t=='SUI':row[4]=0.5597;row[13]=.6359
        if t=='PUMPFUN':row[4]=.000411;row[13]=.001151
        out.append(row)
    return out


class PivotArchiveReleaseTests(unittest.TestCase):
    def test_archive_has_exact_12_tokens_in_published_order(self):
        result=archive_candidates(archive_rows())
        self.assertEqual([r['token'] for r in result],list(TOKENS))
        self.assertTrue(all(not r['certified'] and r['status']=='CANDIDATO_ARCHIVADO_NO_CERTIFICADO' for r in result))
        self.assertEqual(ARCHIVE_A1,"'07_PIVOTES'!A21:Q33")
    def test_manual_selected_low_rejects_flash_crash(self):
        rows=archive_candidates(archive_rows())
        d={x['token']:x for x in rows}
        self.assertEqual(d['SUI']['cycle_low'],.6359)
        self.assertEqual(d['SUI']['raw_cycle_low'],.5597)
        self.assertIsNone(d['SUI']['cl_date'])
        self.assertEqual(d['PUMPFUN']['cycle_low'],.001151)
        self.assertIsNone(d['PUMPFUN']['cl_date'])
    def test_hype_raw_o3_not_certified(self):
        row={x['token']:x for x in archive_candidates(archive_rows())}['HYPE']
        self.assertEqual(row['o3'],97.885)
        self.assertIn('sin 5R',row['warning'])
        self.assertEqual(row['market'],'HYPE/USDC')
        self.assertFalse(row['certified'])
    def test_missing_archive_row_is_data_error_not_old_json(self):
        rows=archive_rows()[:-1]
        obj=archive_candidates(rows)[-1]
        self.assertEqual(obj['status'],'DATA_ERROR')
        self.assertIsNone(obj.get('cycle_low'))
    def test_wrong_columns_rejected(self):
        with self.assertRaises(ValueError):archive_candidates([['BTC','unknown']])
    def test_bad_price_does_not_materialize(self):
        rows=archive_rows();rows[1][2]='nan'
        self.assertIsNone(archive_candidates(rows)[0]['cycle_high'])
    def test_live_mcp_remains_exploratory(self):
        row=candidates_binance('BTC',{'status':'OK','scope':'EXPLORATORY_ONLY',
            'cycle_high':{'price':'10'},'cycle_low':{'price':'3'},'wave_pivots':{}})
        out=review_result(row)
        self.assertFalse(out['certified'])
        self.assertEqual(out['status'],'CANDIDATO_MCP_NO_CERTIFICADO')
    def test_app_endpoint_one_token_not_large_parallel_fanout(self):
        source=(HERE/'app.py').read_text()
        self.assertIn("token = request.args.get('token'",source)
        self.assertIn("read_ranges({'archive':ARCHIVE_A1})",source)
        self.assertNotIn('ThreadPoolExecutor(max_workers=5)',source)
    def test_frontend_shows_progress_and_preserves_manual_edits(self):
        source=(HERE/'static/settings_master.js').read_text()
        self.assertIn('input.dataset.userEdited',source)
        self.assertIn('input.dataset.userEdited===\'true\'',source)
        self.assertIn('refreshLivePivots',source)
        self.assertIn('const progress=',source)
    def test_two_decimal_investment_does_not_round_unchanged_sheet_cost(self):
        source=(HERE/'static/settings_master.js').read_text()
        self.assertIn("Number(value).toFixed(2)",source)
        self.assertIn('value=Number(entry.investment_total)',source)
    def test_dark_forecast_rows_and_totals(self):
        source=(HERE/'static/theme.css').read_text()
        self.assertIn(':root[data-theme="dark"] .fc-tables :is(tfoot',source)
        self.assertIn(':root[data-theme="dark"] .fc-tables .wave-value-row',source)

if __name__=='__main__':unittest.main()
