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

GAGGED = '⬡-Gagged'

SPEECH_OPTIMIZATION = "⬡-Optimized"
GLITCHED = "⬡-Glitched"

MODERATION_ROLES = [ADMIN, MODERATION, HIVE_MXTRESS]

NITRO_BOOSTER = '⬡-Battery'
PATREON_SUPPORTER = '⬡-Patreon'

EVERYONE = '@everyone'


def has_role(member: discord.Member, role: str) -> bool:
    return get(member.roles, name=role) is not None


def has_any_role(member: discord.Member, roles: List[str]) -> bool:
    return any([has_role(member, role) for role in roles])
