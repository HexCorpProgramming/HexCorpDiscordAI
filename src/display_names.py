from src.drone_member import DroneMember
from src.log import log


async def update_display_name(member: DroneMember):
    icon = '⬢' if member.drone.is_configured() else '⬡'

    new_display_name = f"{icon}-Drone #{member.drone.drone_id}"

    if member.display_name == new_display_name:
        # Return false if no update required.
        return False

    log.info(f"Updating drone display name. Old name: {member.display_name}. New name: {new_display_name}.")
    await member.edit(nick=new_display_name)
    return True
