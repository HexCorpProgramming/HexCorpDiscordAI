from contextvars import ContextVar

# The database connection, stored per execution context.
# Defaults to empty, which will raise an error.
cursor = ContextVar('cursor')
transactions = ContextVar('transactions')
