from dcs.common.v0 import common_pb2 as _common_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class SendChatToRequest(_message.Message):
    __slots__ = ("message", "target_player_id")
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    TARGET_PLAYER_ID_FIELD_NUMBER: _ClassVar[int]
    message: str
    target_player_id: int
    def __init__(self, message: _Optional[str] = ..., target_player_id: _Optional[int] = ...) -> None: ...

class SendChatToResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class SendChatRequest(_message.Message):
    __slots__ = ("message", "coalition")
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    COALITION_FIELD_NUMBER: _ClassVar[int]
    message: str
    coalition: _common_pb2.Coalition
    def __init__(self, message: _Optional[str] = ..., coalition: _Optional[_Union[_common_pb2.Coalition, str]] = ...) -> None: ...

class SendChatResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class GetPlayersRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class GetPlayersResponse(_message.Message):
    __slots__ = ("players",)
    class GetPlayerInfo(_message.Message):
        __slots__ = ("id", "name", "coalition", "slot", "ping", "remote_address", "ucid", "locale")
        ID_FIELD_NUMBER: _ClassVar[int]
        NAME_FIELD_NUMBER: _ClassVar[int]
        COALITION_FIELD_NUMBER: _ClassVar[int]
        SLOT_FIELD_NUMBER: _ClassVar[int]
        PING_FIELD_NUMBER: _ClassVar[int]
        REMOTE_ADDRESS_FIELD_NUMBER: _ClassVar[int]
        UCID_FIELD_NUMBER: _ClassVar[int]
        LOCALE_FIELD_NUMBER: _ClassVar[int]
        id: int
        name: str
        coalition: _common_pb2.Coalition
        slot: str
        ping: int
        remote_address: str
        ucid: str
        locale: str
        def __init__(self, id: _Optional[int] = ..., name: _Optional[str] = ..., coalition: _Optional[_Union[_common_pb2.Coalition, str]] = ..., slot: _Optional[str] = ..., ping: _Optional[int] = ..., remote_address: _Optional[str] = ..., ucid: _Optional[str] = ..., locale: _Optional[str] = ...) -> None: ...
    PLAYERS_FIELD_NUMBER: _ClassVar[int]
    players: _containers.RepeatedCompositeFieldContainer[GetPlayersResponse.GetPlayerInfo]
    def __init__(self, players: _Optional[_Iterable[_Union[GetPlayersResponse.GetPlayerInfo, _Mapping]]] = ...) -> None: ...

class ForcePlayerSlotRequest(_message.Message):
    __slots__ = ("player_id", "coalition", "slot_id")
    PLAYER_ID_FIELD_NUMBER: _ClassVar[int]
    COALITION_FIELD_NUMBER: _ClassVar[int]
    SLOT_ID_FIELD_NUMBER: _ClassVar[int]
    player_id: int
    coalition: _common_pb2.Coalition
    slot_id: str
    def __init__(self, player_id: _Optional[int] = ..., coalition: _Optional[_Union[_common_pb2.Coalition, str]] = ..., slot_id: _Optional[str] = ...) -> None: ...

class ForcePlayerSlotResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class KickPlayerRequest(_message.Message):
    __slots__ = ("id", "message")
    ID_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    id: int
    message: str
    def __init__(self, id: _Optional[int] = ..., message: _Optional[str] = ...) -> None: ...

class KickPlayerResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...
