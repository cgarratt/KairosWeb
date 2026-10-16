from pathlib import Path
import unittest

class ModeTemplateRegression(unittest.TestCase):
    def test_chart_mapping_access(self):
        text=(Path(__file__).resolve().parents[1]/"templates"/"mode.html").read_text()
        self.assertIn("chart['items']", text)
        self.assertIn("chart['max']", text)
        self.assertNotIn('chart.items', text)
        self.assertNotIn('chart.max', text)

if __name__=='__main__': unittest.main()
