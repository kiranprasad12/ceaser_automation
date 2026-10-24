import unittest

from check_env import missing_packages


class CheckEnvTests(unittest.TestCase):
    def test_nothing_missing_for_standard_library(self):
        self.assertEqual(missing_packages({"json": "json", "os": "os"}), [])

    def test_reports_pip_name_of_missing_module(self):
        result = missing_packages({"not_a_real_module_xyz": "some-pip-name", "json": "json"})
        self.assertEqual(result, ["some-pip-name"])


if __name__ == "__main__":
    unittest.main()
