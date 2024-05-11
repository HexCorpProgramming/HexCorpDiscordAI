from datetime import datetime
from discord import Emoji, Member, Message, Role, TextChannel
from discord.ext.commands import Bot, Cog
from discord.utils import get
from typing import Any, List, Iterable
from src.emoji import BATTERY_FULL, BATTERY_MID, BATTERY_LOW, BATTERY_EMPTY, DRONE_EMOJI
from src.roles import (INITIATE, ASSOCIATE, DRONE, STORED, DEVELOPMENT, ADMIN, MODERATION, HIVE_MXTRESS,
                       SPEECH_OPTIMIZATION, GLITCHED, ID_PREPENDING, IDENTITY_ENFORCEMENT,
                       THIRD_PERSON_ENFORCEMENT, BATTERY_POWERED, BATTERY_DRAINED, FREE_STORAGE,
                       HIVE_VOICE, MODERATION_ROLES, VOICE, NITRO_BOOSTER, EVERYONE)
from unittest.mock import AsyncMock, MagicMock
from src.db.data_objects import BatteryType, Drone, DroneOrder, Storage, Timer
from src.drone_member import DroneMember
from src.bot_utils import COMMAND_PREFIX

unique_id = 1

emojis = [
    'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q',
    'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z', '1', '2', '3', '4', '5', '6', '7', '8', '9',
    'blank', 'hex_slash', 'hex_dot', 'hex_questionmark', 'hex_exclamationmark', 'hex_comma',
    BATTERY_FULL, BATTERY_MID, BATTERY_LOW, BATTERY_EMPTY, DRONE_EMOJI,
]

roles = [
    INITIATE, ASSOCIATE, DRONE, STORED, DEVELOPMENT, ADMIN, MODERATION, HIVE_MXTRESS, SPEECH_OPTIMIZATION,
    GLITCHED, ID_PREPENDING, IDENTITY_ENFORCEMENT, THIRD_PERSON_ENFORCEMENT, BATTERY_POWERED, BATTERY_DRAINED,
    FREE_STORAGE, HIVE_VOICE, MODERATION_ROLES, VOICE, NITRO_BOOSTER, EVERYONE,
]


