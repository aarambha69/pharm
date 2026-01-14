from DesignerCore.renderer import TemplateRenderer
import unittest

class TestRendererBinding(unittest.TestCase):
    def setUp(self):
        self.renderer = TemplateRenderer()

    def test_oda_formatting_present(self):
        context = {"oda_number": "5"}
        # Case 1: {{oda_number}}
        res = self.renderer._resolve_binding("Ward: {{oda_number}}", context)
        self.assertEqual(res, "Ward: Ward No. 5 (Oda)")
        
        # Case 2: {{client.oda_number}}
        res2 = self.renderer._resolve_binding("{{client.oda_number}}", context)
        self.assertEqual(res2, "Ward No. 5 (Oda)")

    def test_oda_formatting_missing(self):
        context = {"oda_number": ""} # Empty string
        res = self.renderer._resolve_binding("{{oda_number}}", context)
        self.assertEqual(res, "") # Should be blank

        context2 = {} # Key missing
        res2 = self.renderer._resolve_binding("{{client.oda_number}}", context2)
        self.assertEqual(res2, "")

    def test_general_binding(self):
        context = {"pharmacy_name": "My Pharma", "address": "KTM"}
        res = self.renderer._resolve_binding("{{pharmacy_name}} - {{address}}", context)
        self.assertEqual(res, "My Pharma - KTM")
        
        # Test client mapping
        res2 = self.renderer._resolve_binding("{{client.pharmacy_name}}", context)
        self.assertEqual(res2, "My Pharma")

if __name__ == '__main__':
    unittest.main()
