from dataclasses import dataclass
from datetime import datetime
from src.db.record import Record
from typing import List
from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock, patch


@dataclass
class RecordTestbed(Record):
    '''
    A record with various data types to be serialized.
    '''

    table = 'test_table'
    id_column = 'a'
    ignore_properties = ['ignored']

    a: int
    b: int | None
    c: str
    d: str | None
    e: datetime
    f: datetime | None
    g: List[int]
    h: List[str]
    i: bool
    j: bool | None

    ignored = 1


class UnsupportedData(Record):
    '''
    An invalid record: The data type is not supported.
    '''

    a: List[bool]


class TestRecord(IsolatedAsyncioTestCase):
    def test_serialize_invalid(self) -> None:
        '''
        Ensure that an exception is thrown when serializing an unsupported data type.
        '''

        with self.assertRaisesRegex(Exception, 'Unknown data type: typing.List\[bool\]'):
            UnsupportedData.serialize({'a': []})

    def test_serialize_invalid_column(self) -> None:
        '''
        Ensure that an exception is thrown when deserializing an unknown column name.
        '''

        with self.assertRaisesRegex(Exception, 'Database column b not found in class UnsupportedData'):
            UnsupportedData.deserialize({'b': []})

    def test_serialize(self) -> None:
        '''
        Ensure that the record's fields can be serialised to strings.
        '''

        timestamp = '2000-01-02 03:04:05'

        data = {
            'a': 1,
            'b': 2,
            'c': 'c',
            'd': 'd',
            'e': datetime.fromisoformat(timestamp),
            'f': datetime.fromisoformat(timestamp),
            'g': [1, 2, 3],
            'h': ['a', 'b', 'c'],
            'i': True,
            'j': True,
            'ignored': 1,
        }

        result = RecordTestbed.serialize(data)

        self.assertEqual(result['a'], '1')
        self.assertEqual(result['b'], '2')
        self.assertEqual(result['c'], 'c')
        self.assertEqual(result['d'], 'd')
        self.assertEqual(result['e'], timestamp)
        self.assertEqual(result['f'], timestamp)
        self.assertEqual(result['g'], '1|2|3')
        self.assertEqual(result['h'], 'a|b|c')
        self.assertTrue(result['i'])
        self.assertTrue(result['j'])

        # Ensure that ignored properties are not serialized.
        self.assertFalse('table' in result)
        self.assertFalse('id_column' in result)
        self.assertFalse('ignore_properties' in result)
        self.assertFalse('ignored' in result)

    def test_serialize_none(self) -> None:
        timestamp = '2000-01-02 03:04:05'

        data = {
            'a': 1,
            'b': None,
            'c': 'c',
            'd': None,
            'e': datetime.fromisoformat(timestamp),
            'f': None,
            'g': [1, 2, 3],
            'h': ['a', 'b', 'c'],
            'i': True,
            'j': None,
        }

        result = RecordTestbed.serialize(data)

        self.assertEqual(result['a'], '1')
        self.assertIsNone(result['b'])
        self.assertEqual(result['c'], 'c')
        self.assertIsNone(result['d'])
        self.assertEqual(result['e'], timestamp)
        self.assertIsNone(result['f'])
        self.assertEqual(result['g'], '1|2|3')
        self.assertEqual(result['h'], 'a|b|c')
        self.assertTrue(result['i'])
        self.assertIsNone(result['j'])

    def test_serialize_empty_list(self) -> None:
        data = {
            'g': [],
            'h': [],
        }

        result = RecordTestbed.serialize(data)

        self.assertEqual(result['g'], '')
        self.assertEqual(result['h'], '')

    def test_deserialize_invalid_type(self) -> None:
        '''
        Ensure that an exception is thrown when deserializing an unsupported data type.
        '''

        with self.assertRaisesRegex(Exception, 'Unknown data type: typing.List\[bool\]'):
            UnsupportedData.deserialize({'a': []})

    def test_deserialize_invalid_column(self) -> None:
        '''
        Ensure that an exception is thrown when deserializing an unknown column name.
        '''

        with self.assertRaisesRegex(Exception, 'Database column b not found in class UnsupportedData'):
            UnsupportedData.deserialize({'b': []})

    def test_deserialize(self) -> None:
        timestamp = '2000-01-02 03:04:05'

        data = {
            'a': '1',
            'b': '2',
            'c': 'c',
            'd': 'd',
            'e': timestamp,
            'f': timestamp,
            'g': '1|2|3',
            'h': 'a|b|c',
            'i': '1',
            'j': '1',
        }

        result = RecordTestbed(**RecordTestbed.deserialize(data))

        self.assertEqual(result.a, 1)
        self.assertEqual(result.b, 2)
        self.assertEqual(result.c, 'c')
        self.assertEqual(result.d, 'd')
        self.assertEqual(result.e, datetime.fromisoformat(timestamp))
        self.assertEqual(result.f, datetime.fromisoformat(timestamp))
        self.assertEqual(result.g, [1, 2, 3])
        self.assertEqual(result.h, ['a', 'b', 'c'])
        self.assertTrue(result.i)
        self.assertTrue(result.j)

    def test_deserialize_none(self) -> None:
        timestamp = '2000-01-02 03:04:05'

        data = {
            'a': '1',
            'b': None,
            'c': 'c',
            'd': None,
            'e': timestamp,
            'f': None,
            'g': '1|2|3',
            'h': 'a|b|c',
            'i': '1',
            'j': None,
        }

        result = RecordTestbed(**RecordTestbed.deserialize(data))

        self.assertEqual(result.a, 1)
        self.assertIsNone(result.b)
        self.assertEqual(result.c, 'c')
        self.assertIsNone(result.d)
        self.assertEqual(result.e, datetime.fromisoformat(timestamp))
        self.assertIsNone(result.f)
        self.assertEqual(result.g, [1, 2, 3])
        self.assertEqual(result.h, ['a', 'b', 'c'])
        self.assertTrue(result.i)
        self.assertIsNone(result.j)

    def test_deserialize_empty_list(self) -> None:
        timestamp = '2000-01-02 03:04:05'

        data = {
            'a': '1',
            'b': None,
            'c': 'c',
            'd': None,
            'e': timestamp,
            'f': None,
            'g': '',
            'h': '',
            'i': '1',
            'j': None,
        }

        result = RecordTestbed(**RecordTestbed.deserialize(data))

        self.assertEqual(result.g, [])
        self.assertEqual(result.h, [])

    @patch('src.db.record.fetchone', new_callable=AsyncMock)
    async def test_load_missing(self, fetchone: AsyncMock) -> None:
        fetchone.return_value = None

        with self.assertRaisesRegex(Exception, 'Failed to find record in test_table where a = 1'):
            await RecordTestbed.load(1)

    @patch('src.db.record.fetchone', new_callable=AsyncMock)
    async def test_find_missing(self, fetchone: AsyncMock) -> None:
        fetchone.return_value = None

        record = await RecordTestbed.find(1)

        self.assertIsNone(record)

    @patch('src.db.record.fetchone', new_callable=AsyncMock)
    async def test_load(self, fetchone: AsyncMock) -> None:
        timestamp = '2000-01-02 03:04:05'

        data = {
            'a': '1',
            'b': None,
            'c': 'c',
            'd': None,
            'e': timestamp,
            'f': None,
            'g': '1|2|3',
            'h': 'a|b|c',
            'i': '1',
            'j': None,
        }

        fetchone.return_value = data

        record = await RecordTestbed.load(1)

        self.assertEqual(record.a, 1)
        self.assertEqual(record.g, [1, 2, 3])

    @patch('src.db.record.change', new_callable=AsyncMock)
    async def test_delete(self, change: AsyncMock) -> None:
        timestamp = '2000-01-02 03:04:05'

        data = {
            'a': '1',
            'b': None,
            'c': 'c',
            'd': None,
            'e': timestamp,
            'f': None,
            'g': '1|2|3',
            'h': 'a|b|c',
            'i': '1',
            'j': None,
        }

        record = RecordTestbed(**data)

        await record.delete()

        change.assert_called_once_with('DELETE FROM test_table WHERE a = :id', {'id': '1'})
