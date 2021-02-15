from db.drone_dao import is_optimized
from ai.speech_optimization import status_code_regex, get_status_type, StatusType
from channels import ORDERS_REPORTING, ORDERS_COMPLETION, MODERATION_CHANNEL, MODERATION_LOG, MODERATION_CATEGORY, REPETITIONS
from ai.mantras import Mantra_Handler
from bot_utils import get_id
import logging

CHANNEL_BLACKLIST = [ORDERS_REPORTING, ORDERS_COMPLETION, MODERATION_CHANNEL, MODERATION_LOG]
CATEGORY_BLACKLIST = [MODERATION_CATEGORY]

LOGGER = logging.getLogger('ai')


async def enforce_speech_optimization(message, message_copy):
    '''
    This function assesses messages from optimized drones to see if they are acceptable.
    Any message from an optimized drone that is not a plain status code ("5890 :: 200") is deleted.
    Regardless of validity, message attachments are always stripped from optimized drones.
    Function will return early if blacklist conditions are met (ignore specific channel + mantra channel if message is correct mantra).
    '''

    if not is_optimized(message.author):
        # Message author is not an optimized drone. Skip.
        return False

    # Check if message is in any blacklists (specific channels + mantra channel if message is correct mantra).
    drone_id = get_id(message.author.display_name)
    acceptable_mantra = f"{drone_id} :: {Mantra_Handler.current_mantra}"
    LOGGER.info(f"Acceptable mantra:\n{acceptable_mantra}")
    LOGGER.info(f"Message:\n{message_copy.content}")
    if any([
        (message.channel.name == REPETITIONS and message_copy.content == acceptable_mantra),
        (message.channel.name in (ORDERS_REPORTING, ORDERS_COMPLETION, MODERATION_CHANNEL, MODERATION_LOG)),
        (message.channel.category.name == MODERATION_CATEGORY)
    ]):
        LOGGER.info("Skipping enforced optimization in blacklisted channel.")
        return False

    # Strip message attachments of optimized drone.
    message_copy.attachments = []

    # Check for status message.
    status_message = status_code_regex.match(message_copy.content)

    if status_message is None:
        # Optimized drone has posted a non-status message. Delete.
        LOGGER.info("Optimized drone posted non-status code message. Deleting.")
        await message.delete()
        return True

    if get_status_type(status_message) not in (StatusType.PLAIN, StatusType.ADDRESS_BY_ID_PLAIN):
        LOGGER.info("Optimized drone has posted an informative status message. Deleting.")
        # Optimized drone posted an informative status message. Delete.
        await message.delete()
        return True

    # Message has not been found to violate any rules.
    return False
