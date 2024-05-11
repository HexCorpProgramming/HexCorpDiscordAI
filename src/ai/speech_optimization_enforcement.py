from src.ai.speech_optimization import StatusType, get_status_type
from src.channels import (MODERATION_CATEGORY, MODERATION_CHANNEL, MODERATION_LOG,
                          ORDERS_COMPLETION, ORDERS_REPORTING, REPETITIONS)
from src.resources import HEXCORP_MANTRA
from src.log import log
from src.drone_member import DroneMember

CHANNEL_BLACKLIST = [ORDERS_REPORTING, ORDERS_COMPLETION, MODERATION_CHANNEL, MODERATION_LOG]
CATEGORY_BLACKLIST = [MODERATION_CATEGORY]


async def enforce_speech_optimization(message, message_copy):
    '''
    This function assesses messages from optimized drones to see if they are acceptable.
    Any message from an optimized drone that is not a plain status code ("5890 :: 200") is deleted.
    Regardless of validity, message attachments are always stripped from optimized drones.
    Function will return early if blacklist conditions are met (ignore specific channel + mantra channel if message is correct mantra).
    '''

    member = await DroneMember.create(message.author)

    if not member.drone or not member.drone.optimized:
        # Message author is not an optimized drone. Skip.
        return False

    # Check if message is in any blacklists (specific channels + mantra channel if message is correct mantra).
    acceptable_mantra = f"{member.drone.drone_id} :: {HEXCORP_MANTRA}"
    if any([
        (message.channel.name == REPETITIONS and message_copy.content == acceptable_mantra),
        (message.channel.name in (ORDERS_REPORTING, ORDERS_COMPLETION, MODERATION_CHANNEL, MODERATION_LOG)),
        (message.channel.category.name == MODERATION_CATEGORY)
    ]):
        log.debug("Skipping enforced optimization in blacklisted channel.")
        return False

    # Strip message attachments of optimized drone.
    message_copy.attachments = []

    status_type, _, _ = get_status_type(message_copy.content)

    if status_type not in (StatusType.PLAIN, StatusType.ADDRESS_BY_ID_PLAIN) or status_type == StatusType.NONE:
        log.info(f"Optimized drone {member.drone.drone_id} has posted an informative or otherwise inappropriate status message. Deleting.")
        # Optimized drone posted an informative status message. Delete.
        await message.delete()
        return True

    # Message has not been found to violate any rules.
    return False
