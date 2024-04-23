from src.db.database import change


async def delete_timers_by_id_and_mode(discord_id: str, mode: str):
    '''
    Deletes the timer with the given ID and mode.
    '''
    await change('DELETE FROM timer WHERE discord_id = :discord_id AND timer.mode = :mode', {'discord_id': discord_id, 'mode': mode})
