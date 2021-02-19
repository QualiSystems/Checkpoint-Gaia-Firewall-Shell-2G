import unittest

from src.driver import CheckPointGaiaFirewallShell2GDriver


class TestCheckPointGaiaFirewallShell2GDriver(unittest.TestCase):
    def setUp(self):
        self._instance = CheckPointGaiaFirewallShell2GDriver()

    def test_init(self):
        self.assertIsNone(self._instance._cli)
