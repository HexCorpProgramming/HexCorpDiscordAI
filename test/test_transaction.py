from src.db.transaction import Transaction
from unittest import IsolatedAsyncioTestCase
from unittest.mock import call, Mock
from src.db.database import change, cursor, transactions


class TestTransaction(IsolatedAsyncioTestCase):
    def setUp(self):
        '''
        Called before every test.

        Set up a mock database cursor and reset the transaction stack.
        '''

        cursor.set(Mock())
        transactions.set([])
        Transaction.next_savepoint_id = 1

        self.cursor = cursor.get()

    async def test_automatic_commit(self):
        '''
        Ensure that nested transactions are individually committed.
        '''

        with Transaction():
            await change('QUERY 1')

            with Transaction():
                await change('QUERY 2')
                with Transaction():
                    await change('QUERY 3')
                    # Third transaction is auto-committed here.
                # Second transaction is auto-committed here.

            await change('QUERY 4')
            # First transaction is auto-committed here.

        expected_calls = [
            call('BEGIN TRANSACTION'),
            call('QUERY 1', ()),
            call('SAVEPOINT :id', {'id': 2}),
            call('QUERY 2', ()),
            call('SAVEPOINT :id', {'id': 3}),
            call('QUERY 3', ()),
            call('RELEASE SAVEPOINT :id', {'id': 3}),
            call('RELEASE SAVEPOINT :id', {'id': 2}),
            call('QUERY 4', ()),
            call('COMMIT TRANSACTION'),
        ]

        self.cursor.execute.assert_has_calls(expected_calls)

    async def test_inner_rollback(self):
        '''
        Ensure that the inner transaction is rolled back if it throws.
        '''

        with Transaction():
            await change('QUERY 1')

            try:
                with Transaction():
                    await change('QUERY 2')
                    raise RuntimeError()
            except RuntimeError:
                # Inner transaction is rolled back.
                pass

            await change('QUERY 3')
            # Outer transaction is auto-committed here.

        expected_calls = [
            call('BEGIN TRANSACTION'),
            call('QUERY 1', ()),
            call('SAVEPOINT :id', {'id': 2}),
            call('QUERY 2', ()),
            call('ROLLBACK TO SAVEPOINT :id', {'id': 2}),
            call('QUERY 3', ()),
            call('COMMIT TRANSACTION'),
        ]

        self.cursor.execute.assert_has_calls(expected_calls)

    async def test_outer_rollback(self):
        '''
        Ensure that the transaction is rolled back if the outer transaction throws.
        '''

        try:
            with Transaction():
                await change('QUERY 1')

                with Transaction():
                    await change('QUERY 2')
                    # Inner transaction is auto-committed here.

                # Outer transaction fails.
                raise RuntimeError()
        except RuntimeError:
            pass

        expected_calls = [
            call('BEGIN TRANSACTION'),
            call('QUERY 1', ()),
            call('SAVEPOINT :id', {'id': 2}),
            call('QUERY 2', ()),
            call('RELEASE SAVEPOINT :id', {'id': 2}),
            call('ROLLBACK TRANSACTION'),
        ]

        self.cursor.execute.assert_has_calls(expected_calls)
