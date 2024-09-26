from datetime import datetime, timedelta, timezone
from discord import Emoji, Member, Message, Role, TextChannel
from discord.channel import CategoryChannel
from discord.ext.commands import Bot, Cog, Context
from discord.utils import get
from functools import partial
from typing import Any, Iterable
from src.emoji import BATTERY_FULL, BATTERY_MID, BATTERY_LOW, BATTERY_EMPTY, DRONE_EMOJI
from src.roles import (INITIATE, ASSOCIATE, DRONE, STORED, DEVELOPMENT, ADMIN, MODERATION, HIVE_MXTRESS,
                       SPEECH_OPTIMIZATION, GLITCHED, ID_PREPENDING, IDENTITY_ENFORCEMENT,
                       THIRD_PERSON_ENFORCEMENT, BATTERY_POWERED, BATTERY_DRAINED, FREE_STORAGE,
                       HIVE_VOICE, MODERATION_ROLES, VOICE, NITRO_BOOSTER, EVERYONE)
from unittest.mock import AsyncMock, create_autospec, MagicMock
from src.db.data_objects import BatteryType, Drone, DroneOrder, Storage
from src.db.timer import Timer
from src.drone_member import DroneMember
from src.bot_utils import COMMAND_PREFIX
from src.db.record import Record
import src.channels as channels

unique_id = 1

emojis = [
    'hex_a', 'hex_b', 'hex_c', 'hex_d', 'hex_e', 'hex_f', 'hex_g', 'hex_h', 'hex_i', 'hex_j', 'hex_k', 'hex_l',
    'hex_m', 'hex_n', 'hex_o', 'hex_p', 'hex_q', 'hex_r', 'hex_s', 'hex_t', 'hex_u', 'hex_v', 'hex_w', 'hex_x',
    'hex_y', 'hex_z', 'hex_1', 'hex_2', 'hex_3', 'hex_4', 'hex_5', 'hex_6', 'hex_7', 'hex_8', 'hex_9',
    'blank', 'hex_slash', 'hex_dot', 'hex_questionmark', 'hex_exclamationmark', 'hex_comma', 'hex_dc',
    BATTERY_FULL, BATTERY_MID, BATTERY_LOW, BATTERY_EMPTY, DRONE_EMOJI,
]

roles = [
    INITIATE, ASSOCIATE, DRONE, STORED, DEVELOPMENT, ADMIN, MODERATION, HIVE_MXTRESS, SPEECH_OPTIMIZATION,
    GLITCHED, ID_PREPENDING, IDENTITY_ENFORCEMENT, THIRD_PERSON_ENFORCEMENT, BATTERY_POWERED, BATTERY_DRAINED,
    FREE_STORAGE, HIVE_VOICE, MODERATION_ROLES, VOICE, NITRO_BOOSTER, EVERYONE,
]


class TestBot(Bot):
    context: Context = None


