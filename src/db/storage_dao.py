from src.db.database import fetchall, change, fetchone
from src.db.data_objects import Storage, map_to_objects, map_to_object

from datetime import datetime
from typing import List


async def insert_storage(storage: Storage):
    '''
    Inserts the given storage into the table drone_order.
    '''
    await change('INSERT INTO storage VALUES (:id, :stored_by, :target_id, :purpose, :roles, :release_time)', vars(storage))


async def delete_storage(id: int):
    '''
    Deletes the storage with the given ID.
    '''
    await change('DELETE FROM storage WHERE id = :id', {'id': id})


async def fetch_all_storage() -> List[Storage]:
    '''
    Get all current storage.
    '''
    return map_to_objects(await fetchall('SELECT id, stored_by, target_id, purpose, roles, release_time FROM storage', {}), Storage)


async def fetch_all_elapsed_storage() -> List[Storage]:
    '''
    Fetch all storage that should be released.
    '''
    return map_to_objects(await fetchall('SELECT id, stored_by, target_id, purpose, roles, release_time FROM storage WHERE release_time < :now', {'now': datetime.now()}), Storage)


async def fetch_storage_by_target_id(discord_id: int) -> Storage:
    '''
    Fetch a single storage by the target_id.
    '''
    return map_to_object(await fetchone('SELECT * FROM storage WHERE target_id = :discord_id', {'discord_id': discord_id}), Storage)
