from typing import Type
from types import TracebackType
from sqlite3 import Cursor
from src.db.connection import cursor, transactions


class Transaction:
    '''
    Encapsulate a database transaction.

    The transaction operates on the database connection that is current in the execution context.

    Automatic usage:

    with Transaction():
        # ... perform database operations ...

    Manual usage:

    transaction = Transaction()
    transaction.begin()
    transaction.commit()
    '''

    next_savepoint_id = 1

    def __init__(self) -> None:
        self.cursor = cursor.get()
        self.transactions = transactions.get()
        self.completed = False
        self.savepoint_id = 0

    def __enter__(self) -> Cursor:
        self.begin()
        return self.cursor

    def __exit__(self, exception_type: Type[BaseException] | None, exception_value: BaseException | None, traceback: TracebackType | None):
        '''
        If the transaction has not been manually completed then commit it, or roll it back if there was an exception.
        '''

        if not self.completed:
            if exception_type is not None:
                self.roll_back()
            else:
                self.commit()

    def begin(self) -> None:
        '''
        Start the transaction.
        '''

        # If this is the first transaction on the connection then begin a transaction, else make a savepoint.
        if len(self.transactions) == 0:
            self.cursor.execute('BEGIN TRANSACTION')
        else:
            self.cursor.execute('SAVEPOINT :id', {'id': Transaction.next_savepoint_id})

        # Add the savepoint ID to the stack.
        self.savepoint_id = Transaction.next_savepoint_id
        self.transactions.append(self.savepoint_id)
        Transaction.next_savepoint_id += 1

    def commit(self):
        '''
        Commit any changes made to the database.

        Any uncommitted database changes will be saved.

        This will raise RuntimeError if the transaction has already been rolled back or committed.
        '''

        if self.completed:
            raise RuntimeError('Transaction already completed')

        if len(self.transactions) == 0:
            raise RuntimeError('Transaction stack is empty')

        if self.transactions.pop() != self.savepoint_id:
            raise RuntimeError('Transactions improperly nested')

        if len(self.transactions) == 0:
            self.cursor.execute('COMMIT TRANSACTION')
        else:
            self.cursor.execute('RELEASE SAVEPOINT :id', {'id': self.savepoint_id})

        self.completed = True

    def roll_back(self):
        '''
        Roll back any changes made to the database.

        Any uncommitted database changes will be undone.

        This will raise RuntimeError if the transaction has already been rolled back or committed.
        '''

        if self.completed:
            raise RuntimeError('Transaction already completed')

        if len(self.transactions) == 0:
            raise RuntimeError('Transaction stack is empty')

        if self.transactions.pop() != self.savepoint_id:
            raise RuntimeError('Transactions improperly nested')

        if len(self.transactions) == 0:
            self.cursor.execute('ROLLBACK TRANSACTION')
        else:
            self.cursor.execute('ROLLBACK TO SAVEPOINT :id', {'id': self.savepoint_id})

        self.completed = True
