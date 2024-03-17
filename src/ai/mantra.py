from ast import Match
from typing import Dict

import discord

from src.ai.speech_optimization import status_code_regex
from src.bot_utils import get_id
from src.db.drone_dao import (get_battery_minutes_remaining,
                              set_battery_minutes_remaining, is_battery_powered)
from src.resources import MAX_BATTERY_CAPACITY_MINS

mantra_counters: Dict[str, int] = {}


async def check_for_mantra(message: discord.Message, message_copy=None):
    code_match = status_code_regex.match(message.content)
    if code_match and message.channel.name == 'hive-repetitions' and is_battery_powered(message.author):
        await handle_mantra(message, code_match)


async def handle_mantra(message: discord.Message, code_match: Match):
    drone_id = get_id(message.author.display_name)

    if drone_id not in mantra_counters and code_match.group(3) == "301":
        mantra_counters[drone_id] = 1

    if mantra_counters[drone_id] == 1 and code_match.group(3) == "302":
        mantra_counters[drone_id] = 2

    if mantra_counters[drone_id] == 2 and code_match.group(3) == "303":
        mantra_counters[drone_id] = 3

    if mantra_counters[drone_id] == 3 and code_match.group(3) == "304":
        mantra_counters[drone_id] = 0
        await increase_battery_by_five_percent(message)


async def increase_battery_by_five_percent(message: discord.Message):
    minutes_remaining = get_battery_minutes_remaining(message.author)
    if minutes_remaining >= MAX_BATTERY_CAPACITY_MINS:
        await message.channel.send("Good drone. Battery already at 100%.")
        return

    await message.channel.send("Good drone. Battery has been recharged by 5%.")
    set_battery_minutes_remaining(message.author, minutes=min(minutes_remaining + MAX_BATTERY_CAPACITY_MINS / 20, MAX_BATTERY_CAPACITY_MINS))
