from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class GetMissionNameRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class GetMissionNameResponse(_message.Message):
    __slots__ = ("name",)
    NAME_FIELD_NUMBER: _ClassVar[int]
    name: str
    def __init__(self, name: _Optional[str] = ...) -> None: ...

class GetMissionFilenameRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class GetMissionFilenameResponse(_message.Message):
    __slots__ = ("name",)
    NAME_FIELD_NUMBER: _ClassVar[int]
    name: str
    def __init__(self, name: _Optional[str] = ...) -> None: ...

class GetMissionDescriptionRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class GetMissionDescriptionResponse(_message.Message):
    __slots__ = ("description",)
    DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
    description: str
    def __init__(self, description: _Optional[str] = ...) -> None: ...

class GetPausedRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class GetPausedResponse(_message.Message):
    __slots__ = ("paused",)
    PAUSED_FIELD_NUMBER: _ClassVar[int]
    paused: bool
    def __init__(self, paused: bool = ...) -> None: ...

class SetPausedRequest(_message.Message):
    __slots__ = ("paused",)
    PAUSED_FIELD_NUMBER: _ClassVar[int]
    paused: bool
    def __init__(self, paused: bool = ...) -> None: ...

class SetPausedResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class ReloadCurrentMissionRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class ReloadCurrentMissionResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class LoadNextMissionRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class LoadNextMissionResponse(_message.Message):
    __slots__ = ("loaded",)
    LOADED_FIELD_NUMBER: _ClassVar[int]
    loaded: bool
    def __init__(self, loaded: bool = ...) -> None: ...

class LoadMissionRequest(_message.Message):
    __slots__ = ("file_name",)
    FILE_NAME_FIELD_NUMBER: _ClassVar[int]
    file_name: str
    def __init__(self, file_name: _Optional[str] = ...) -> None: ...

class LoadMissionResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class StopMissionRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class StopMissionResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class EvalRequest(_message.Message):
    __slots__ = ("lua",)
    LUA_FIELD_NUMBER: _ClassVar[int]
    lua: str
    def __init__(self, lua: _Optional[str] = ...) -> None: ...

class EvalResponse(_message.Message):
    __slots__ = ("json",)
    JSON_FIELD_NUMBER: _ClassVar[int]
    json: str
    def __init__(self, json: _Optional[str] = ...) -> None: ...

class ExitProcessRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class ExitProcessResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class IsMultiplayerRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class IsMultiplayerResponse(_message.Message):
    __slots__ = ("multiplayer",)
    MULTIPLAYER_FIELD_NUMBER: _ClassVar[int]
    multiplayer: bool
    def __init__(self, multiplayer: bool = ...) -> None: ...

class IsServerRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class IsServerResponse(_message.Message):
    __slots__ = ("server",)
    SERVER_FIELD_NUMBER: _ClassVar[int]
    server: bool
    def __init__(self, server: bool = ...) -> None: ...

class BanPlayerRequest(_message.Message):
    __slots__ = ("id", "period", "reason")
    ID_FIELD_NUMBER: _ClassVar[int]
    PERIOD_FIELD_NUMBER: _ClassVar[int]
    REASON_FIELD_NUMBER: _ClassVar[int]
    id: int
    period: int
    reason: str
    def __init__(self, id: _Optional[int] = ..., period: _Optional[int] = ..., reason: _Optional[str] = ...) -> None: ...

class BanPlayerResponse(_message.Message):
    __slots__ = ("banned",)
    BANNED_FIELD_NUMBER: _ClassVar[int]
    banned: bool
    def __init__(self, banned: bool = ...) -> None: ...

class UnbanPlayerRequest(_message.Message):
    __slots__ = ("ucid",)
    UCID_FIELD_NUMBER: _ClassVar[int]
    ucid: str
    def __init__(self, ucid: _Optional[str] = ...) -> None: ...

class UnbanPlayerResponse(_message.Message):
    __slots__ = ("unbanned",)
    UNBANNED_FIELD_NUMBER: _ClassVar[int]
    unbanned: bool
    def __init__(self, unbanned: bool = ...) -> None: ...

class GetBannedPlayersRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class GetBannedPlayersResponse(_message.Message):
    __slots__ = ("bans",)
    BANS_FIELD_NUMBER: _ClassVar[int]
    bans: _containers.RepeatedCompositeFieldContainer[BanDetails]
    def __init__(self, bans: _Optional[_Iterable[_Union[BanDetails, _Mapping]]] = ...) -> None: ...

class BanDetails(_message.Message):
    __slots__ = ("ucid", "ip_address", "player_name", "reason", "banned_from", "banned_until")
    UCID_FIELD_NUMBER: _ClassVar[int]
    IP_ADDRESS_FIELD_NUMBER: _ClassVar[int]
    PLAYER_NAME_FIELD_NUMBER: _ClassVar[int]
    REASON_FIELD_NUMBER: _ClassVar[int]
    BANNED_FROM_FIELD_NUMBER: _ClassVar[int]
    BANNED_UNTIL_FIELD_NUMBER: _ClassVar[int]
    ucid: str
    ip_address: str
    player_name: str
    reason: str
    banned_from: int
    banned_until: int
    def __init__(self, ucid: _Optional[str] = ..., ip_address: _Optional[str] = ..., player_name: _Optional[str] = ..., reason: _Optional[str] = ..., banned_from: _Optional[int] = ..., banned_until: _Optional[int] = ...) -> None: ...

class GetUnitTypeRequest(_message.Message):
    __slots__ = ("id",)
    ID_FIELD_NUMBER: _ClassVar[int]
    id: str
    def __init__(self, id: _Optional[str] = ...) -> None: ...

class GetUnitTypeResponse(_message.Message):
    __slots__ = ("type",)
    TYPE_FIELD_NUMBER: _ClassVar[int]
    type: str
    def __init__(self, type: _Optional[str] = ...) -> None: ...

class GetRealTimeRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class GetRealTimeResponse(_message.Message):
    __slots__ = ("time",)
    TIME_FIELD_NUMBER: _ClassVar[int]
    time: float
    def __init__(self, time: _Optional[float] = ...) -> None: ...

class GetBallisticsCountRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class GetBallisticsCountResponse(_message.Message):
    __slots__ = ("count",)
    COUNT_FIELD_NUMBER: _ClassVar[int]
    count: int
    def __init__(self, count: _Optional[int] = ...) -> None: ...
