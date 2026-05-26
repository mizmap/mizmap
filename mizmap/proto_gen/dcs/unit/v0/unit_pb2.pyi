from dcs.common.v0 import common_pb2 as _common_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class GetRadarRequest(_message.Message):
    __slots__ = ("name",)
    NAME_FIELD_NUMBER: _ClassVar[int]
    name: str
    def __init__(self, name: _Optional[str] = ...) -> None: ...

class GetRadarResponse(_message.Message):
    __slots__ = ("active", "target")
    ACTIVE_FIELD_NUMBER: _ClassVar[int]
    TARGET_FIELD_NUMBER: _ClassVar[int]
    active: bool
    target: _common_pb2.Target
    def __init__(self, active: bool = ..., target: _Optional[_Union[_common_pb2.Target, _Mapping]] = ...) -> None: ...

class GetPositionRequest(_message.Message):
    __slots__ = ("name",)
    NAME_FIELD_NUMBER: _ClassVar[int]
    name: str
    def __init__(self, name: _Optional[str] = ...) -> None: ...

class GetPositionResponse(_message.Message):
    __slots__ = ("position",)
    POSITION_FIELD_NUMBER: _ClassVar[int]
    position: _common_pb2.Position
    def __init__(self, position: _Optional[_Union[_common_pb2.Position, _Mapping]] = ...) -> None: ...

class GetDrawArgumentValueRequest(_message.Message):
    __slots__ = ("name", "argument")
    NAME_FIELD_NUMBER: _ClassVar[int]
    ARGUMENT_FIELD_NUMBER: _ClassVar[int]
    name: str
    argument: int
    def __init__(self, name: _Optional[str] = ..., argument: _Optional[int] = ...) -> None: ...

class GetDrawArgumentValueResponse(_message.Message):
    __slots__ = ("value",)
    VALUE_FIELD_NUMBER: _ClassVar[int]
    value: float
    def __init__(self, value: _Optional[float] = ...) -> None: ...

class GetTransformRequest(_message.Message):
    __slots__ = ("name",)
    NAME_FIELD_NUMBER: _ClassVar[int]
    name: str
    def __init__(self, name: _Optional[str] = ...) -> None: ...

class GetTransformResponse(_message.Message):
    __slots__ = ("time", "position", "orientation", "velocity")
    TIME_FIELD_NUMBER: _ClassVar[int]
    POSITION_FIELD_NUMBER: _ClassVar[int]
    ORIENTATION_FIELD_NUMBER: _ClassVar[int]
    VELOCITY_FIELD_NUMBER: _ClassVar[int]
    time: float
    position: _common_pb2.Position
    orientation: _common_pb2.Orientation
    velocity: _common_pb2.Velocity
    def __init__(self, time: _Optional[float] = ..., position: _Optional[_Union[_common_pb2.Position, _Mapping]] = ..., orientation: _Optional[_Union[_common_pb2.Orientation, _Mapping]] = ..., velocity: _Optional[_Union[_common_pb2.Velocity, _Mapping]] = ...) -> None: ...

class GetPlayerNameRequest(_message.Message):
    __slots__ = ("name",)
    NAME_FIELD_NUMBER: _ClassVar[int]
    name: str
    def __init__(self, name: _Optional[str] = ...) -> None: ...

class GetPlayerNameResponse(_message.Message):
    __slots__ = ("player_name",)
    PLAYER_NAME_FIELD_NUMBER: _ClassVar[int]
    player_name: str
    def __init__(self, player_name: _Optional[str] = ...) -> None: ...

class GetDescriptorRequest(_message.Message):
    __slots__ = ("name",)
    NAME_FIELD_NUMBER: _ClassVar[int]
    name: str
    def __init__(self, name: _Optional[str] = ...) -> None: ...

class GetDescriptorResponse(_message.Message):
    __slots__ = ("attributes",)
    ATTRIBUTES_FIELD_NUMBER: _ClassVar[int]
    attributes: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, attributes: _Optional[_Iterable[str]] = ...) -> None: ...

class SetEmissionRequest(_message.Message):
    __slots__ = ("name", "emitting")
    NAME_FIELD_NUMBER: _ClassVar[int]
    EMITTING_FIELD_NUMBER: _ClassVar[int]
    name: str
    emitting: bool
    def __init__(self, name: _Optional[str] = ..., emitting: bool = ...) -> None: ...

class SetEmissionResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class GetRequest(_message.Message):
    __slots__ = ("name",)
    NAME_FIELD_NUMBER: _ClassVar[int]
    name: str
    def __init__(self, name: _Optional[str] = ...) -> None: ...

class GetResponse(_message.Message):
    __slots__ = ("unit",)
    UNIT_FIELD_NUMBER: _ClassVar[int]
    unit: _common_pb2.Unit
    def __init__(self, unit: _Optional[_Union[_common_pb2.Unit, _Mapping]] = ...) -> None: ...

class DestroyRequest(_message.Message):
    __slots__ = ("name",)
    NAME_FIELD_NUMBER: _ClassVar[int]
    name: str
    def __init__(self, name: _Optional[str] = ...) -> None: ...

class DestroyResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...
