import discord
from discord.utils import get
from typing import List

INITIATE = 'Initiate'
ASSOCIATE = 'Associate'
DRONE = '⬡-Drone'
ENFORCER_DRONE = '⬢-Drone'
STORED = '⬡-Stored'
ADMIN = 'admin'
MODERATION = 'Moderation Drone'
HIVE_MXTRESS = 'Drone Hive Mxtress'

GAGGED = '⬡-Gagged'

DRONE_MODE = '⬡-DroneMode'

MODERATION_ROLES = [ADMIN, MODERATION, HIVE_MXTRESS]

NITRO_BOOSTER = 'Nitro Booster'
PATREON_SUPPORTER = '⬡-Patreon'

EVERYONE = '@everyone'

def has_role(member: discord.Member, role: str) -> bool:
    return get(member.roles, name=role) is not None

def has_any_role(member: discord.Member, roles: List[str]) -> bool:
    return any([has_role(member, role) for role in roles])