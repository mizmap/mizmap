from dcs.common.v0 import common_pb2 as _common_pb2
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class GetWindRequest(_message.Message):
    __slots__ = ("position",)
    POSITION_FIELD_NUMBER: _ClassVar[int]
    position: _common_pb2.InputPosition
    def __init__(self, position: _Optional[_Union[_common_pb2.InputPosition, _Mapping]] = ...) -> None: ...

class GetWindResponse(_message.Message):
    __slots__ = ("heading", "strength")
    HEADING_FIELD_NUMBER: _ClassVar[int]
    STRENGTH_FIELD_NUMBER: _ClassVar[int]
    heading: float
    strength: float
    def __init__(self, heading: _Optional[float] = ..., strength: _Optional[float] = ...) -> None: ...

class GetWindWithTurbulenceRequest(_message.Message):
    __slots__ = ("position",)
    POSITION_FIELD_NUMBER: _ClassVar[int]
    position: _common_pb2.InputPosition
    def __init__(self, position: _Optional[_Union[_common_pb2.InputPosition, _Mapping]] = ...) -> None: ...

class GetWindWithTurbulenceResponse(_message.Message):
    __slots__ = ("heading", "strength")
    HEADING_FIELD_NUMBER: _ClassVar[int]
    STRENGTH_FIELD_NUMBER: _ClassVar[int]
    heading: float
    strength: float
    def __init__(self, heading: _Optional[float] = ..., strength: _Optional[float] = ...) -> None: ...

class GetTemperatureAndPressureRequest(_message.Message):
    __slots__ = ("position",)
    POSITION_FIELD_NUMBER: _ClassVar[int]
    position: _common_pb2.InputPosition
    def __init__(self, position: _Optional[_Union[_common_pb2.InputPosition, _Mapping]] = ...) -> None: ...

class GetTemperatureAndPressureResponse(_message.Message):
    __slots__ = ("temperature", "pressure")
    TEMPERATURE_FIELD_NUMBER: _ClassVar[int]
    PRESSURE_FIELD_NUMBER: _ClassVar[int]
    temperature: float
    pressure: float
    def __init__(self, temperature: _Optional[float] = ..., pressure: _Optional[float] = ...) -> None: ...
