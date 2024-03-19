import glob
import logging
import sqlite3
from hashlib import sha256
from typing import List
from src.db.connection import cursor, transactions
from src.db.transaction import Transaction
from contextvars import copy_context
from inspect import iscoroutinefunction

LOGGER = logging.getLogger('ai')


def connect(filename='ai.db'):
    '''
    Function decorator to run a function in a new execution context with its own database connection.
    The decorated function will therefore be unaffected by transactions created by other execution contexts.

    Usage:

    @connect()
    def my_func():
        # This will have its own connection to the database.
    '''

    # The connect() function is a decorator factory, not a decorator, so it must be written as:
    # @connect() and not @connect.
    if callable(filename):
        raise Exception('Use @connect(), not @connect')

    def decorator(func):
        '''
        This function is called before the decorated function.

        It will return a new function that runs the decorated function in a new execution context.
        '''

        if (iscoroutinefunction(func)):
            async def run_with_connection(*args, **kwargs):
                '''
                Open a connection to the databse and then run func().
                '''

                # Open a new connection to the database.
                with sqlite3.connect(filename) as connection:
                    # Fetch the connection's cursor.
                    db_cursor = connection.cursor()

                    # Set up the execution context's cursor and transaction stack.
                    cursor.set(db_cursor)
                    transactions.set([])

                    # Open a new transaction and run the decorated code.
                    with Transaction():
                        return await func(*args, **kwargs)

            # Return a function that runs in the new context.
            async def runner(*args, **kwargs):
                # Create a new execution context.
                execution_context = copy_context()

                # Run the decorated function within the new execution context.
                return await execution_context.run(run_with_connection, *args, **kwargs)

            return runner

        else:

            def run_with_connection(*args, **kwargs):
                '''
                Open a connection to the databse and then run func().
                '''

                # Open a new connection to the database.
                with sqlite3.connect(filename) as connection:
                    # Fetch the connection's cursor.
                    db_cursor = connection.cursor()

                    # Set up the execution context's cursor and transaction stack.
                    cursor.set(db_cursor)
                    transactions.set([])

                    # Open a new transaction and run the decorated code.
                    with Transaction():
                        return func(*args, **kwargs)

            # Return a function that runs in the new context.
            def runner(*args, **kwargs):
                # Create a new execution context.
                execution_context = copy_context()

                # Run the decorated function within the new execution context.
                return execution_context.run(run_with_connection, *args, **kwargs)

            return runner

    return decorator


def dictionary_row_factory(cursor: sqlite3.Cursor, row):
    '''
    Convert a row from a tuple into a dictionary keyed by column name.
    '''

    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d


def prepare():
    '''
    Creates the DB and initializes it by executing the migration scripts if necessary.
    '''
    c = cursor.get()

    c.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='schema_version'")

    if c.fetchone() is None:
        with open("res/db/init/CREATE_SCHEMA_VERSION.sql") as create_schema_version:
            c.executescript(create_schema_version.read())

    c.execute("SELECT * from schema_version")
    LOGGER.info(f'DB schema before migration {c.fetchall()}')

    for script_file in sorted(glob.glob("res/db/migrate/*.sql")):
        with open(script_file) as script:
            script_hash = sha256(script.read().encode()).hexdigest()
            c.execute("SELECT hash FROM schema_version WHERE version=:script_file", {
                "script_file": script_file})
            saved_hash = c.fetchone()
            if saved_hash is None:
                script.seek(0)
                c.executescript(script.read())
                c.execute("INSERT INTO schema_version values (:file, :hashed)",
                          {'file': script_file, 'hashed': script_hash})
                continue

            if script_hash != saved_hash[0]:
                raise Exception(
                    f"Bad migration. For script {script_file} expected has {saved_hash[0]} but got {script_hash}")

    c.execute("SELECT * from schema_version")
    LOGGER.info(f'DB schema after migration {c.fetchall()}')


def change(query: str, params=()):
    '''
    Executes a given query.
    '''

    c = cursor.get()
    c.execute(query, params)


def fetchall(query: str, params=()) -> dict:
    '''
    Executes a given query and retrieves the result. Does not change data.
    '''

    c = cursor.get()
    c.row_factory = dictionary_row_factory
    c.execute(query, params)
    return c.fetchall()


def fetchone(query: str, params=()) -> dict | None:
    '''
    Executes a given query and retrieves a single result. Does not change data.
    Returns None if there is no row to fetch.
    '''

    c = cursor.get()
    c.row_factory = dictionary_row_factory
    c.execute(query, params)
    return c.fetchone()


def fetchcolumn(query: str, params=()) -> List[str]:
    '''
    Executes a given query and retrives a single column from all rows. Does not change data.
    '''

    c = cursor.get()
    c.row_factory = lambda cursor, row: row[0]
    c.execute(query, params)
    return c.fetchall()
