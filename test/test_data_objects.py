from src.db.data_objects import DroneOrder, Storage
from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock, MagicMock, patch


class TestDataObjects(IsolatedAsyncioTestCase):
    @patch('src.db.data_objects.fetchcolumn', new_callable=AsyncMock)
    @patch('src.db.record.fetchone', new_callable=AsyncMock)
    async def test_storage_all_elapsed(self, fetchone: AsyncMock, fetchcolumn: AsyncMock) -> None:
        fetchcolumn.return_value = [1, 2, 3]
        fetchone.side_effect = [
            {'id': 1, 'stored_by': 1, 'target_id': 1, 'purpose': '', 'roles': '', 'release_time': '2000-01-01 01:02:03'},
            {'id': 2, 'stored_by': 2, 'target_id': 2, 'purpose': '', 'roles': '', 'release_time': '2000-01-01 01:02:03'},
            {'id': 3, 'stored_by': 3, 'target_id': 3, 'purpose': '', 'roles': '', 'release_time': '2000-01-01 01:02:03'},
        ]

        records = await Storage.all_elapsed()

        self.assertEqual(len(records), 3)
        self.assertEqual(records[0].id, 1)
        self.assertEqual(records[1].id, 2)
        self.assertEqual(records[2].id, 3)
        self.assertIsInstance(records[0], Storage)

    @patch('src.db.record.fetchcolumn', new_callable=AsyncMock)
    @patch('src.db.record.fetchone', new_callable=AsyncMock)
    @patch('src.drone_member.DroneMember')
    async def test_drone_order_all_drones(self, DroneMember: MagicMock, fetchone: AsyncMock, fetchcolumn: AsyncMock) -> None:
        fetchcolumn.return_value = [1, 2, 3]
        fetchone.side_effect = [
            {'id': '1', 'discord_id': 1, 'protocol': 'test 1', 'finish_time': '2000-01-01 01:02:03'},
            {'id': '2', 'discord_id': 2, 'protocol': 'test 2', 'finish_time': '2000-01-01 01:02:03'},
            {'id': '3', 'discord_id': 3, 'protocol': 'test 3', 'finish_time': '2000-01-01 01:02:03'},
        ]

        DroneMember.load = AsyncMock(return_value='test')

        records = await DroneOrder.all_drones(None)

        self.assertEqual(len(records), 3)
        self.assertEqual(records[0], 'test')
