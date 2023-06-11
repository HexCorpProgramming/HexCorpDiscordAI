from src.db.database import fetchall, change, fetchone
from src.db.data_objects import DroneOrder, map_to_objects, map_to_object

from typing import List


def insert_drone_order(drone_order: DroneOrder):
    '''
    Inserts the given drone_order into the table drone_order.
    '''
    change('INSERT INTO drone_order VALUES (:id, :drone_id, :protocol, :finish_time)', vars(drone_order))


def delete_drone_order(id: int):
    '''
    Deletes the drone_order with the given ID.
    '''
    change('DELETE FROM drone_order WHERE id = :id', {'id': id})


def fetch_all_drone_orders() -> List[DroneOrder]:
    '''
    Get all current drone_orders.
    '''
    return map_to_objects(fetchall('SELECT id, drone_id, protocol, finish_time FROM drone_order', {}), DroneOrder)


def get_order_by_drone_id(drone_id: str) -> DroneOrder:
    '''
    Gets current order if given drone has one.
    '''
    return map_to_object(fetchone('SELECT protocol FROM drone_order WHERE drone_id = :drone_id', {'drone_id': drone_id}), DroneOrder)


def delete_drone_order_by_drone_id(drone_id: str):
    '''
    Deletes the drone_order with the given drone_id.
    '''
    change('DELETE FROM drone_order WHERE drone_id = :drone_id', {'drone_id': drone_id})
