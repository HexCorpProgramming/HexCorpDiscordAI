import asyncio
from pathlib import Path
import src.db.database
from main import prepare_database

# Make database.connect() default to 'test.db'.
original_connect = src.db.database.connect
src.db.database.connect = lambda filename='test.db': original_connect(filename=filename)

# Reset the database.
p = Path('test.db')
p.unlink(True)
asyncio.run(prepare_database())