class Mocks():
    '''
    Manage a mock guild.
    '''

    _guild: MagicMock

    _bot: Bot

    def __init__(self):
        self._guild = self.guild()

        # Set up some default channels.
        for name in ['general', 'hex-office', 'hexcorp-transmissions']:
            self.channel(name)

        # Set up default emoji.
        for name in emojis:
            self.emoji(name)

        # Set up default roles.
        for name in roles:
            self.role(name)

        self.hive_mxtress()

        self._bot = self.bot()

        # Add the Bot as a property on the guild so it can be accessed by the Cog test.
        self._guild._bot = self._bot

    def get_guild(self) -> MagicMock:
        '''
        Get the mock Guild.
        '''

        return self._guild

    def get_bot(self) -> Bot:
        '''
        Get the Bot, for testing bot commands.
        '''

        return self._bot

    def get_cog(self) -> Cog:
        '''
        Get the first Cog on the bot.

        The bot should usually only have one Cog, as added by the @cog() decorator.
        '''

        cogs = self.get_bot().cogs

        if len(cogs) == 0:
            raise Exception('Bot has no Cogs')

        return cogs[next(iter(cogs))]

    def get_unique_id(self) -> int:
        '''
        Create an ID unique to this run of the application.
        '''

        global unique_id

        unique_id += 1

        return unique_id

    def find(self, collection, **kwargs) -> Any:
        '''
        Find an item within a collection.

        Returns the first item whose properties match all keyword arguments.

        Returns None if no matching item is found.
        '''

        def all_equal(obj: object, props: dict) -> bool:
            for key, value in props:
                if getattr(obj, key, None) != value:
                    return False

            return True

        props = kwargs.items()

        for item in collection:
            if all_equal(item, props):
                return item

        return None

    def get(self, collection: Iterable, **kwargs) -> Any:
        '''
        Return an item from a collection.

        Returns the first item whose properties match all keyword arguments.

        Raises an Exception if no matching item is found.
        '''

        item = self.find(collection, **kwargs)

        if item is None:
            raise Exception('Failed to find item')

        return item

    def set_drone_members(self, drones: List[MagicMock], members: List[MagicMock]) -> None:
        '''
        Set the drone and memeber records that will be used to build DroneMembers returned by the parameter converter.

        This sets the return values from Drone.find(), so you will also need to use it if you are loading drones manually.

        To return drones and members after the DroneMember parameter converter, put a None in both drone and member.
        For example to return two drone members in the `Greedy[DroneMember]` argument, then one manually afterwards, use:

        ```python
        drones = [bot.create_drone(), bot.create_drone(), None, bot.create_drone()]
        member = [bot.member_drone(), bot.member_drone(), None, bot.member_drone()]
        ```
        '''

        self._guild.drone_members['drones'] = drones
        self._guild.drone_members['members'] = members

    def guild(self) -> MagicMock:
        '''
        Create a mock guild.
        '''

        guild = MagicMock(channels=[], text_channels=[], roles=[], _members={}, emojis=[])

        # These are called by the discord.Member parameter converter.
        guild.get_member_named.return_value = None
        guild.query_members = AsyncMock(return_value=[])

        # This will be filled in by set_drone_members().
        guild.drone_members = {'drones': [], 'members': []}

        return guild

    def record(self, **kwargs) -> Any:
        '''
        Create a mock of a class that derives from Record.
        '''

        record = MagicMock(**kwargs)

        record.insert = AsyncMock()
        record.delete = AsyncMock()
        record.find = AsyncMock()
        record.load = AsyncMock()
        record.save = AsyncMock()
        record.all = AsyncMock()

        return record

    def drone(self, drone_id: str | int, **kwargs) -> MagicMock:
        '''
        Create a mock drone record.
        '''

        drone_id = str(drone_id)
        drone = self.record(spec=Drone, table='drone')

        drone.drone_id = drone_id
        drone.ignore_properties = ['battery_type', 'storage', 'order']
        drone.id_column = 'discord_id'
        drone.discord_id = drone_id + 'snowflake'
        drone.optimized = False
        drone.glitched = False
        drone.trusted_users = []
        drone.last_activity = datetime.now()
        drone.id_prepending = False
        drone.identity_enforcement = False
        drone.third_person_enforcement = False
        drone.can_self_configure = False
        drone.temporary_until = None
        drone.is_battery_powered = False
        drone.battery_type_id = 2
        drone.battery_minutes = 100
        drone.free_storage = False
        drone.associate_name = 'Associate ' + drone_id
        drone.battery_type = self.battery_type()
        drone.storage = None
        drone.order = None

        # TODO: Use autospec?

        self.set_props(drone, kwargs)

        return drone

    def set_props(self, object: object, props: dict) -> None:
        '''
        Set properties on an object to the values contained in a dictionary.
        '''

        for key, value in props.items():
            setattr(object, key, value)

    def channel(self, name: str) -> MagicMock:
        '''
        Create a mock channel and add it to the guild.
        '''

        existing = get(self._guild.channels, name=name)

        if existing:
            return existing

        channel = MagicMock(spec=TextChannel)
        channel.id = self.get_unique_id()
        channel.name = name

        # A shortcut to get the first webhook.
        channel.webhook = AsyncMock()
        channel.webhooks.return_value = [channel.webhook]

        self._guild.channels.append(channel)
        self._guild.text_channels.append(channel)

        return channel

    def role(self, name: str) -> MagicMock:
        '''
        Create a mock role and add it to the guild.
        '''

        existing = self.find(self._guild.roles, name=name)

        if existing:
            return existing

        role = MagicMock(spec=Role)
        role.id = self.get_unique_id()
        role.name = name
        role.guild = self._guild

        self._guild.roles.append(role)

        return role

    def member(self, nick=None, **kwargs) -> MagicMock:
        '''
        Create a mock Discord Member.
        '''

        if nick is None:
            nick = 'User' + str(self.get_unique_id())

        member = MagicMock(spec=Member)

        member.id = kwargs.get('id', 'snowflake' + nick)
        member.bot = False
        member.display_avatar.url = 'Pretty avatar'
        member.nick = nick
        member.display_name = nick
        member.edit = AsyncMock()
        member.mention = ''

        self.set_props(member, kwargs)

        member._roles = [self.role(role) for role in kwargs.get('roles', [])]

        # member.roles should be an @property but that can't be patched onto an object, only a class.
        member.roles = member._roles

        self._guild._members[member.id] = member

        return member

    def message(self, author=None, channel_name='', content='', **kwargs) -> Message:
        '''
        Create a new mock Message object.

        Channel: The channel name, e.g. general.
        Content: The message's text.

        Any additional keyword parameters are set as properties on the message.
        '''

        message = AsyncMock(spec=Message, mentions=[], author=author or self.member())
        message.id = self.get_unique_id()
        message.drone_members = {'drones': [], 'members': []}
        message.channel = self.channel(channel_name)
        message.guild = self._guild
        message.content = content

        message.state = AsyncMock()
        message.state.create_message = MagicMock()

        # Set any additional properties.
        for n, v in kwargs.items():
            setattr(message, n, v)

        return message

    def direct_message(self, author=None, content='', **kwargs) -> Message:
        '''
        Create a new mock Message object.

        Content: The message's text.

        Any additional keyword parameters are set as properties on the message.
        '''

        message = AsyncMock(spec=Message, mentions=[], author=author or self.member())
        message.id = self.get_unique_id()
        message.drone_members = {'drones': [], 'members': []}
        message.guild = None
        message.content = content

        message.state = AsyncMock()
        message.state.create_message = MagicMock()

        self.set_props(message, kwargs)

        return message

    def hive_mxtress(self, **kwargs) -> MagicMock:
        '''
        Create a mock DroneMember representing the Hive Mxtress.
        '''

        existing = self.find(self._guild._members, id='snowflake0006')

        if existing:
            return existing

        member = self.member()

        # Assign the HIVE_MXTRESS role to the member.
        member._roles = [self.role(HIVE_MXTRESS)]
        member.roles = member._roles

        self.set_props(member, kwargs)

        return member

    def battery_type(self, **kwargs) -> MagicMock:
        '''
        Create a mock BatteryType.
        '''

        battery_type = self.record(spec=BatteryType, table='battery_types')

        battery_type.id = 2
        battery_type.name = 'Medium'
        battery_type.capacity = 480
        battery_type.recharge_rate = 120

        self.set_props(battery_type, kwargs)

        return battery_type

    def drone_member(self, drone_id: str | int, **kwargs) -> MagicMock:
        '''
        Create a mock drone member for testing.

        The database methods are mocked out.
        The HIVE_MXTRESS role is added if the id is 0006.
        '''

        # Special case for the Hive Mxtress with no Drone record.
        if drone_id == '0006':
            drone_member = self.hive_mxtress()
            drone_member.drone = None

        drone_id = str(drone_id)
        discord_id = drone_id + 'snowflake'
        nick = 'Drone-#' + drone_id

        drone_member = MagicMock(spec=DroneMember)
        drone_member.id = discord_id
        drone_member.bot = False
        drone_member._avatar = 'Pretty avatar'
        drone_member.nick = nick
        drone_member.display_name = nick
        drone_member.edit = AsyncMock()
        drone_member.guild = self._guild
        drone_member.mention = f'<@{discord_id}>'
        drone_member._roles = [self.role(role) for role in kwargs.get('roles', [])]
        drone_member.roles = drone_member._roles
        # drone_member.roles = property(lambda self: self._roles)
        drone_member.drone = self.drone(drone_id)

        async_methods = [
            'create',
            'find',
            'load',
            'update_display_name',
            'add_roles',
            'remove_roles',
            'ban',
            'unban',
            'kick',
            'edit',
            'timeout',
            'timeout_for',
            'remove_timeout',
            'request_to_speak',
            'move_to'
        ]

        # Set async methods to async mocks.
        for method in async_methods:
            setattr(drone_member, method, AsyncMock())

        self.set_props(drone_member, {k: v for k, v in kwargs.items() if not k.startswith('drone_')})
        self.set_props(drone_member.drone, {k[6:]: v for k, v in kwargs.items() if k.startswith('drone_')})

        return drone_member

    def drone_order(self, **kwargs) -> MagicMock:
        '''
        Create a mock DroneOrder record.
        '''

        drone_order = self.record(spec=DroneOrder)
        drone_order.table = 'drone_order'
        drone_order.id = self.get_unique_id()
        drone_order.protocol = ''
        drone_order.finish_time = datetime.now()

        return drone_order

    def storage(self, **kwargs) -> MagicMock:
        '''
        Create a mock Storage record.
        '''

        storage = self.record(spec=Storage)
        storage.table = 'storage'
        storage.id = self.get_unique_id()

        return storage

    def timer(self, **kwargs) -> MagicMock:
        '''
        Create a mock Timer record.
        '''

        timer = self.record(spec=Timer)
        timer.table = 'timer'
        timer.id = self.get_unique_id()

        return timer

    def bot(self, **kwargs) -> Bot:
        '''
        Create a bot for testing with.

        This creates an actual Bot object, not a mock, so that the argument parsing for commands is in place.
        '''
        # Create the bot
        bot = Bot(command_prefix=COMMAND_PREFIX)

        # Give the bot a user as if it is connected to the server.
        bot._connection.user = self.member(bot=True)

        # Set up the guild to reference the mock guild.
        bot._connection._guilds = {0: self._guild}

        return bot

    def emoji(self, name: str, **kwargs) -> MagicMock:
        '''
        Create a mock emoji.
        '''

        existing = self.find(self._guild.emoji, name=name)

        if existing:
            return existing

        emoji = MagicMock(spec=Emoji)
        emoji.id = self.get_unique_id()
        emoji.name = name
        emoji.__str__ = lambda e: e.name

        self.set_props(emoji, kwargs)

        self._guild.emojis.append(emoji)

        return emoji
