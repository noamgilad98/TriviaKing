


class Config:
    UDP_PORT = 13117
    MAGIC_COOKIE = b'\xab\xcd\xdc\xba'
    OFFER_MESSAGE_TYPE = b'\x02'
    SERVER_NAME = 'Mystic'
    GAME_START_DELAY = 4  # in seconds
    TCP_PORT_RANGE = (1025, 65535)  # Allowable range for TCP port