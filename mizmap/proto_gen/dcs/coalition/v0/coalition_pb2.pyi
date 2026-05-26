from dcs.common.v0 import common_pb2 as _common_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class AddGroupRequest(_message.Message):
    __slots__ = ("country", "group_category", "ground_template", "ship_template", "helicopter_template", "plane_template")
    class Skill(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        SKILL_RANDOM: _ClassVar[AddGroupRequest.Skill]
        SKILL_AVERAGE: _ClassVar[AddGroupRequest.Skill]
        SKILL_GOOD: _ClassVar[AddGroupRequest.Skill]
        SKILL_HIGH: _ClassVar[AddGroupRequest.Skill]
        SKILL_EXCELLENT: _ClassVar[AddGroupRequest.Skill]
        SKILL_PLAYER: _ClassVar[AddGroupRequest.Skill]
    SKILL_RANDOM: AddGroupRequest.Skill
    SKILL_AVERAGE: AddGroupRequest.Skill
    SKILL_GOOD: AddGroupRequest.Skill
    SKILL_HIGH: AddGroupRequest.Skill
    SKILL_EXCELLENT: AddGroupRequest.Skill
    SKILL_PLAYER: AddGroupRequest.Skill
    class GroundGroupTemplate(_message.Message):
        __slots__ = ("group_id", "hidden", "late_activation", "name", "position", "waypoints", "start_time", "task", "task_selected", "tasks", "uncontrollable", "units", "visible")
        GROUP_ID_FIELD_NUMBER: _ClassVar[int]
        HIDDEN_FIELD_NUMBER: _ClassVar[int]
        LATE_ACTIVATION_FIELD_NUMBER: _ClassVar[int]
        NAME_FIELD_NUMBER: _ClassVar[int]
        POSITION_FIELD_NUMBER: _ClassVar[int]
        WAYPOINTS_FIELD_NUMBER: _ClassVar[int]
        START_TIME_FIELD_NUMBER: _ClassVar[int]
        TASK_FIELD_NUMBER: _ClassVar[int]
        TASK_SELECTED_FIELD_NUMBER: _ClassVar[int]
        TASKS_FIELD_NUMBER: _ClassVar[int]
        UNCONTROLLABLE_FIELD_NUMBER: _ClassVar[int]
        UNITS_FIELD_NUMBER: _ClassVar[int]
        VISIBLE_FIELD_NUMBER: _ClassVar[int]
        group_id: int
        hidden: bool
        late_activation: bool
        name: str
        position: _common_pb2.InputPosition
        waypoints: _containers.RepeatedCompositeFieldContainer[AddGroupRequest.Point]
        start_time: int
        task: str
        task_selected: bool
        tasks: _containers.RepeatedCompositeFieldContainer[AddGroupRequest.Task]
        uncontrollable: bool
        units: _containers.RepeatedCompositeFieldContainer[AddGroupRequest.GroundUnitTemplate]
        visible: bool
        def __init__(self, group_id: _Optional[int] = ..., hidden: bool = ..., late_activation: bool = ..., name: _Optional[str] = ..., position: _Optional[_Union[_common_pb2.InputPosition, _Mapping]] = ..., waypoints: _Optional[_Iterable[_Union[AddGroupRequest.Point, _Mapping]]] = ..., start_time: _Optional[int] = ..., task: _Optional[str] = ..., task_selected: bool = ..., tasks: _Optional[_Iterable[_Union[AddGroupRequest.Task, _Mapping]]] = ..., uncontrollable: bool = ..., units: _Optional[_Iterable[_Union[AddGroupRequest.GroundUnitTemplate, _Mapping]]] = ..., visible: bool = ...) -> None: ...
    class GroundUnitTemplate(_message.Message):
        __slots__ = ("name", "type", "position", "unit_id", "heading", "skill")
        NAME_FIELD_NUMBER: _ClassVar[int]
        TYPE_FIELD_NUMBER: _ClassVar[int]
        POSITION_FIELD_NUMBER: _ClassVar[int]
        UNIT_ID_FIELD_NUMBER: _ClassVar[int]
        HEADING_FIELD_NUMBER: _ClassVar[int]
        SKILL_FIELD_NUMBER: _ClassVar[int]
        name: str
        type: str
        position: _common_pb2.InputPosition
        unit_id: int
        heading: int
        skill: AddGroupRequest.Skill
        def __init__(self, name: _Optional[str] = ..., type: _Optional[str] = ..., position: _Optional[_Union[_common_pb2.InputPosition, _Mapping]] = ..., unit_id: _Optional[int] = ..., heading: _Optional[int] = ..., skill: _Optional[_Union[AddGroupRequest.Skill, str]] = ...) -> None: ...
    class ShipGroupTemplate(_message.Message):
        __slots__ = ()
        def __init__(self) -> None: ...
    class ShipUnitTemplate(_message.Message):
        __slots__ = ()
        def __init__(self) -> None: ...
    class HelicopterGroupTemplate(_message.Message):
        __slots__ = ()
        def __init__(self) -> None: ...
    class HelicopterUnitTemplate(_message.Message):
        __slots__ = ()
        def __init__(self) -> None: ...
    class PlaneGroupTemplate(_message.Message):
        __slots__ = ()
        def __init__(self) -> None: ...
    class PlaneUnitTemplate(_message.Message):
        __slots__ = ()
        def __init__(self) -> None: ...
    class Point(_message.Message):
        __slots__ = ("position", "altitude_type", "type", "action", "form", "speed")
        class AltitudeType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
            __slots__ = ()
            ALTITUDE_TYPE_UNSPECIFIED: _ClassVar[AddGroupRequest.Point.AltitudeType]
            ALTITUDE_TYPE_BAROMETRIC: _ClassVar[AddGroupRequest.Point.AltitudeType]
            ALTITUDE_TYPE_RADIO: _ClassVar[AddGroupRequest.Point.AltitudeType]
        ALTITUDE_TYPE_UNSPECIFIED: AddGroupRequest.Point.AltitudeType
        ALTITUDE_TYPE_BAROMETRIC: AddGroupRequest.Point.AltitudeType
        ALTITUDE_TYPE_RADIO: AddGroupRequest.Point.AltitudeType
        class PointType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
            __slots__ = ()
            POINT_TYPE_RANDOM: _ClassVar[AddGroupRequest.Point.PointType]
            POINT_TYPE_TAKEOFF: _ClassVar[AddGroupRequest.Point.PointType]
            POINT_TYPE_TAKEOFF_PARKING: _ClassVar[AddGroupRequest.Point.PointType]
            POINT_TYPE_TURNING_POINT: _ClassVar[AddGroupRequest.Point.PointType]
            POINT_TYPE_TAKEOFF_PARKING_HOT: _ClassVar[AddGroupRequest.Point.PointType]
            POINT_TYPE_LAND: _ClassVar[AddGroupRequest.Point.PointType]
        POINT_TYPE_RANDOM: AddGroupRequest.Point.PointType
        POINT_TYPE_TAKEOFF: AddGroupRequest.Point.PointType
        POINT_TYPE_TAKEOFF_PARKING: AddGroupRequest.Point.PointType
        POINT_TYPE_TURNING_POINT: AddGroupRequest.Point.PointType
        POINT_TYPE_TAKEOFF_PARKING_HOT: AddGroupRequest.Point.PointType
        POINT_TYPE_LAND: AddGroupRequest.Point.PointType
        POSITION_FIELD_NUMBER: _ClassVar[int]
        ALTITUDE_TYPE_FIELD_NUMBER: _ClassVar[int]
        TYPE_FIELD_NUMBER: _ClassVar[int]
        ACTION_FIELD_NUMBER: _ClassVar[int]
        FORM_FIELD_NUMBER: _ClassVar[int]
        SPEED_FIELD_NUMBER: _ClassVar[int]
        position: _common_pb2.InputPosition
        altitude_type: AddGroupRequest.Point.AltitudeType
        type: AddGroupRequest.Point.PointType
        action: str
        form: str
        speed: float
        def __init__(self, position: _Optional[_Union[_common_pb2.InputPosition, _Mapping]] = ..., altitude_type: _Optional[_Union[AddGroupRequest.Point.AltitudeType, str]] = ..., type: _Optional[_Union[AddGroupRequest.Point.PointType, str]] = ..., action: _Optional[str] = ..., form: _Optional[str] = ..., speed: _Optional[float] = ...) -> None: ...
    class Task(_message.Message):
        __slots__ = ()
        def __init__(self) -> None: ...
    COUNTRY_FIELD_NUMBER: _ClassVar[int]
    GROUP_CATEGORY_FIELD_NUMBER: _ClassVar[int]
    GROUND_TEMPLATE_FIELD_NUMBER: _ClassVar[int]
    SHIP_TEMPLATE_FIELD_NUMBER: _ClassVar[int]
    HELICOPTER_TEMPLATE_FIELD_NUMBER: _ClassVar[int]
    PLANE_TEMPLATE_FIELD_NUMBER: _ClassVar[int]
    country: _common_pb2.Country
    group_category: _common_pb2.GroupCategory
    ground_template: AddGroupRequest.GroundGroupTemplate
    ship_template: AddGroupRequest.ShipGroupTemplate
    helicopter_template: AddGroupRequest.HelicopterGroupTemplate
    plane_template: AddGroupRequest.PlaneGroupTemplate
    def __init__(self, country: _Optional[_Union[_common_pb2.Country, str]] = ..., group_category: _Optional[_Union[_common_pb2.GroupCategory, str]] = ..., ground_template: _Optional[_Union[AddGroupRequest.GroundGroupTemplate, _Mapping]] = ..., ship_template: _Optional[_Union[AddGroupRequest.ShipGroupTemplate, _Mapping]] = ..., helicopter_template: _Optional[_Union[AddGroupRequest.HelicopterGroupTemplate, _Mapping]] = ..., plane_template: _Optional[_Union[AddGroupRequest.PlaneGroupTemplate, _Mapping]] = ...) -> None: ...

class AddGroupResponse(_message.Message):
    __slots__ = ("group",)
    GROUP_FIELD_NUMBER: _ClassVar[int]
    group: _common_pb2.Group
    def __init__(self, group: _Optional[_Union[_common_pb2.Group, _Mapping]] = ...) -> None: ...

class GetStaticObjectsRequest(_message.Message):
    __slots__ = ("coalition",)
    COALITION_FIELD_NUMBER: _ClassVar[int]
    coalition: _common_pb2.Coalition
    def __init__(self, coalition: _Optional[_Union[_common_pb2.Coalition, str]] = ...) -> None: ...

class GetStaticObjectsResponse(_message.Message):
    __slots__ = ("statics",)
    STATICS_FIELD_NUMBER: _ClassVar[int]
    statics: _containers.RepeatedCompositeFieldContainer[_common_pb2.Static]
    def __init__(self, statics: _Optional[_Iterable[_Union[_common_pb2.Static, _Mapping]]] = ...) -> None: ...

class AddStaticObjectRequest(_message.Message):
    __slots__ = ("name", "country", "type", "livery", "dead", "rate", "heading", "position", "cargo_mass")
    NAME_FIELD_NUMBER: _ClassVar[int]
    COUNTRY_FIELD_NUMBER: _ClassVar[int]
    TYPE_FIELD_NUMBER: _ClassVar[int]
    LIVERY_FIELD_NUMBER: _ClassVar[int]
    DEAD_FIELD_NUMBER: _ClassVar[int]
    RATE_FIELD_NUMBER: _ClassVar[int]
    HEADING_FIELD_NUMBER: _ClassVar[int]
    POSITION_FIELD_NUMBER: _ClassVar[int]
    CARGO_MASS_FIELD_NUMBER: _ClassVar[int]
    name: str
    country: _common_pb2.Country
    type: str
    livery: str
    dead: bool
    rate: int
    heading: float
    position: _common_pb2.InputPosition
    cargo_mass: int
    def __init__(self, name: _Optional[str] = ..., country: _Optional[_Union[_common_pb2.Country, str]] = ..., type: _Optional[str] = ..., livery: _Optional[str] = ..., dead: bool = ..., rate: _Optional[int] = ..., heading: _Optional[float] = ..., position: _Optional[_Union[_common_pb2.InputPosition, _Mapping]] = ..., cargo_mass: _Optional[int] = ...) -> None: ...

class AddStaticObjectResponse(_message.Message):
    __slots__ = ("name",)
    NAME_FIELD_NUMBER: _ClassVar[int]
    name: str
    def __init__(self, name: _Optional[str] = ...) -> None: ...

class AddLinkedStaticRequest(_message.Message):
    __slots__ = ("name", "country", "type", "livery", "dead", "rate", "unit", "angle", "x", "y")
    NAME_FIELD_NUMBER: _ClassVar[int]
    COUNTRY_FIELD_NUMBER: _ClassVar[int]
    TYPE_FIELD_NUMBER: _ClassVar[int]
    LIVERY_FIELD_NUMBER: _ClassVar[int]
    DEAD_FIELD_NUMBER: _ClassVar[int]
    RATE_FIELD_NUMBER: _ClassVar[int]
    UNIT_FIELD_NUMBER: _ClassVar[int]
    ANGLE_FIELD_NUMBER: _ClassVar[int]
    X_FIELD_NUMBER: _ClassVar[int]
    Y_FIELD_NUMBER: _ClassVar[int]
    name: str
    country: _common_pb2.Country
    type: str
    livery: str
    dead: bool
    rate: int
    unit: str
    angle: float
    x: float
    y: float
    def __init__(self, name: _Optional[str] = ..., country: _Optional[_Union[_common_pb2.Country, str]] = ..., type: _Optional[str] = ..., livery: _Optional[str] = ..., dead: bool = ..., rate: _Optional[int] = ..., unit: _Optional[str] = ..., angle: _Optional[float] = ..., x: _Optional[float] = ..., y: _Optional[float] = ...) -> None: ...

class AddLinkedStaticResponse(_message.Message):
    __slots__ = ("name",)
    NAME_FIELD_NUMBER: _ClassVar[int]
    name: str
    def __init__(self, name: _Optional[str] = ...) -> None: ...

class GetGroupsRequest(_message.Message):
    __slots__ = ("coalition", "category")
    COALITION_FIELD_NUMBER: _ClassVar[int]
    CATEGORY_FIELD_NUMBER: _ClassVar[int]
    coalition: _common_pb2.Coalition
    category: _common_pb2.GroupCategory
    def __init__(self, coalition: _Optional[_Union[_common_pb2.Coalition, str]] = ..., category: _Optional[_Union[_common_pb2.GroupCategory, str]] = ...) -> None: ...

class GetGroupsResponse(_message.Message):
    __slots__ = ("groups",)
    GROUPS_FIELD_NUMBER: _ClassVar[int]
    groups: _containers.RepeatedCompositeFieldContainer[_common_pb2.Group]
    def __init__(self, groups: _Optional[_Iterable[_Union[_common_pb2.Group, _Mapping]]] = ...) -> None: ...

class GetBullseyeRequest(_message.Message):
    __slots__ = ("coalition",)
    COALITION_FIELD_NUMBER: _ClassVar[int]
    coalition: _common_pb2.Coalition
    def __init__(self, coalition: _Optional[_Union[_common_pb2.Coalition, str]] = ...) -> None: ...

class GetBullseyeResponse(_message.Message):
    __slots__ = ("position",)
    POSITION_FIELD_NUMBER: _ClassVar[int]
    position: _common_pb2.Position
    def __init__(self, position: _Optional[_Union[_common_pb2.Position, _Mapping]] = ...) -> None: ...

class GetPlayerUnitsRequest(_message.Message):
    __slots__ = ("coalition",)
    COALITION_FIELD_NUMBER: _ClassVar[int]
    coalition: _common_pb2.Coalition
    def __init__(self, coalition: _Optional[_Union[_common_pb2.Coalition, str]] = ...) -> None: ...

class GetPlayerUnitsResponse(_message.Message):
    __slots__ = ("units",)
    UNITS_FIELD_NUMBER: _ClassVar[int]
    units: _containers.RepeatedCompositeFieldContainer[_common_pb2.Unit]
    def __init__(self, units: _Optional[_Iterable[_Union[_common_pb2.Unit, _Mapping]]] = ...) -> None: ...
