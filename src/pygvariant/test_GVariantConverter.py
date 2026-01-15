import unittest
from .GVariantConverter import GVariantValueConverter

class TestGVariantValueConverter(unittest.TestCase):
    def setUp(self):
        self.converter = GVariantValueConverter()

    def test_user_provided_string(self):
        user_string = """
        [{'org.gnome.Geary.desktop': <{'position': <0>}>, 'org.gnome.Contacts.desktop': <{'position': <1>}>, 'org.gnome.Weather.desktop': <{'position': <2>}>, 'org.gnome.clocks.desktop': <{'position': <3>}>, 'org.gnome.Maps.desktop': <{'position': <4>}>, 'org.gnome.Music.desktop': <{'position': <5>}>, 'simple-scan.desktop': <{'position': <6>}>, 'org.gnome.Settings.desktop': <{'position': <7>}>, 'org.gnome.Boxes.desktop': <{'position': <8>}>, 'org.gnome.Totem.desktop': <{'position': <9>}>, 'org.gnome.Snapshot.desktop': <{'position': <10>}>, 'org.gnome.Characters.desktop': <{'position': <11>}>, 'Utilities': <{'position': <12>}>, 'System': <{'position': <13>}>, 'org.gnome.Console.desktop': <{'position': <14>}>, 'org.gnome.Tour.desktop': <{'position': <15>}>, 'yelp.desktop': <{'position': <16>}>}]
        """
        parsed = self.converter.parse_value_string(user_string, "aa{sv}")
        self.assertIsInstance(parsed, list)
        self.assertIsInstance(parsed[0], dict)
        self.assertIn('org.gnome.Geary.desktop', parsed[0])
        self.assertEqual(parsed[0]['org.gnome.Geary.desktop'], {'position': 0})


    def test_string_with_variant_markers(self):
        string_with_markers = "['<hello>']"
        parsed = self.converter.parse_value_string(string_with_markers, "as")
        self.assertEqual(parsed, ["<hello>"])

if __name__ == '__main__':
    unittest.main()
