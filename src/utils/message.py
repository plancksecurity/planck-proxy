from dataclasses import dataclass, field


def init_msg():
    """
    Initializes a dictionary for storing message information.

    Returns:
        dict: A dictionary with the following keys:
            - 'inmail': None
            - 'msgfrom': None
            - 'msgto': None
            - 'src': None (pEp Message)
            - 'dst': None (pEp Message)
    """
    return {
        "inmail": None,
        "msgfrom": None,
        "msgto": None,
        "src": None,
        "dst": None,
    }


@dataclass
class Message:
    """
    Dataclass for storing message information.
    """

    msg: dict = field(default_factory=init_msg)
