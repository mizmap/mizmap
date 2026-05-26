from dcs.common.v0 import common_pb2 as _common_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class LineType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    LINE_TYPE_NO_LINE: _ClassVar[LineType]
    LINE_TYPE_SOLID: _ClassVar[LineType]
    LINE_TYPE_DASHED: _ClassVar[LineType]
    LINE_TYPE_DOTTED: _ClassVar[LineType]
    LINE_TYPE_DOT_DASH: _ClassVar[LineType]
    LINE_TYPE_LONG_DASH: _ClassVar[LineType]
    LINE_TYPE_TWO_DASH: _ClassVar[LineType]

class Shape(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    SHAPE_UNSPECIFIED: _ClassVar[Shape]
    SHAPE_LINE: _ClassVar[Shape]
    SHAPE_CIRCLE: _ClassVar[Shape]
    SHAPE_RECT: _ClassVar[Shape]
    SHAPE_ARROW: _ClassVar[Shape]
    SHAPE_TEXT: _ClassVar[Shape]
    SHAPE_QUAD: _ClassVar[Shape]
    SHAPE_FREEFORM: _ClassVar[Shape]
LINE_TYPE_NO_LINE: LineType
LINE_TYPE_SOLID: LineType
LINE_TYPE_DASHED: LineType
LINE_TYPE_DOTTED: LineType
LINE_TYPE_DOT_DASH: LineType
LINE_TYPE_LONG_DASH: LineType
LINE_TYPE_TWO_DASH: LineType
SHAPE_UNSPECIFIED: Shape
SHAPE_LINE: Shape
SHAPE_CIRCLE: Shape
SHAPE_RECT: Shape
SHAPE_ARROW: Shape
SHAPE_TEXT: Shape
SHAPE_QUAD: Shape
SHAPE_FREEFORM: Shape

class OutTextRequest(_message.Message):
    __slots__ = ("text", "display_time", "clear_view")
    TEXT_FIELD_NUMBER: _ClassVar[int]
    DISPLAY_TIME_FIELD_NUMBER: _ClassVar[int]
    CLEAR_VIEW_FIELD_NUMBER: _ClassVar[int]
    text: str
    display_time: int
    clear_view: bool
    def __init__(self, text: _Optional[str] = ..., display_time: _Optional[int] = ..., clear_view: bool = ...) -> None: ...

class OutTextResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class OutTextForCoalitionRequest(_message.Message):
    __slots__ = ("text", "display_time", "clear_view", "coalition")
    TEXT_FIELD_NUMBER: _ClassVar[int]
    DISPLAY_TIME_FIELD_NUMBER: _ClassVar[int]
    CLEAR_VIEW_FIELD_NUMBER: _ClassVar[int]
    COALITION_FIELD_NUMBER: _ClassVar[int]
    text: str
    display_time: int
    clear_view: bool
    coalition: _common_pb2.Coalition
    def __init__(self, text: _Optional[str] = ..., display_time: _Optional[int] = ..., clear_view: bool = ..., coalition: _Optional[_Union[_common_pb2.Coalition, str]] = ...) -> None: ...

class OutTextForCoalitionResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class OutTextForGroupRequest(_message.Message):
    __slots__ = ("text", "display_time", "clear_view", "group_id")
    TEXT_FIELD_NUMBER: _ClassVar[int]
    DISPLAY_TIME_FIELD_NUMBER: _ClassVar[int]
    CLEAR_VIEW_FIELD_NUMBER: _ClassVar[int]
    GROUP_ID_FIELD_NUMBER: _ClassVar[int]
    text: str
    display_time: int
    clear_view: bool
    group_id: int
    def __init__(self, text: _Optional[str] = ..., display_time: _Optional[int] = ..., clear_view: bool = ..., group_id: _Optional[int] = ...) -> None: ...

class OutTextForGroupResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class OutTextForUnitRequest(_message.Message):
    __slots__ = ("text", "display_time", "clear_view", "unit_id")
    TEXT_FIELD_NUMBER: _ClassVar[int]
    DISPLAY_TIME_FIELD_NUMBER: _ClassVar[int]
    CLEAR_VIEW_FIELD_NUMBER: _ClassVar[int]
    UNIT_ID_FIELD_NUMBER: _ClassVar[int]
    text: str
    display_time: int
    clear_view: bool
    unit_id: int
    def __init__(self, text: _Optional[str] = ..., display_time: _Optional[int] = ..., clear_view: bool = ..., unit_id: _Optional[int] = ...) -> None: ...

class OutTextForUnitResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class GetUserFlagRequest(_message.Message):
    __slots__ = ("flag",)
    FLAG_FIELD_NUMBER: _ClassVar[int]
    flag: str
    def __init__(self, flag: _Optional[str] = ...) -> None: ...

class GetUserFlagResponse(_message.Message):
    __slots__ = ("value",)
    VALUE_FIELD_NUMBER: _ClassVar[int]
    value: int
    def __init__(self, value: _Optional[int] = ...) -> None: ...

class SetUserFlagRequest(_message.Message):
    __slots__ = ("flag", "value")
    FLAG_FIELD_NUMBER: _ClassVar[int]
    VALUE_FIELD_NUMBER: _ClassVar[int]
    flag: str
    value: int
    def __init__(self, flag: _Optional[str] = ..., value: _Optional[int] = ...) -> None: ...

class SetUserFlagResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class MarkToAllRequest(_message.Message):
    __slots__ = ("text", "position", "read_only", "message")
    TEXT_FIELD_NUMBER: _ClassVar[int]
    POSITION_FIELD_NUMBER: _ClassVar[int]
    READ_ONLY_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    text: str
    position: _common_pb2.InputPosition
    read_only: bool
    message: str
    def __init__(self, text: _Optional[str] = ..., position: _Optional[_Union[_common_pb2.InputPosition, _Mapping]] = ..., read_only: bool = ..., message: _Optional[str] = ...) -> None: ...

class MarkToAllResponse(_message.Message):
    __slots__ = ("id",)
    ID_FIELD_NUMBER: _ClassVar[int]
    id: int
    def __init__(self, id: _Optional[int] = ...) -> None: ...

class MarkToCoalitionRequest(_message.Message):
    __slots__ = ("id", "text", "position", "coalition", "read_only", "message")
    ID_FIELD_NUMBER: _ClassVar[int]
    TEXT_FIELD_NUMBER: _ClassVar[int]
    POSITION_FIELD_NUMBER: _ClassVar[int]
    COALITION_FIELD_NUMBER: _ClassVar[int]
    READ_ONLY_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    id: int
    text: str
    position: _common_pb2.InputPosition
    coalition: _common_pb2.Coalition
    read_only: bool
    message: str
    def __init__(self, id: _Optional[int] = ..., text: _Optional[str] = ..., position: _Optional[_Union[_common_pb2.InputPosition, _Mapping]] = ..., coalition: _Optional[_Union[_common_pb2.Coalition, str]] = ..., read_only: bool = ..., message: _Optional[str] = ...) -> None: ...

class MarkToCoalitionResponse(_message.Message):
    __slots__ = ("id",)
    ID_FIELD_NUMBER: _ClassVar[int]
    id: int
    def __init__(self, id: _Optional[int] = ...) -> None: ...

class MarkToGroupRequest(_message.Message):
    __slots__ = ("id", "text", "position", "group_id", "read_only", "message")
    ID_FIELD_NUMBER: _ClassVar[int]
    TEXT_FIELD_NUMBER: _ClassVar[int]
    POSITION_FIELD_NUMBER: _ClassVar[int]
    GROUP_ID_FIELD_NUMBER: _ClassVar[int]
    READ_ONLY_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    id: int
    text: str
    position: _common_pb2.InputPosition
    group_id: int
    read_only: bool
    message: str
    def __init__(self, id: _Optional[int] = ..., text: _Optional[str] = ..., position: _Optional[_Union[_common_pb2.InputPosition, _Mapping]] = ..., group_id: _Optional[int] = ..., read_only: bool = ..., message: _Optional[str] = ...) -> None: ...

class MarkToGroupResponse(_message.Message):
    __slots__ = ("id",)
    ID_FIELD_NUMBER: _ClassVar[int]
    id: int
    def __init__(self, id: _Optional[int] = ...) -> None: ...

class RemoveMarkRequest(_message.Message):
    __slots__ = ("id",)
    ID_FIELD_NUMBER: _ClassVar[int]
    id: int
    def __init__(self, id: _Optional[int] = ...) -> None: ...

class RemoveMarkResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class ExplosionRequest(_message.Message):
    __slots__ = ("position", "power")
    POSITION_FIELD_NUMBER: _ClassVar[int]
    POWER_FIELD_NUMBER: _ClassVar[int]
    position: _common_pb2.InputPosition
    power: int
    def __init__(self, position: _Optional[_Union[_common_pb2.InputPosition, _Mapping]] = ..., power: _Optional[int] = ...) -> None: ...

class ExplosionResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class SmokeRequest(_message.Message):
    __slots__ = ("position", "color")
    class SmokeColor(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        SMOKE_COLOR_UNSPECIFIED: _ClassVar[SmokeRequest.SmokeColor]
        SMOKE_COLOR_GREEN: _ClassVar[SmokeRequest.SmokeColor]
        SMOKE_COLOR_RED: _ClassVar[SmokeRequest.SmokeColor]
        SMOKE_COLOR_WHITE: _ClassVar[SmokeRequest.SmokeColor]
        SMOKE_COLOR_ORANGE: _ClassVar[SmokeRequest.SmokeColor]
        SMOKE_COLOR_BLUE: _ClassVar[SmokeRequest.SmokeColor]
    SMOKE_COLOR_UNSPECIFIED: SmokeRequest.SmokeColor
    SMOKE_COLOR_GREEN: SmokeRequest.SmokeColor
    SMOKE_COLOR_RED: SmokeRequest.SmokeColor
    SMOKE_COLOR_WHITE: SmokeRequest.SmokeColor
    SMOKE_COLOR_ORANGE: SmokeRequest.SmokeColor
    SMOKE_COLOR_BLUE: SmokeRequest.SmokeColor
    POSITION_FIELD_NUMBER: _ClassVar[int]
    COLOR_FIELD_NUMBER: _ClassVar[int]
    position: _common_pb2.InputPosition
    color: SmokeRequest.SmokeColor
    def __init__(self, position: _Optional[_Union[_common_pb2.InputPosition, _Mapping]] = ..., color: _Optional[_Union[SmokeRequest.SmokeColor, str]] = ...) -> None: ...

class SmokeResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class IlluminationBombRequest(_message.Message):
    __slots__ = ("position", "power")
    POSITION_FIELD_NUMBER: _ClassVar[int]
    POWER_FIELD_NUMBER: _ClassVar[int]
    position: _common_pb2.InputPosition
    power: int
    def __init__(self, position: _Optional[_Union[_common_pb2.InputPosition, _Mapping]] = ..., power: _Optional[int] = ...) -> None: ...

class IlluminationBombResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class SignalFlareRequest(_message.Message):
    __slots__ = ("position", "color", "azimuth")
    class FlareColor(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        FLARE_COLOR_UNSPECIFIED: _ClassVar[SignalFlareRequest.FlareColor]
        FLARE_COLOR_GREEN: _ClassVar[SignalFlareRequest.FlareColor]
        FLARE_COLOR_RED: _ClassVar[SignalFlareRequest.FlareColor]
        FLARE_COLOR_WHITE: _ClassVar[SignalFlareRequest.FlareColor]
        FLARE_COLOR_YELLOW: _ClassVar[SignalFlareRequest.FlareColor]
    FLARE_COLOR_UNSPECIFIED: SignalFlareRequest.FlareColor
    FLARE_COLOR_GREEN: SignalFlareRequest.FlareColor
    FLARE_COLOR_RED: SignalFlareRequest.FlareColor
    FLARE_COLOR_WHITE: SignalFlareRequest.FlareColor
    FLARE_COLOR_YELLOW: SignalFlareRequest.FlareColor
    POSITION_FIELD_NUMBER: _ClassVar[int]
    COLOR_FIELD_NUMBER: _ClassVar[int]
    AZIMUTH_FIELD_NUMBER: _ClassVar[int]
    position: _common_pb2.InputPosition
    color: SignalFlareRequest.FlareColor
    azimuth: int
    def __init__(self, position: _Optional[_Union[_common_pb2.InputPosition, _Mapping]] = ..., color: _Optional[_Union[SignalFlareRequest.FlareColor, str]] = ..., azimuth: _Optional[int] = ...) -> None: ...

class SignalFlareResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class Color(_message.Message):
    __slots__ = ("red", "green", "blue", "alpha")
    RED_FIELD_NUMBER: _ClassVar[int]
    GREEN_FIELD_NUMBER: _ClassVar[int]
    BLUE_FIELD_NUMBER: _ClassVar[int]
    ALPHA_FIELD_NUMBER: _ClassVar[int]
    red: float
    green: float
    blue: float
    alpha: float
    def __init__(self, red: _Optional[float] = ..., green: _Optional[float] = ..., blue: _Optional[float] = ..., alpha: _Optional[float] = ...) -> None: ...

class MarkupToAllRequest(_message.Message):
    __slots__ = ("shape", "points", "border_color", "fill_color", "line_type", "read_only", "message")
    SHAPE_FIELD_NUMBER: _ClassVar[int]
    POINTS_FIELD_NUMBER: _ClassVar[int]
    BORDER_COLOR_FIELD_NUMBER: _ClassVar[int]
    FILL_COLOR_FIELD_NUMBER: _ClassVar[int]
    LINE_TYPE_FIELD_NUMBER: _ClassVar[int]
    READ_ONLY_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    shape: Shape
    points: _containers.RepeatedCompositeFieldContainer[_common_pb2.InputPosition]
    border_color: Color
    fill_color: Color
    line_type: LineType
    read_only: bool
    message: str
    def __init__(self, shape: _Optional[_Union[Shape, str]] = ..., points: _Optional[_Iterable[_Union[_common_pb2.InputPosition, _Mapping]]] = ..., border_color: _Optional[_Union[Color, _Mapping]] = ..., fill_color: _Optional[_Union[Color, _Mapping]] = ..., line_type: _Optional[_Union[LineType, str]] = ..., read_only: bool = ..., message: _Optional[str] = ...) -> None: ...

class MarkupToAllResponse(_message.Message):
    __slots__ = ("id",)
    ID_FIELD_NUMBER: _ClassVar[int]
    id: int
    def __init__(self, id: _Optional[int] = ...) -> None: ...

class MarkupToCoalitionRequest(_message.Message):
    __slots__ = ("shape", "coalition", "points", "border_color", "fill_color", "line_type", "read_only", "message")
    SHAPE_FIELD_NUMBER: _ClassVar[int]
    COALITION_FIELD_NUMBER: _ClassVar[int]
    POINTS_FIELD_NUMBER: _ClassVar[int]
    BORDER_COLOR_FIELD_NUMBER: _ClassVar[int]
    FILL_COLOR_FIELD_NUMBER: _ClassVar[int]
    LINE_TYPE_FIELD_NUMBER: _ClassVar[int]
    READ_ONLY_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    shape: Shape
    coalition: _common_pb2.Coalition
    points: _containers.RepeatedCompositeFieldContainer[_common_pb2.InputPosition]
    border_color: Color
    fill_color: Color
    line_type: LineType
    read_only: bool
    message: str
    def __init__(self, shape: _Optional[_Union[Shape, str]] = ..., coalition: _Optional[_Union[_common_pb2.Coalition, str]] = ..., points: _Optional[_Iterable[_Union[_common_pb2.InputPosition, _Mapping]]] = ..., border_color: _Optional[_Union[Color, _Mapping]] = ..., fill_color: _Optional[_Union[Color, _Mapping]] = ..., line_type: _Optional[_Union[LineType, str]] = ..., read_only: bool = ..., message: _Optional[str] = ...) -> None: ...

class MarkupToCoalitionResponse(_message.Message):
    __slots__ = ("id",)
    ID_FIELD_NUMBER: _ClassVar[int]
    id: int
    def __init__(self, id: _Optional[int] = ...) -> None: ...
