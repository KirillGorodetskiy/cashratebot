import unittest
from datetime import datetime, timezone

from jobs import evaluate_alerts


class TestEvaluateAlerts(unittest.TestCase):
    def test_due_below_alert(self) -> None:
        alerts = [{
            'id': 1,
            'user_id': 7,
            'kind': 'cash_buy',
            'city': 'Moscow',
            'currency': 'USD',
            'direction': 'below',
            'threshold': 91.0,
            'last_triggered_at': None,
        }]
        due = evaluate_alerts(alerts, lambda _alert: 90.5)
        self.assertEqual(len(due), 1)
        self.assertEqual(due[0]['id'], 1)
        self.assertIn('90.50', due[0]['text'])

    def test_cooldown_skips(self) -> None:
        alerts = [{
            'id': 2,
            'user_id': 7,
            'kind': 'usdt',
            'city': '',
            'currency': 'USDT',
            'direction': 'above',
            'threshold': 80.0,
            'last_triggered_at': datetime.now(timezone.utc),
        }]
        due = evaluate_alerts(alerts, lambda _alert: 81.0)
        self.assertEqual(due, [])

    def test_missing_rate_skips(self) -> None:
        alerts = [{
            'id': 3,
            'user_id': 7,
            'kind': 'cash_buy',
            'city': 'Moscow',
            'currency': 'USD',
            'direction': 'below',
            'threshold': 91.0,
            'last_triggered_at': None,
        }]
        self.assertEqual(evaluate_alerts(alerts, lambda _a: None), [])


if __name__ == '__main__':
    unittest.main()
