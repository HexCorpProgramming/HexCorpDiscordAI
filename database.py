import glob
import logging
import sqlite3
from hashlib import sha256

LOGGER = logging.getLogger('ai')

def prepare():
    conn = sqlite3.connect('ai.db')
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
            if saved_hash is not None and script_hash != saved_hash:
                raise Exception(f"Bad migration. For script {script_file} expected has {saved_hash} but got {script_hash}")

            c.executescript(script.read())
            c.execute("INSERT INTO schema_version values (:file, :hashed)",
                      {'file': script_file, 'hashed': script_hash})

    c.execute("SELECT * from schema_version")
    LOGGER.info(f'DB schema after migration {c.fetchall()}')
    conn.close()
