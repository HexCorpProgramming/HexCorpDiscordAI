import src.db.database

# Make database.connect() default to 'test.db'.
original_connect = src.db.database.connect
src.db.database.connect = lambda filename='test.db': original_connect(filename=filename)
