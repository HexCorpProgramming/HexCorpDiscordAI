import discord
from discord.utils import get
from typing import List

INITIATE = 'Initiate'
ASSOCIATE = 'Associate'
DRONE = '⬡-Drone'
STORED = '⬡-Stored'
DEVELOPMENT = '⬡-Development'
ADMIN = 'admin'
MODERATION = '⬡-Moderation'
HIVE_MXTRESS = 'Drone Hive Mxtress'

SPEECH_OPTIMIZATION = "⬡-Optimized"
GLITCHED = "⬡-Glitched"
ID_PREPENDING = "⬡-Prepending"
IDENTITY_ENFORCEMENT = "⬡-Enforced"

MODERATION_ROLES = [ADMIN, MODERATION, HIVE_MXTRESS]

VOICE = '⬡-Voice'

NITRO_BOOSTER = '⬡-Integrated'

EVERYONE = '@everyone'


def has_role(member: discord.Member, role: str) -> bool:
    return get(member.roles, name=role) is not None


def has_any_role(member: discord.Member, roles: List[str]) -> bool:
    return any([has_role(member, role) for role in roles])
