import unittest
from unittest.mock import MagicMock, patch

from db_manager import (
    create_alert,
    delete_alert,
    get_user_prefs,
    increment_field_db,
    set_favorite,
    set_last_lookup,
)


def _mock_conn(fetchone=None, fetchall=None):
    conn = MagicMock()
    cursor = MagicMock()
    conn.cursor.return_value.__enter__.return_value = cursor
    cursor.fetchone.return_value = fetchone
    cursor.fetchall.return_value = fetchall or []
    return conn, cursor


class TestUserPrefs(unittest.TestCase):
    @patch('db_manager.get_db_connection')
    def test_get_user_prefs(self, mock_get) -> None:
        conn, cursor = _mock_conn(
            fetchone=('Moscow', 'USD', 'SPB', 'EUR'),
        )
        mock_get.return_value = conn
        prefs = get_user_prefs(7)
        self.assertEqual(prefs['last_city'], 'Moscow')
        self.assertEqual(prefs['fav_currency'], 'EUR')
        conn.close.assert_called_once()

    @patch('db_manager.get_db_connection')
    def test_set_last_lookup(self, mock_get) -> None:
        conn, cursor = _mock_conn()
        mock_get.return_value = conn
        set_last_lookup(7, 'Moscow', 'USD')
        sql = cursor.execute.call_args[0][0]
        self.assertIn('last_city', sql)
        self.assertIn('last_currency', sql)
        self.assertEqual(
            cursor.execute.call_args[0][1],
            ('Moscow', 'USD', 7),
        )
        conn.commit.assert_called_once()

    @patch('db_manager.get_db_connection')
    def test_set_favorite(self, mock_get) -> None:
        conn, cursor = _mock_conn()
        mock_get.return_value = conn
        set_favorite(7, 'SPB', 'EUR')
        sql = cursor.execute.call_args[0][0]
        self.assertIn('fav_city', sql)
        self.assertEqual(
            cursor.execute.call_args[0][1],
            ('SPB', 'EUR', 7),
        )


class TestAlertsDb(unittest.TestCase):
    @patch('db_manager.get_db_connection')
    def test_create_alert_rejects_bad_kind(self, mock_get) -> None:
        with self.assertRaises(ValueError):
            create_alert(7, 'hack', 'Moscow', 'USD', 'below', 91.0)
        mock_get.assert_not_called()

    @patch('db_manager.count_alerts', return_value=0)
    @patch('db_manager.get_db_connection')
    def test_create_alert_inserts(
        self,
        mock_get,
        _count,
    ) -> None:
        conn, cursor = _mock_conn()
        mock_get.return_value = conn
        created = create_alert(
            7, 'cash_buy', 'Moscow', 'USD', 'below', 91.0,
        )
        self.assertTrue(created)
        sql = cursor.execute.call_args[0][0]
        self.assertIn('INSERT INTO alerts', sql)

    @patch('db_manager.get_db_connection')
    def test_delete_alert_scoped_to_user(self, mock_get) -> None:
        conn, cursor = _mock_conn()
        mock_get.return_value = conn
        delete_alert(7, 3)
        sql, params = cursor.execute.call_args[0]
        self.assertIn('user_id', sql)
        self.assertEqual(params, (3, 7))


class TestIncrementWhitelist(unittest.TestCase):
    @patch('db_manager.get_db_connection')
    def test_unknown_field_is_rejected(self, mock_get) -> None:
        user = MagicMock()
        user.id = 7
        increment_field_db(user, 'is_bot')
        mock_get.assert_not_called()


if __name__ == '__main__':
    unittest.main()
