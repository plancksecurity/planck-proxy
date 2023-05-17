from dataclasses import dataclass
from typing import Any


@dataclass
class Message:
    """
    Dataclass for storing message information.
    """

    inmail: str = None  # inbound email
    inmail_parsed: Any = None  # pEp message containing the inbound email
    inmail_decrypted: str = None  # inbound email decrypted
    msgfrom: str = None  # inmail from address
    msgto: str = None  # inmail to address
