import unittest

from alerts import alert_is_triggered


class TestAlertMatch(unittest.TestCase):
    def test_below_triggers(self) -> None:
        self.assertTrue(
            alert_is_triggered('below', 91.0, 90.5)
        )
        self.assertFalse(
            alert_is_triggered('below', 91.0, 91.5)
        )

    def test_above_triggers(self) -> None:
        self.assertTrue(
            alert_is_triggered('above', 93.0, 93.2)
        )
        self.assertFalse(
            alert_is_triggered('above', 93.0, 92.8)
        )


if __name__ == '__main__':
    unittest.main()
