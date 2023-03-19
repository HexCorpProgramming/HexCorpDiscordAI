from typing import Iterable, Optional
from discord import Attachment, Asset, Reaction


class MessageCopy:
    '''
    This class is instantiated at the start of the on_message chain in main.py.
    It copies all important attributes required to proxy a message.
    At the end of the on_message chain, the message original and message copy are compared.
    If they are not identical, the original is deleted and the copy is proxied via webhook.
    '''
    def __init__(
        self,
        content: Optional[str] = None,
        display_name: Optional[str] = None,
        avatar: Optional[Asset] = None,
        identity_enforced: bool = False,
        attachments: Iterable[Attachment] = [],
        reactions: Iterable[Reaction] = []
    ):
        self.content = content
        self.display_name = display_name
        self.avatar = avatar
        self.identity_enforced = identity_enforced
        self.attachments = attachments
        self.reactions = reactions
