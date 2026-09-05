import unittest

from office_info import (
    format_office,
    parse_bank_id,
    parse_bank_info,
)


SAMPLE = {
    'bank': {
        'info': {
            'bank_name': 'Test <Bank>',
            'tel': '+7 495 000-00-00',
            'address': 'Street 1',
            'city_name': 'Moscow',
            'metro': [['Kievskaya', 't1', 1, 1, '200 m']],
        }
    }
}


class TestOfficeInfo(unittest.TestCase):
    def test_parse_bank_id_digits_only(self) -> None:
        self.assertEqual(parse_bank_id('104060'), '104060')
        self.assertIsNone(parse_bank_id(''))
        self.assertIsNone(parse_bank_id('12ab'))
        self.assertIsNone(parse_bank_id('../etc'))

    def test_parse_bank_info_fields(self) -> None:
        info = parse_bank_info(SAMPLE)
        self.assertEqual(info['name'], 'Test <Bank>')
        self.assertEqual(info['phone'], '+7 495 000-00-00')
        self.assertEqual(info['address'], 'Street 1')
        self.assertEqual(info['metro'], 'Kievskaya')
        self.assertEqual(info['city'], 'Moscow')

    def test_format_escapes_html(self) -> None:
        text = format_office(parse_bank_info(SAMPLE), 'en')
        self.assertIn('Test &lt;Bank&gt;', text)
        self.assertNotIn('<Bank>', text)
        self.assertIn('Street 1', text)
        self.assertIn('Kievskaya', text)


if __name__ == '__main__':
    unittest.main()
