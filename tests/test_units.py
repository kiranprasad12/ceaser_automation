import unittest

from units import FULL_VACUUM_KPA, pressure_to_kpa, temperature_to_c


class PressureTests(unittest.TestCase):
    def test_bar(self):
        self.assertAlmostEqual(pressure_to_kpa(10, "bar"), 1000.0)

    def test_kgcm2(self):
        self.assertAlmostEqual(pressure_to_kpa(1, "kgcm2"), 98.0665)

    def test_unit_is_case_insensitive(self):
        self.assertAlmostEqual(pressure_to_kpa(2, " MPa "), 2000.0)

    def test_unknown_unit(self):
        with self.assertRaises(ValueError):
            pressure_to_kpa(1, "atm")

    def test_full_vacuum_constant(self):
        self.assertAlmostEqual(FULL_VACUUM_KPA, -101.325)


class TemperatureTests(unittest.TestCase):
    def test_celsius_unchanged(self):
        self.assertEqual(temperature_to_c(150, "C"), 150.0)

    def test_fahrenheit(self):
        self.assertAlmostEqual(temperature_to_c(212, "F"), 100.0)

    def test_unknown_unit(self):
        with self.assertRaises(ValueError):
            temperature_to_c(10, "K")


if __name__ == "__main__":
    unittest.main()
