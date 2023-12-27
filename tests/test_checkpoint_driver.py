import unittest

from src.driver import CheckpointShellDriver


class TestCheckPointGaiaFirewallShell2GDriver(unittest.TestCase):
    def setUp(self):
        self._instance = CheckpointShellDriver()

    def test_init(self):
        self.assertIsNone(self._instance._cli)
