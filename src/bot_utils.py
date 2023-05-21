import re
from typing import Optional

COMMAND_PREFIX = 'hc!'


def get_id(username: str) -> Optional[str]:
    '''
    Find the four digit ID in a nickname or None if no such ID is found.
    '''
    found = re.search(r"\d{4}", username)
    if found is None:
        return None
    else:
        return found.group()
