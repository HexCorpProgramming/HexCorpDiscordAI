from db.drone_dao import is_optimized
from ai.speech_optimization import status_code_regex, get_status_type, StatusType


async def enforce_speech_optimization(message, message_copy=None):
    '''
    This function assesses messages from optimized drones to see if they are acceptable.
    Any message from an optimized drone that is not a plain status code ("5890 :: 200") is deleted.
    Regardless of validity, message attachments are always stripped from optimized drones.
    '''

    if not is_optimized(message.author):
        # Message author is not an optimized drone. Skip.
        return False
    else:
        # Drone is forcibly optimized. Strip their message attachments.
        message_copy.attachments = []

    status_message = status_code_regex.match(message_copy.content)

    if status_message is None:
        # Optimized drone has posted a non-status message. Delete.
        await message.delete()
        return True

    if get_status_type(status_message) not in (StatusType.PLAIN, StatusType.ADDRESS_BY_ID_PLAIN):
        # Optimized drone posted an informative status message. Delete.
        await message.delete()
        return True

    # Message has not been found to violate any rules.
    return False
