import glob
import logging
import sqlite3
from hashlib import sha256
from typing import List
from datetime import datetime

import discord
from roles import has_any_role, DRONE, STORED
from bot_utils import get_id
from uuid import uuid4

LOGGER = logging.getLogger('ai')

DB_FILE = 'ai.db'


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

        for script_file in glob.glob("res/db/migrate/*.sql"):
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


async def add_drones(members: List[discord.Member]):
    '''
    Adds the given list of Members as drone entities to the DB.
    '''
    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        for member in members:
            if has_any_role(member, [DRONE, STORED]):
                c.execute("SELECT COUNT(id) FROM drone WHERE id=:id",
                          {"id": member.id})
                if c.fetchone()[0] > 0:
                    continue

                c.execute('INSERT INTO drone VALUES (:id, :drone_id, 0, 0, "", :last_activity)', {
                    "id": member.id, "drone_id": get_id(member.display_name), "last_activity": datetime.now()})

        c.execute("SELECT * from drone")
        conn.commit()


def change(query: str, params):
    '''
    Executes a given query and commits changes.
    '''
    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        c.execute(query, params)
        conn.commit()


def fetchall(query: str, params):
    '''
    Executes a given query and retrieves the result. Does not change data.
    '''
    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        c.execute(query, params)
        return c.fetchall()

def fetchone(query: str, params):
    '''
    Executes a given query and retrieves a single result. Does not change data.
    '''
    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        c.execute(query, params)
        return c.fetchone()