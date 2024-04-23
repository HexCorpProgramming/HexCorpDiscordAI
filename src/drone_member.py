import discord
from discord.ext.commands import BadArgument, Context, MemberConverter, MemberNotFound
from src.db.data_objects import Drone
from typing import Any, Self
from src.resources import DRONE_AVATAR
from src.channels import DRONE_HIVE_CHANNELS, HEXCORP_CONTROL_TOWER_CATEGORY, MODERATION_CATEGORY
from src.log import log


class DroneMember(discord.Member):
    '''
    A Discord member record augmented with a drone record.

    This can be used anywhere that discord.Member can be used.
    It also has a .drone property that contains a Drone record, if the Member has one.
    '''

    drone: Drone | None

    async def __init__(self, member: discord.Member):
        self.drone = await Drone.find(member)
        self.member = member

    def __getattr__(self, name) -> Any:
        return getattr(self.member, name)

    def __setattr__(self, name: str, value: any) -> None:
        setattr(self.member, name, value)

    def identity_enforcable(self, channel: discord.TextChannel) -> bool:
        '''
        Determine if a member's drone identity should be enforced in the given channel.
        '''

        return self.drone and (channel.name in DRONE_HIVE_CHANNELS or self.drone.identity_enforcement) and channel.category.name not in [HEXCORP_CONTROL_TOWER_CATEGORY, MODERATION_CATEGORY]

    def avatar_url(self, channel: discord.TextChannel) -> str:
        '''
        Fetch the URL for the member's avatar.
        '''

        return self.member.display_avatar.url if not self.identity_enforcable(channel) else DRONE_AVATAR

    @classmethod
    async def convert(cls, context: Context, argument: str) -> Self:
        '''
        Converts a given argument to a Member that is a drone.
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
        return await DroneMember(member)

    @classmethod
    async def load(cls, guild: discord.Guild, *, discord_id: int | None = None, drone_id: str | None = None):
        '''
        Create a DroneMember given a guild and either a Discord ID or a drone ID.
        '''

        if drone_id is not None:
            drone = Drone.load(drone_id=drone_id)
            discord_id = drone.discord_id

        return await DroneMember(guild.get_member(discord_id))

    async def update_display_name(self):
        '''
        Change the drone's display name depending on their DroneOS state.
        '''

        if not self.drone:
            return

        icon = '⬢' if self.drone.is_configured() else '⬡'

        new_display_name = f"{icon}-Drone #{self.drone.drone_id}"

        if self.member.display_name == new_display_name:
            # Return false if no update required.
            return False

        log.info(f"Updating drone display name. Old name: {self.member.display_name}. New name: {new_display_name}.")
        await self.member.edit(nick=new_display_name)
        return True
