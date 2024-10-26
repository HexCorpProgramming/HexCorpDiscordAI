import discord
from src.db.data_objects import Drone
from discord.ext.commands import BadArgument, Context, MemberConverter, MemberNotFound
from typing import Self
from src.resources import DRONE_AVATAR
from src.log import log
from operator import attrgetter


def proxy(proxied, prop: str):
    '''
    Add all the properties and methods of the proxied class onto the proxy class.

    proxied: The class to be proxied.
    prop: The property name under which the proxied object will be stored in the proxy class.
    '''

    def make_proxy(cls):
        '''
        Make class "cls" a proxy for class "proxied".
        '''

        # Iterate over every property and method of the class to be proxied.
        for attr in dir(proxied):

            # Ignore private members.
            if attr.startswith('_'):
                continue

            # Create a getter and setter that wrap the property or method.
            getter = attrgetter(f"{prop}.{attr}")
            setter = (lambda a: lambda self, v: setattr(getattr(self, prop), a, v))(attr)

            # Set the property on the proxy class.
            setattr(cls, attr, property(getter, setter, doc=f"{proxied.__name__}.{attr}"))

        return cls

    return make_proxy


@proxy(discord.Member, '_member')
class DroneMember:
    _member = None
    drone = None

    def __init__(self, member: discord.Member):
        '''
        Do not call this directly, use one of:

        ```python
        await DroneMember.create()
        await DroneMember.find()
        await DroneMember.load()
        ```
        '''

        self._member = member

    @classmethod
    async def create(cls, member: discord.Member, drone: Drone | None = None) -> Self:
        '''
        Factory for creating DroneMembers.

        This is necessary because __init__ cannot be async.
        '''

        result = cls(member)
        result.drone = drone or await Drone.find(member=member)

        return result

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
            raise BadArgument('Could not find member ' + argument)

        # Combine the Drone and Member.
        return await DroneMember.create(member)

    @classmethod
    async def load(cls, guild: discord.Guild, *, discord_id: int | None = None, drone_id: str | None = None) -> Self:
        '''
        Create a DroneMember given a guild and either a Discord ID or a drone ID.

        Raises an exception if no member is found.
        '''

        drone_member = await cls.find(guild, discord_id=discord_id, drone_id=drone_id)

        if drone_member is None:
            raise Exception('Could not find guild member by Discord ID ' + str(discord_id))

        return drone_member

    @classmethod
    async def find(cls, guild: discord.Guild, *, discord_id: int | None = None, drone_id: str | None = None) -> Self | None:
        '''
        Find a DroneMember given a guild and either a Discord ID or a drone ID.

        Returns None if no member is found
        '''

        if drone_id is not None:
            drone = await Drone.load(drone_id=drone_id)

            if drone is None:
                return None

            discord_id = drone.discord_id

        member = guild.get_member(discord_id)

        if member is None:
            return None

        return await DroneMember.create(member)

    def identity_enforcable(self, channel: discord.TextChannel) -> bool:
        '''
        Determine if a member's drone identity should be enforced in the given channel.
        '''

        return self.drone and self.drone.identity_enforcable(channel)

    def avatar_url(self, channel: discord.TextChannel) -> str:
        '''
        Fetch the URL for the member's avatar.
        '''

        return self.display_avatar.url if not self.identity_enforcable(channel) else DRONE_AVATAR

    async def update_display_name(self) -> None:
        '''
        Change the drone's display name depending on their DroneOS state.
        '''

        if not self.drone:
            return

        icon = '⬢' if self.drone.is_configured() else '⬡'

        new_display_name = f"{icon}-Drone #{self.drone.drone_id}"

        if self.display_name == new_display_name:
            # Return false if no update required.
            return

        log.info(f"Updating drone display name. Old name: {self.display_name}. New name: {new_display_name}.")
        await self.edit(nick=new_display_name)
