import unittest

from line_number import normalize_line_number, same_line


class LineNumberTests(unittest.TestCase):
    def test_strips_size_prefix_and_quotes(self):
        self.assertEqual(normalize_line_number('12"-ST-30108-B24S-HI'), "ST-30108-B24S-HI")

    def test_plain_size_prefix(self):
        self.assertEqual(normalize_line_number("6-ST-30108-B24S-NI"), "ST-30108-B24S-NI")

    def test_ignores_spaces_and_case(self):
        self.assertEqual(normalize_line_number(" 4 - ch-33807-b52-ni "), "CH-33807-B52-NI")

    def test_same_line(self):
        self.assertTrue(same_line('4"-CH-33807-B52-NI', "4-CH-33807-B52-NI"))

    def test_different_insulation_code_is_different(self):
        # Same sequence number, but HI is not NI (the mismatch seen in the Excel line list).
        self.assertFalse(same_line('12"-ST-30108-B24S-HI', "6-ST-30108-B24S-NI"))


if __name__ == "__main__":
    unittest.main()
