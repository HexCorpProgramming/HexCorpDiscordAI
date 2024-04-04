import asyncio
from pathlib import Path
import src.db.database

# Make database.connect() default to 'test.db'.
original_connect = src.db.database.connect
src.db.database.connect = lambda filename='test.db': original_connect(filename=filename)

# The prepare_database function can only be imported after connect() is patched.
from main import prepare_database  # noqa: E402

# Reset the database.
p = Path('test.db')
p.unlink(True)
asyncio.run(prepare_database())
