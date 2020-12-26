from db.database import fetchall, change
from db.data_objects import Timer, map_to_objects

from typing import List

from datetime import datetime


def insert_timer(timer: Timer):
    '''
    Inserts the given timer into the table timer.
    '''
    change('INSERT INTO timer VALUES (:id, :drone_id, :mode, :end_time)', vars(timer))


def delete_timer(id: str):
    '''
    Deletes the timer with the given ID.
    '''
    change('DELETE FROM timer WHERE id = :id', {'id': id})


def delete_timers_by_drone_id(drone_id: str):
    '''
    Deletes the timer with the given ID.
    '''
    change('DELETE FROM timer WHERE drone_id = :drone_id', {'drone_id': drone_id})


def get_timers_elapsed_before(time: datetime) -> List[Timer]:
    '''
    Finds all timers, that ended before the given time.
    Returns an empty list if there are none.
    '''
    return map_to_objects(fetchall('SELECT id, target_id, mode, end_time FROM timer where end_time < :time', {'time': time}), Timer)
