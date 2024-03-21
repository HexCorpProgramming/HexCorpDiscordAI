from contextvars import ContextVar
from typing import List
import sqlite3

# The database connection, stored per execution context.
# Defaults to empty, which will raise an error.
cursor: sqlite3.Cursor = ContextVar('cursor')
transactions: List[int] = ContextVar('transactions')
