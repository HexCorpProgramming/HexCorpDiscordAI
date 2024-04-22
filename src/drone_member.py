import discord
from discord.ext.commands import BadArgument, Context, MemberConverter, MemberNotFound
from src.db.data_objects import Drone
from typing import Any, Self
from src.resources import DRONE_AVATAR
from src.channels import DRONE_HIVE_CHANNELS, HEXCORP_CONTROL_TOWER_CATEGORY, MODERATION_CATEGORY


class DroneMember(discord.Member):
    '''
    A Discord member record augmented with a drone record.

    This can be used anywhere that discord.Member can be used.
    It also has a .drone property that contains a Drone record, if the Member has one.
    '''

    drone: Drone | None

    def __init__(self, member: discord.Member):
        self.drone = Drone.find(member)
        self.member = member

    def __getattr__(self, name) -> Any:
        return getattr(self.member, name)

    def __setattr__(self, name: str, value: any) -> None:
        setattr(self.member, name, value)

    def identity_enforcable(self, channel: discord.TextChannel) -> bool:
        return self.drone and (channel.name in DRONE_HIVE_CHANNELS or self.drone.identity_enforcement) and channel.category.name not in [HEXCORP_CONTROL_TOWER_CATEGORY, MODERATION_CATEGORY]

    def avatar_url(self, channel: discord.TextChannel) -> str:
        return self.member.display_avatar.url if not self.identity_enforcable(channel) else DRONE_AVATAR

    @classmethod
    async def convert(cls, context: Context, argument: str) -> Self:
        '''
        Converts a given argument to a Member that is a drone. Raises BadArgument otherwise.
        Does not handle mentions. Those should be handled by the default converter.
        '''

        member = None

        try:
            # Try to find the member by Discord ID, mention, name, and nickname.
            member_converter = MemberConverter()
            member = await member_converter.convert(context, argument)
        except MemberNotFound:
            # If the member is not found then continue to try by drone ID.
            pass

        if member is None:
            # Try to find the member by drone ID.
            drone = await Drone.find(drone_id=argument)

            if drone:
                member = context.guild.get_member(drone.discord_id)

        if member is None:
            raise BadArgument

        # Combine the Drone and Member.
        return DroneMember(member)

    @classmethod
    async def load(cls, guild: discord.Guild, *, discord_id: int | None = None, drone_id: str | None = None):
        '''
        Create a DroneMember given a guild and either a Discord ID or a drone ID.
        '''

        if drone_id is not None:
            drone = Drone.load(drone_id=drone_id)
            discord_id = drone.discord_id

        return DroneMember(guild.get_member(discord_id))
