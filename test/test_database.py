from unittest import IsolatedAsyncioTestCase
from src.db.database import change, connect, dictionary_row_factory, fetchall, fetchcolumn, fetchone, prepare
from pathlib import Path
from unittest.mock import Mock
import asyncio


class TestDatabase(IsolatedAsyncioTestCase):

    @classmethod
    def setUpClass(cls):
        asyncio.run(TestDatabase.setUpDatabase())

    @connect()
    async def setUpDatabase():
        '''
        Initialize the database schema in "test.db" before running the tests.
        '''

        prepare()

        # Insert some test data.
        drones = [
            {'id': 11, 'drone_id': 1111},
            {'id': 22, 'drone_id': 2222},
        ]

        [await change('INSERT INTO drone(id, drone_id) VALUES (:id, :drone_id)', drone) for drone in drones]

    @classmethod
    def tearDownClass(cls):
        '''
        Delete the "test.db" file after all the tests have run.
        '''

        Path.unlink('test.db')

    @connect()
    async def test_prepare_check(self):
        '''
        Ensure that preparing fails if a hash is incorrect.
        '''

        # Corrupt a migration hash.
        await change('UPDATE schema_version SET hash=1 WHERE version="res/db/migrate/0005_CONFIG_TIMER.sql"', {})

        # Ensure an exception is raised.
        self.assertRaises(Exception, prepare)

    @connect()
    async def test_fetchcolumn(self):
        '''
        Test the operation of fetchcolumn.
        '''

        # Fetch a single column and return it as a list.
        rows = await fetchcolumn('SELECT drone_id FROM drone')
        self.assertEqual(['1111', '2222'], rows)

        # If more than one column is specified, only the first one must be returned.
        rows = await fetchcolumn('SELECT id, drone_id FROM drone')
        self.assertEqual([11, 22], rows)

    @connect()
    async def test_fetchone(self):
        '''
        Test the operation of fetchcolumn.
        '''

        # Fetch a single row.
        row = await fetchone('SELECT id, drone_id FROM drone WHERE id = 11', {})
        self.assertEqual({'id': 11, 'drone_id': '1111'}, row)

        # Return None if there is no such row.
        row = await fetchone('SELECT id, drone_id FROM drone WHERE id = 0', {})
        self.assertEqual(None, row)

    @connect()
    async def test_fetchall(self):
        '''
        Test the operation of fetchcolumn.
        '''

        # Fetch all rows.
        rows = await fetchall('SELECT id, drone_id FROM drone', {})
        self.assertEqual([{'id': 11, 'drone_id': '1111'}, {'id': 22, 'drone_id': '2222'}], rows)

        # Return an empty list if no rows matched.
        rows = await fetchall('SELECT id, drone_id FROM drone WHERE id = 0', {})
        self.assertEqual([], rows)

    @connect()
    async def test_change(self):
        '''
        Test updating the database.
        '''

        # Insert a new row.
        await change('INSERT INTO drone (id, drone_id) VALUES (33, "3333")', {})
        row = await fetchone('SELECT id, drone_id FROM drone WHERE id = 33', {})
        self.assertEqual({'id': 33, 'drone_id': '3333'}, row)

        # Update the row.
        await change('UPDATE drone SET drone_id = "3334" WHERE id = 33', {})
        row = await fetchone('SELECT id, drone_id FROM drone WHERE id = 33', {})
        self.assertEqual({'id': 33, 'drone_id': '3334'}, row)

        # Delete the row.
        await change('DELETE FROM drone WHERE id = 33', {})
        row = await fetchone('SELECT id, drone_id FROM drone WHERE id = 33', {})
        self.assertEqual(None, row)

    def test_dictionary_row_factory(self):
        '''
        Ensure that dictionary_row_factory() keys rows by column name.
        '''

        cursor = Mock()
        cursor.description = [('id', None), ('drone_id', None)]
        row = (11, '1111')
        newRow = dictionary_row_factory(cursor, row)
        self.assertEqual({'id': 11, 'drone_id': '1111'}, newRow)
