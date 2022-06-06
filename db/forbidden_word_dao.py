from typing import List

from db.database import fetchone, change, fetchall

from db.data_objects import ForbiddenWord, map_to_object, map_to_objects


def insert_forbidden_word(forbidden_word: ForbiddenWord):
    '''
    Inserts the given forbidden word into the table forbidden_word.
    '''
    change('INSERT INTO forbidden_word (id, regex) VALUES (:id, :regex)', vars(forbidden_word))


def fetch_forbidden_word_with_id(id: str) -> ForbiddenWord:
    '''
    Finds the forbidden word with the given id.
    '''
    return map_to_object(fetchone('SELECT * FROM forbidden_word WHERE id = :id', {'id': id}))


def get_all_forbidden_words() -> List[ForbiddenWord]:
    '''
    Finds all forbidden words.
    '''
    return map_to_objects(fetchall('SELECT * FROM forbidden_word', {}), ForbiddenWord)


def delete_forbidden_word_by_id(id: str):
    '''
    Deletes the forbidden word with the given ID.
    '''
    change('DELETE FROM forbidden_word WHERE id = :id', {'id': id})
