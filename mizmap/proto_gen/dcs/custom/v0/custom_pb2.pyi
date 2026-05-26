from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Optional as _Optional

DESCRIPTOR: _descriptor.FileDescriptor

class RequestMissionAssignmentRequest(_message.Message):
    __slots__ = ("unit_name", "mission_type")
    UNIT_NAME_FIELD_NUMBER: _ClassVar[int]
    MISSION_TYPE_FIELD_NUMBER: _ClassVar[int]
    unit_name: str
    mission_type: str
    def __init__(self, unit_name: _Optional[str] = ..., mission_type: _Optional[str] = ...) -> None: ...

class RequestMissionAssignmentResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class JoinMissionRequest(_message.Message):
    __slots__ = ("unit_name", "mission_code")
    UNIT_NAME_FIELD_NUMBER: _ClassVar[int]
    MISSION_CODE_FIELD_NUMBER: _ClassVar[int]
    unit_name: str
    mission_code: int
    def __init__(self, unit_name: _Optional[str] = ..., mission_code: _Optional[int] = ...) -> None: ...

class JoinMissionResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class AbortMissionRequest(_message.Message):
    __slots__ = ("unit_name",)
    UNIT_NAME_FIELD_NUMBER: _ClassVar[int]
    unit_name: str
    def __init__(self, unit_name: _Optional[str] = ...) -> None: ...

class AbortMissionResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class GetMissionStatusRequest(_message.Message):
    __slots__ = ("unit_name",)
    UNIT_NAME_FIELD_NUMBER: _ClassVar[int]
    unit_name: str
    def __init__(self, unit_name: _Optional[str] = ...) -> None: ...

class GetMissionStatusResponse(_message.Message):
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

class GetMagneticDeclinationRequest(_message.Message):
    __slots__ = ("lat", "lon", "alt")
    LAT_FIELD_NUMBER: _ClassVar[int]
    LON_FIELD_NUMBER: _ClassVar[int]
    ALT_FIELD_NUMBER: _ClassVar[int]
    lat: float
    lon: float
    alt: float
    def __init__(self, lat: _Optional[float] = ..., lon: _Optional[float] = ..., alt: _Optional[float] = ...) -> None: ...

class GetMagneticDeclinationResponse(_message.Message):
    __slots__ = ("declination",)
    DECLINATION_FIELD_NUMBER: _ClassVar[int]
    declination: float
    def __init__(self, declination: _Optional[float] = ...) -> None: ...
