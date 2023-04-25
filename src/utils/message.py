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


def init_person():
    """
    Initializes a dictionary for storing person information.

    Returns:
        dict: A dictionary with the following keys:
            - 'addr': None
            - 'key': None
            - 'keyname': None
            - 'keyaddr': None
            - 'keyfpr': None
            - 'pepid': None (pEp Identity)
    """

    return {
        "addr": None,
        "key": None,
        "keyname": None,
        "keyaddr": None,
        "keyfpr": None,
        "pepid": None,
    }


@dataclass
class Message:
    """
    Dataclass for storing message information.
    """

    msg: dict = field(default_factory=init_msg)
    us: dict = field(default_factory=init_person)
    them: dict = field(default_factory=init_person)
