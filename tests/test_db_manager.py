import unittest
import os
from db_manager import get_db_connection, save_new_user_data_in_db, db_init
from unittest.mock import patch, MagicMock


class TestDBConnection(unittest.TestCase):

    def test_connection_faile(self):
        """Test that connection fails with wrond credentials"""
        # Backup real env vars
        real_user = os.environ.get('DB_USER')
        real_pass = os.environ.get('DB_PASSWORD')

        # Set bad credentials
        os.environ['DB_USER'] = 'invalid_user'
        os.environ['DB_PASSWORD'] = 'invalid_pass'

        conn = get_db_connection()
        self.assertIsNone(conn)

        # Restore original credentials
        if real_user:
            os.environ['DB_USER'] = real_user
        if real_pass:
            os.environ['DB_PASSWORD'] = real_pass


class TestSaveUser(unittest.TestCase):
    @patch('db_manager.get_db_connection')
    def test_save_new_user(self, mock_get_conn):
        # Setup mocks
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_conn.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        # Cursor will simulate "no user found"
        mock_cursor.fetchone.return_value = None

        # Fake user object
        user = MagicMock()
        user.id = 123
        user.first_name = "John"
        user.last_name = "Doe"
        user.username = "johndoe"
        user.language_code = "en"
        user.is_bot = False

        # Call function
        save_new_user_data_in_db(user)

        # Check if SELECT and INSERT were called
        mock_cursor.execute.assert_any_call("SELECT 1 FROM users WHERE id = %s", (user.id,))
        self.assertTrue(mock_cursor.execute.call_count >= 2)

        # Check if commit was called
        mock_conn.commit.assert_called_once()

        # Check if connection closed
        mock_conn.close.assert_called_once()


class TestDBInit(unittest.TestCase):
    @patch('db_manager.get_db_connection')
    def test_db_init(self, mock_get_conn):
        #SetUp mocks
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_conn.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        #call the function
        db_init()

        #check if cursor excecuted the CREATE TABLE statement
        mock_cursor.execute.assert_called_once()
        args, kwargs = mock_cursor.execute.call_args
        self.assertIn("CREATE TABLE IF NOT EXISTS users", args[0])
        
        # Check commit and close were called
        mock_conn.commit.assert_called_once()
        mock_conn.close.assert_called_once()


if __name__ == '__main__':
    unittest.main()
