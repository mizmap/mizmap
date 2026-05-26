from dcs.common.v0 import common_pb2 as _common_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class GetAirbasesRequest(_message.Message):
    __slots__ = ("coalition",)
    COALITION_FIELD_NUMBER: _ClassVar[int]
    coalition: _common_pb2.Coalition
    def __init__(self, coalition: _Optional[_Union[_common_pb2.Coalition, str]] = ...) -> None: ...

class GetAirbasesResponse(_message.Message):
    __slots__ = ("airbases",)
    AIRBASES_FIELD_NUMBER: _ClassVar[int]
    airbases: _containers.RepeatedCompositeFieldContainer[_common_pb2.Airbase]
    def __init__(self, airbases: _Optional[_Iterable[_Union[_common_pb2.Airbase, _Mapping]]] = ...) -> None: ...

class GetMarkPanelsRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class GetMarkPanelsResponse(_message.Message):
    __slots__ = ("mark_panels",)
    MARK_PANELS_FIELD_NUMBER: _ClassVar[int]
    mark_panels: _containers.RepeatedCompositeFieldContainer[_common_pb2.MarkPanel]
    def __init__(self, mark_panels: _Optional[_Iterable[_Union[_common_pb2.MarkPanel, _Mapping]]] = ...) -> None: ...

class GetTheatreRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class GetTheatreResponse(_message.Message):
    __slots__ = ("theatre",)
    THEATRE_FIELD_NUMBER: _ClassVar[int]
    theatre: str
    def __init__(self, theatre: _Optional[str] = ...) -> None: ...

class SearchObjectsRequest(_message.Message):
    __slots__ = ("categories", "volume")
    CATEGORIES_FIELD_NUMBER: _ClassVar[int]
    VOLUME_FIELD_NUMBER: _ClassVar[int]
    categories: _containers.RepeatedScalarFieldContainer[_common_pb2.ObjectCategory]
    volume: SearchVolume
    def __init__(self, categories: _Optional[_Iterable[_Union[_common_pb2.ObjectCategory, str]]] = ..., volume: _Optional[_Union[SearchVolume, _Mapping]] = ...) -> None: ...

class SearchObjectsResponse(_message.Message):
    __slots__ = ("objects",)
    OBJECTS_FIELD_NUMBER: _ClassVar[int]
    objects: _containers.RepeatedCompositeFieldContainer[_common_pb2.Target]
    def __init__(self, objects: _Optional[_Iterable[_Union[_common_pb2.Target, _Mapping]]] = ...) -> None: ...

class SearchVolume(_message.Message):
    __slots__ = ("sphere", "box", "segment", "pyramid")
    SPHERE_FIELD_NUMBER: _ClassVar[int]
    BOX_FIELD_NUMBER: _ClassVar[int]
    SEGMENT_FIELD_NUMBER: _ClassVar[int]
    PYRAMID_FIELD_NUMBER: _ClassVar[int]
    sphere: SphereVolume
    box: BoxVolume
    segment: SegmentVolume
    pyramid: PyramidVolume
    def __init__(self, sphere: _Optional[_Union[SphereVolume, _Mapping]] = ..., box: _Optional[_Union[BoxVolume, _Mapping]] = ..., segment: _Optional[_Union[SegmentVolume, _Mapping]] = ..., pyramid: _Optional[_Union[PyramidVolume, _Mapping]] = ...) -> None: ...

class SphereVolume(_message.Message):
    __slots__ = ("center", "radius")
    CENTER_FIELD_NUMBER: _ClassVar[int]
    RADIUS_FIELD_NUMBER: _ClassVar[int]
    center: _common_pb2.InputPosition
    radius: float
    def __init__(self, center: _Optional[_Union[_common_pb2.InputPosition, _Mapping]] = ..., radius: _Optional[float] = ...) -> None: ...

class BoxVolume(_message.Message):
    __slots__ = ("min", "max")
    MIN_FIELD_NUMBER: _ClassVar[int]
    MAX_FIELD_NUMBER: _ClassVar[int]
    min: _common_pb2.InputPosition
    max: _common_pb2.InputPosition
    def __init__(self, min: _Optional[_Union[_common_pb2.InputPosition, _Mapping]] = ..., max: _Optional[_Union[_common_pb2.InputPosition, _Mapping]] = ...) -> None: ...

class SegmentVolume(_message.Message):
    __slots__ = ("to",)
    FROM_FIELD_NUMBER: _ClassVar[int]
    TO_FIELD_NUMBER: _ClassVar[int]
    to: _common_pb2.InputPosition
    def __init__(self, to: _Optional[_Union[_common_pb2.InputPosition, _Mapping]] = ..., **kwargs) -> None: ...

class PyramidVolume(_message.Message):
    __slots__ = ("center", "forward", "right", "up", "length", "half_angle_horizontal", "half_angle_vertical")
    CENTER_FIELD_NUMBER: _ClassVar[int]
    FORWARD_FIELD_NUMBER: _ClassVar[int]
    RIGHT_FIELD_NUMBER: _ClassVar[int]
    UP_FIELD_NUMBER: _ClassVar[int]
    LENGTH_FIELD_NUMBER: _ClassVar[int]
    HALF_ANGLE_HORIZONTAL_FIELD_NUMBER: _ClassVar[int]
    HALF_ANGLE_VERTICAL_FIELD_NUMBER: _ClassVar[int]
    center: _common_pb2.InputPosition
    forward: _common_pb2.Vector
    right: _common_pb2.Vector
    up: _common_pb2.Vector
    length: float
    half_angle_horizontal: float
    half_angle_vertical: float
    def __init__(self, center: _Optional[_Union[_common_pb2.InputPosition, _Mapping]] = ..., forward: _Optional[_Union[_common_pb2.Vector, _Mapping]] = ..., right: _Optional[_Union[_common_pb2.Vector, _Mapping]] = ..., up: _Optional[_Union[_common_pb2.Vector, _Mapping]] = ..., length: _Optional[float] = ..., half_angle_horizontal: _Optional[float] = ..., half_angle_vertical: _Optional[float] = ...) -> None: ...
