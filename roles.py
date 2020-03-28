import discord
from discord.utils import get

INITIATE = 'Initiate'
ASSOCIATE = 'Associate'
DRONE = '⬡-Drone'
DEEP_DRONE = '⬢-Drone'
STORED = '⬡-Stored'
ADMIN = 'admin'
MODERATION = 'Moderation Drone'
HIVE_MXTRESS = 'Drone Hive Mxtress'

GAGGED = '⬡-Gagged'
ENFORCER = '⬡-Enforcer'

DRONE_MODE = '⬡-DroneMode'

MODERATION_ROLES = [ADMIN, MODERATION, HIVE_MXTRESS]

EVERYONE = '@everyone'

def has_role(member: discord.Member, role: str) -> bool:
    return get(member.roles, name=role) is not None
