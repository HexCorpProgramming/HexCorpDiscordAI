from src.db.database import fetchall, change
from src.db.data_objects import Timer, map_to_objects

from typing import List

from datetime import datetime


async def insert_timer(timer: Timer):
    '''
    Inserts the given timer into the table timer.
    '''
    await change('INSERT INTO timer VALUES (:id, :discord_id, :mode, :end_time)', vars(timer))


async def delete_timer(id: str):
    '''
    Deletes the timer with the given ID.
    '''
    await change('DELETE FROM timer WHERE id = :id', {'id': id})


async def delete_timers_by_id_and_mode(discord_id: str, mode: str):
    '''
    Deletes the timer with the given ID and mode.
    '''
    await change('DELETE FROM timer WHERE discord_id = :discord_id AND timer.mode = :mode', {'discord_id': discord_id, 'mode': mode})


async def get_timers_elapsed_before(time: datetime) -> List[Timer]:
    '''
    Finds all timers, that ended before the given time.
    Returns an empty list if there are none.
    '''
    return map_to_objects(await fetchall('SELECT id, discord_id, mode, end_time FROM timer WHERE end_time < :time', {'time': time}), Timer)
