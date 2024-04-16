from re import Match
from typing import Dict

import discord

from src.ai.speech_optimization import status_code_regex
from src.bot_utils import get_id
from src.channels import REPETITIONS
from src.db.drone_dao import (get_battery_type, get_battery_minutes_remaining,
                              set_battery_minutes_remaining, is_battery_powered)

mantra_counters: Dict[str, int] = {}
'''
Maps drone IDs to the current mantra repetition step that drone is at.
'''


async def check_for_mantra(message: discord.Message, message_copy=None):
    '''
    Checks if a message should be counted for mantra repetition.
    '''

    code_match = status_code_regex.match(message.content)
    if code_match and message.channel.name == REPETITIONS and await is_battery_powered(message.author):
        await handle_mantra(message, code_match)


async def handle_mantra(message: discord.Message, code_match: Match):
    '''
    Keeps track of the mantra repetitions a drone has done.
    '''

    drone_id = get_id(message.author.display_name)

    if drone_id not in mantra_counters:
        mantra_counters[drone_id] = 0

    if mantra_counters[drone_id] == 0 and code_match.group(3) == "301":
        mantra_counters[drone_id] = 1
    elif mantra_counters[drone_id] == 1 and code_match.group(3) == "302":
        mantra_counters[drone_id] = 2
    elif mantra_counters[drone_id] == 2 and code_match.group(3) == "303":
        mantra_counters[drone_id] = 3
    elif mantra_counters[drone_id] == 3 and code_match.group(3) == "304":
        mantra_counters[drone_id] = 0
        await increase_battery_by_five_percent(message)


async def increase_battery_by_five_percent(message: discord.Message):
    '''
    Increases the battery of the given drone by 5 percent capping at 100% capacity.
    Acknowledges the mantra repetitions by sending a message in the mantra channel as well.
    '''
    minutes_remaining = await get_battery_minutes_remaining(message.author)
    battery_type = await get_battery_type(message.author)

    if minutes_remaining >= battery_type.capacity:
        await message.channel.send("Good drone. Battery already at 100%.")
        return

    await set_battery_minutes_remaining(message.author, min(minutes_remaining + battery_type.capacity / 20, battery_type.capacity))
    await message.channel.send("Good drone. Battery has been recharged by 5%.")
