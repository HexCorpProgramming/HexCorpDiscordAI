import glob
import logging
import sqlite3
from hashlib import sha256
from typing import List

LOGGER = logging.getLogger('ai')

DB_FILE = 'ai.db'


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
    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()

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
        conn.commit()


def change(query: str, params):
    '''
    Executes a given query and commits changes.
    '''
    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        c.execute(query, params)
        conn.commit()


def fetchall(query: str, params) -> dict:
    '''
    Executes a given query and retrieves the result. Does not change data.
    '''
    with sqlite3.connect(DB_FILE) as conn:
        conn.row_factory = dictionary_row_factory
        c = conn.cursor()
        c.execute(query, params)
        return c.fetchall()


def fetchone(query: str, params) -> dict | None:
    '''
    Executes a given query and retrieves a single result. Does not change data.
    Returns None if there is no row to fetch.
    '''
    with sqlite3.connect(DB_FILE) as conn:
        conn.row_factory = dictionary_row_factory
        c = conn.cursor()
        c.execute(query, params)
        return c.fetchone()


def fetchcolumn(query: str, params=()) -> List[str]:
    '''
    Executes a given query and retrives a single column from all rows. Does not change data.
    '''

    with sqlite3.connect(DB_FILE) as conn:
        conn.row_factory = lambda cursor, row: row[0]
        c = conn.cursor()
        c.execute(query, params)
        return c.fetchall()
