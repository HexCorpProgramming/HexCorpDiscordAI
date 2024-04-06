from src.db.database import fetchall, change, fetchone
from src.db.data_objects import DroneOrder, map_to_objects, map_to_object

from typing import List


async def insert_drone_order(drone_order: DroneOrder):
    '''
    Inserts the given drone_order into the table drone_order.
    '''
    await change('INSERT INTO drone_order VALUES (:id, :discord_id, :protocol, :finish_time)', vars(drone_order))


async def delete_drone_order(id: int):
    '''
    Deletes the drone_order with the given ID.
    '''
    await change('DELETE FROM drone_order WHERE id = :id', {'id': id})


async def fetch_all_drone_orders() -> List[DroneOrder]:
    '''
    Get all current drone_orders.
    '''
    return map_to_objects(await fetchall('SELECT * FROM drone_order'), DroneOrder)


async def get_order_by_drone_id(drone_id: str) -> DroneOrder | None:
    '''
    Gets current order if given drone has one.
    '''
    return map_to_object(await fetchone('SELECT drone_order.* FROM drone_order '
                                        'INNER JOIN drone ON drone.discord_id = drone_order.discord_id '
                                        'WHERE drone.drone_id = :drone_id', {'drone_id': drone_id}), DroneOrder)


async def delete_drone_order_by_drone_id(drone_id: str):
    '''
    Deletes the drone_order with the given drone_id.
    '''
    await change('DELETE FROM drone_order '
                 'INNER JOIN drone ON drone.discord_id = drone_order.discord_id '
                 'WHERE drone.drone_id = :drone_id', {'drone_id': drone_id})
