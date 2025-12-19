from enum import Enum


class TicketStatus(str, Enum):
    WAITING_MANAGER = "WAITING_MANAGER"
    ASSIGNED = "ASSIGNED"
    CLOSED = "CLOSED"


class MessageRole(str, Enum):
    USER = "USER"
    MANAGER = "MANAGER"
    BOT = "BOT"


class MessageType(str, Enum):
    TEXT = "TEXT"
    PHOTO = "PHOTO"
    VIDEO = "VIDEO"
    VOICE = "VOICE"
    AUDIO = "AUDIO"
    DOCUMENT = "DOCUMENT"
    STICKER = "STICKER"
    CONTACT = "CONTACT"
    LOCATION = "LOCATION"
    UNKNOWN = "UNKNOWN"
