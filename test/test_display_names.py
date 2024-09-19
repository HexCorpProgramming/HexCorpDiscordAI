from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock
from src.drone_member import DroneMember
from test.mocks import Mocks

mocks = Mocks()


class TestDisplayNames(IsolatedAsyncioTestCase):

    async def test_display_name_when_unoptimized_drone_requires_no_updates(self) -> None:
        dm = await DroneMember.create(mocks.member(), mocks.drone('1234'))
        dm.display_name = '⬡-Drone #1234'
        dm.drone.optimized = False

        await dm.update_display_name()

        dm.edit.assert_not_called()

    async def test_display_name_when_optimized_drone_requires_no_updates(self) -> None:
        dm = await DroneMember.create(mocks.member(), mocks.drone('1234'))
        dm.display_name = '⬢-Drone #1234'
        dm.drone.optimized = True

        await dm.update_display_name()

        dm.edit.assert_not_called()

    async def test_display_name_edits_nick_of_unoptimized_drone_when_updates_required(self):
        options = 'third_person_enforcement', 'glitched', 'optimized', 'id_prepending', 'identity_enforcement', 'is_battery_powered'
        dm = await DroneMember.create(mocks.member(), mocks.drone('1234'))

        # Test each option individually.
        for option in options:

            # Set all options to False except one.
            for o in options:
                setattr(dm.drone, o, o == option)

            dm.display_name = '⬡-Drone #1234'
            dm.edit = AsyncMock()
            await dm.update_display_name()

            dm.edit.assert_called_with(nick='⬢-Drone #1234')

    async def test_display_name_edits_nick_of_optimized_drone_when_updates_required(self):
        dm = await DroneMember.create(mocks.member(), mocks.drone('1234'))
        dm.display_name = '⬢-Drone #1234'

        await dm.update_display_name()

        dm.edit.assert_called_with(nick='⬡-Drone #1234')
