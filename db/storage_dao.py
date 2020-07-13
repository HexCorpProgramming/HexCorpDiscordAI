from db.database import fetchall, change, fetchone
from db.dos import Storage, map_to_objects, map_to_object

from datetime import datetime
from typing import List


def insert_storage(storage: Storage):
    '''
    Inserts the given storage into the table drone_order.
    '''
    change('INSERT INTO storage VALUES (:id, :stored_by, :target_id, :purpose, :roles, :release_time)', vars(storage))


def delete_storage(id: int):
    '''
    Deletes the storage with the given ID.
    '''
    change('DELETE FROM storage WHERE id = :id', {'id': id})


def fetch_all_storage() -> List[Storage]:
    '''
    Get all current storage.
    '''
    return map_to_objects(fetchall('SELECT id, stored_by, target_id, purpose, roles, release_time FROM storage', {}), Storage)


def fetch_all_elapsed_storage() -> List[Storage]:
    '''
    Fetch all storage that should be released.
    '''
    return map_to_objects(fetchall('SELECT id, stored_by, target_id, purpose, roles, release_time FROM storage WHERE release_time < :now', {'now': datetime.now()}), Storage)

def fetch_storage_by_target_id(drone_id: str) -> Storage:
    '''
    Fetch a single storage by the target_id.
    '''
    return map_to_object(fetchone('SELECT id, stored_by, target_id, purpose, roles, release_time FROM storage WHERE target_id = :drone_id', {'drone_id': drone_id}), Storage)

def delete_storage_by_target_id(target_id: str):
    '''
    Deletes the storage with the given target_id.
    '''
    change('DELETE FROM storage WHERE target_id = :target_id', {'target_id': target_id})