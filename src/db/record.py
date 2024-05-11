from src.db.database import change, fetchcolumn, fetchone
from typing import Any, List, Self, TypeVar

Object = TypeVar('Object', bound=object)


def map_to_objects(rows: List[dict], constructor: type[Object]) -> Object:
    '''
    Construct a list of objects from a list of dictionaries.
    '''

    return [constructor(**row) for row in rows]


def map_to_object(row: dict | None, constructor: type[Object]) -> Object:
    '''
    Construct an object from a dictionary.
    '''

    if row is None:
        return None

    return constructor(**row)


class Record:
    '''
    The base class for database records.
    This adds the methods: all, find, load, save, insert, delete.
    '''

    @classmethod
    def get_id_column(cls) -> str:
        '''
        Get the name of the column that stores the primary key.

        This will read the `id_column` property if it exists, else it will default to "id".
        '''

        return getattr(cls, 'id_column', 'id')

    def get_id(self) -> str:
        '''
        Get the value of the primary key for this record.
        '''

        return getattr(self, self.get_id_column())

    async def delete(self) -> None:
        '''
        Delete the current database record.
        '''

        await change(f'DELETE FROM {self.table} WHERE {self.get_id_column()} = :id', {'id': self.get_id()})

    @classmethod
    async def find(cls, id: Any = None, **kwargs) -> Self | None:
        '''
        Find a database record by the given column name and value.

        Note that the column name is used directly in the SQL and so must not contain user input.
        '''

        if id is not None:
            kwargs = {cls.get_id_column(): id}

        if len(kwargs) != 1:
            raise Exception('Record::find() requires exactly one keyword argument')

        column = next(iter(kwargs))
        value = kwargs[column]

        return map_to_object(await fetchone(f'SELECT * FROM {cls.table} WHERE {column} = :value', {'value': value}), cls)

    @classmethod
    async def load(cls, id: Any = None, **kwargs) -> Self:
        '''
        Load a single database record.

        Specify a single keyword argument that consists of the column name and value to find.

        Raises an Exception if the record is not found.
        '''

        if id is not None:
            kwargs = {cls.get_id_column(): id}

        result = await cls.find(**kwargs)

        if result is None:
            column = next(iter(kwargs))
            value = kwargs[column]

            raise Exception(f'Failed to find record in {cls.table_name} where {column} = {value}')

        return result

    @classmethod
    async def all(cls) -> List[Self]:
        '''
        Fetch all records.

        Records are loaded individually in case the class is overriding the load or find method.
        '''

        ids = await fetchcolumn(f'SELECT {cls.get_id_column()} FROM {cls.table}')
        records = []

        for id in ids:
            args = {cls.get_id_column(): id}
            records.append(cls.load(**args))

        return records

    def build_sets(self) -> None:
        '''
        Build a string of "column = :column" for INSERT and UPDATE statements.
        '''

        columns = vars(self).keys()
        ignore_properties = getattr(self, 'ignore_properties', [])

        # Build a string of "col_1 = :col_1, col_2 = :col2" etc.
        return ', '.join([f'{col} = :{col}' for col in columns if col not in ignore_properties])

    async def insert(self) -> None:
        '''
        Insert a new record.
        '''

        sets = self.build_sets()

        await change(f'INSERT INTO {self.table} SET {sets}', vars(self))

    async def save(self) -> None:
        '''
        Update an existing record.
        '''

        sets = self.build_sets()
        id = self.get_id_column()

        await change(f'UPDATE {self.table} SET {sets} WHERE {id} = :{id}', vars(self))