class Mocks():
    '''
    Manage a mock guild.

    This class creates a mock guild and provides factory methods for creating mock objects associated with the guild.
    Creating a mock object will automatically add it to the guild.

    Mocks are created with create_autospec() instead of Mock() so that accessing invalid properties or members will
    cause an error, rather than creating a new mock property.
    '''

    _guild: MagicMock

    _bot: Bot

    def __init__(self):
        self._guild = self.guild()

        # Set up some default channels.
        for name in ['general', 'hex-office', 'hexcorp-transmissions', 'hive-storage-chambers']:
            self.channel(name)

        # Set up default emoji.
        for name in emojis:
            self.emoji(name)

        # Set up default roles.
        for name in roles:
            self.role(name)

        self.hive_mxtress()

        self._bot = self.bot()

    def mock(*args, **kwargs) -> MagicMock:
        return create_autospec(*args, **kwargs)

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

        for item in collection.values() if isinstance(collection, dict) else collection:
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

    def guild(self) -> MagicMock:
        '''
        Create a mock guild.
        '''

        guild = MagicMock(channels=[], text_channels=[], roles=[], _members={}, emojis=[])

        # These are called by the discord.Member parameter converter.
        guild.get_member_named.return_value = None
        guild.query_members = AsyncMock(return_value=[])

        guild.get_member = lambda discord_id: self.find(guild._members, id=discord_id)

        return guild

    def record(self, spec=Record, **kwargs) -> Any:
        '''
        Create a mock of a class that derives from Record.
        '''

        record = create_autospec(spec)

        self.set_props(record, kwargs)

        return record

    def drone(self, drone_id: str, **kwargs) -> MagicMock:
        '''
        Create a mock drone record.
        '''

        drone = create_autospec(Drone, table='drone')

        drone.drone_id = drone_id
        drone.ignore_properties = ['battery_type', 'storage', 'order']
        drone.id_column = 'discord_id'
        drone.discord_id = (int)('111111111111111' + drone_id)
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

        # Use the actual implementation of these simple functions.
        drone.allows_configuration_by.side_effect = partial(Drone.allows_configuration_by, drone)
        drone.allows_storage_by.side_effect = partial(Drone.allows_storage_by, drone)
        drone.trusts.side_effect = partial(Drone.trusts, drone)
        drone.is_configured.side_effect = partial(Drone.is_configured, drone)
        drone.get_battery_percent_remaining.side_effect = partial(Drone.get_battery_percent_remaining, drone)
        drone.third_person_enforcable.side_effect = partial(Drone.third_person_enforcable, drone)
        drone.identity_enforcable.side_effect = partial(Drone.identity_enforcable, drone)
        drone.enforcable_channel.side_effect = partial(Drone.enforcable_channel, drone)

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

        channel = create_autospec(TextChannel)
        channel.id = self.get_unique_id()
        channel.name = name
        channel.guild = self._guild

        # A shortcut to get the first webhook.
        channel.webhook = AsyncMock()
        channel.webhooks.return_value = [channel.webhook]

        self._guild.channels.append(channel)
        self._guild.text_channels.append(channel)

        # Assign pre-defined channels to the correct category.
        categories = {
            channels.OFFICE: channels.HEXCORP_CONTROL_TOWER_CATEGORY,
            channels.MODERATION_CHANNEL: channels.HEXCORP_CONTROL_TOWER_CATEGORY,
            channels.MODERATION_LOG: channels.MODERATION_CATEGORY,
        }

        channel.category = self.category_channel(categories.get(name, ''))

        return channel

    def category_channel(self, name: str, **kwargs) -> MagicMock:
        '''
        Create a mock channel category.
        '''

        category = create_autospec(CategoryChannel)
        category.name = name
        category.guild = self.guild
        category.id = self.get_unique_id()
        category.nsfw = False
        category.is_nsfw = lambda: category.nsfw

        self.set_props(category, kwargs)

        return category

    def role(self, name: str) -> MagicMock:
        '''
        Create a mock role and add it to the guild.
        '''

        existing = self.find(self._guild.roles, name=name)

        if existing:
            return existing

        role = create_autospec(Role)
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

        member = create_autospec(Member)

        member.id = int(kwargs.get('id', '111111111111111' + str(self.get_unique_id())))
        member.bot = False
        member.display_avatar.url = 'Pretty avatar'
        member.nick = nick
        member.display_name = nick
        member.edit = AsyncMock()
        member.mention = '<@' + str(member.id) + '>'
        member.joined_at = datetime.now(timezone.utc) - timedelta(weeks=3)

        self.set_props(member, kwargs)

        member._roles = [self.role(role) if isinstance(role, str) else role for role in kwargs.get('roles', [])]

        # member.roles should be an @property but that can't be patched onto an object, only a class.
        member.roles = member._roles

        self._guild._members[member.id] = member

        return member

    def command(self, author=None, channel_name='', content='', **kwargs) -> Message:
        '''
        Create a mock message prefixed with COMMAND_PREFIX.

        This is a convenience method to save you from having to import COMMAND_PREFIX into every test.
        '''

        return self.message(author, channel_name, COMMAND_PREFIX + content, **kwargs)

    def message(self, author=None, channel_name='', content='', **kwargs) -> Message:
        '''
        Create a new mock Message object.

        Channel: The channel name, e.g. general.
        Content: The message's text.

        Any additional keyword parameters are set as properties on the message.
        '''

        message = create_autospec(Message)
        message.mentions = []
        message.author = author or self.member()
        message.id = self.get_unique_id()
        message.channel = self.channel(channel_name)
        message.guild = self._guild
        message.content = content

        message.state = AsyncMock()
        message.state.create_message = MagicMock()

        self.set_props(message, kwargs)

        return message

    def direct_command(self, author=None, content='', **kwargs) -> Message:
        '''
        Create a mock direct message prefixed with COMMAND_PREFIX.

        This is a convenience method to save you from having to import COMMAND_PREFIX into every test.
        '''

        return self.direct_message(author, COMMAND_PREFIX + content, **kwargs)

    def direct_message(self, author=None, content='', **kwargs) -> Message:
        '''
        Create a new mock Message object.

        Content: The message's text.

        Any additional keyword parameters are set as properties on the message.
        '''

        message = self.message(author, '', content, **kwargs)
        message.guild = None

        return message

    def hive_mxtress(self, **kwargs) -> MagicMock:
        '''
        Create a mock DroneMember representing the Hive Mxtress.
        '''

        existing = self.find(self._guild._members, id='1111111111111110006')

        if existing:
            return existing

        # The Hive Mxtress does not have a drone record.
        member = self.drone_member('0006', drone=None)

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

        Specify a `member=` parameter to initialize from an existing [mock] member.
        '''

        drone_id = str(drone_id)
        discord_id = int('111111111111111' + str(drone_id))
        nick = 'Drone-' + drone_id

        drone_member = create_autospec(DroneMember)

        if kwargs.get('member', None) is not None:
            member = kwargs.get('member')

            drone_member.id = member.id
            drone_member.bot = member.bot
            drone_member._avatar = member._avatar
            drone_member.nick = member.nick
            drone_member.display_name = member.display_name
            drone_member.edit = member.edit
            drone_member.guild = member.guild
            drone_member.mention = member.mention
            drone_member._roles = member._roles
            drone_member.roles = member.roles
            drone_member.joined_at = member.joined_at
        else:
            drone_member.id = discord_id
            drone_member.bot = False
            drone_member._avatar = 'Pretty avatar'
            drone_member.nick = nick
            drone_member.display_name = nick
            drone_member.edit = AsyncMock()
            drone_member.guild = self._guild
            drone_member.mention = f'<@{discord_id}>'
            drone_member._roles = []
            drone_member.roles = []
            drone_member.joined_at = datetime.now(timezone.utc) - timedelta(weeks=3)

        if 'drone' not in kwargs:
            drone_member.drone = self.drone(drone_id)

        drone_member.avatar_url.return_value = drone_member._avatar

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
            'move_to',
            'send',
            'trigger_typing',
            'fetch_message',
            'pins',
        ]

        # Set async methods to async mocks.
        for method in async_methods:
            setattr(drone_member, method, AsyncMock())

        self.set_props(drone_member, {k: v for k, v in kwargs.items() if not k.startswith('drone_')})
        self.set_props(drone_member.drone, {k[6:]: v for k, v in kwargs.items() if k.startswith('drone_')})

        # Set the roles after set_props because they may need converting from role names to role objects.
        if kwargs.get('roles', None) is not None:
            drone_member._roles = [self.role(role) if isinstance(role, str) else role for role in kwargs.get('roles', [])]
            drone_member.roles = drone_member._roles

        # Ensure that the drone's discord ID matches the member after props have been set.
        if drone_member.drone is not None:
            drone_member.drone.discord_id = drone_member.id

        # Add the DroneMember to the guild.  This should really be just a Member, not a DroneMember.
        self._guild._members[drone_member.id] = drone_member

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

        self.set_props(drone_order, kwargs)

        return drone_order

    def storage(self, **kwargs) -> MagicMock:
        '''
        Create a mock Storage record.
        '''

        storage = self.record(spec=Storage)
        storage.table = 'storage'
        storage.id = self.get_unique_id()
        storage.stored_by = None
        storage.target_id = 0
        storage.purpose = 'testing'
        storage.roles = ''
        storage.release_time = datetime.now() + timedelta(hours=1)

        self.set_props(storage, kwargs)

        return storage

    def timer(self, **kwargs) -> MagicMock:
        '''
        Create a mock Timer record.
        '''

        timer = self.record(spec=Timer)
        timer.table = 'timer'
        timer.id = self.get_unique_id()

        self.set_props(timer, kwargs)

        return timer

    def bot(self, **kwargs) -> Bot:
        '''
        Create a bot for testing with.

        This creates an actual Bot object, not a mock, so that the argument parsing for commands is in place.
        '''
        # Create the bot
        bot = TestBot(command_prefix=COMMAND_PREFIX)

        # Give the bot a user as if it is connected to the server.
        bot._connection.user = self.member(bot=True)

        # Set up the guild to reference the mock guild.
        bot._connection._guilds = {0: self._guild}

        self.set_props(bot, kwargs)

        return bot

    def emoji(self, name: str, **kwargs) -> MagicMock:
        '''
        Create a mock emoji.
        '''

        existing = self.find(self._guild.emoji, name=name)

        if existing:
            return existing

        emoji = create_autospec(Emoji)
        emoji.id = self.get_unique_id()
        emoji.name = name
        emoji.__str__ = lambda e: f':{e.name}:'

        self.set_props(emoji, kwargs)

        self._guild.emojis.append(emoji)

        return emoji
