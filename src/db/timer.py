from dataclasses import dataclass
from datetime import datetime
from typing import Any, List
from discord import Guild
from src.db.record import Record
from src.db.database import fetchcolumn


@dataclass
class Timer(Record):
    table = 'timer'
    '''
    The database table name.
    '''

    id: str
    '''
    The timer's unique ID.
    '''

    discord_id: int
    '''
    The Discord ID of the user to which the timer applies.
    '''

    mode: str
    '''
    The DroneOS parameter being timed.
    '''

    end_time: datetime
    '''
    The time at which the timer expires.
    '''

    @classmethod
    async def all_elapsed(cls, guild: Guild) -> List[Any]:
        '''
        Fetch all the DroneMembers whose timer has expired.
        '''

        # Import here to avoid a circular import.
        from src.drone_member import DroneMember

        ids = await fetchcolumn('SELECT discord_id FROM timer WHERE end_time >= datetime("now")')
        records = []

        for id in ids:
            records.append(await DroneMember.load(guild, discord_id=id))

        return records
