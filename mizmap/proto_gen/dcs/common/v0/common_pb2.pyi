from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class ObjectCategory(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    OBJECT_CATEGORY_UNSPECIFIED: _ClassVar[ObjectCategory]
    OBJECT_CATEGORY_UNIT: _ClassVar[ObjectCategory]
    OBJECT_CATEGORY_WEAPON: _ClassVar[ObjectCategory]
    OBJECT_CATEGORY_STATIC: _ClassVar[ObjectCategory]
    OBJECT_CATEGORY_SCENERY: _ClassVar[ObjectCategory]
    OBJECT_CATEGORY_BASE: _ClassVar[ObjectCategory]
    OBJECT_CATEGORY_CARGO: _ClassVar[ObjectCategory]

class AirbaseCategory(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    AIRBASE_CATEGORY_UNSPECIFIED: _ClassVar[AirbaseCategory]
    AIRBASE_CATEGORY_AIRDROME: _ClassVar[AirbaseCategory]
    AIRBASE_CATEGORY_HELIPAD: _ClassVar[AirbaseCategory]
    AIRBASE_CATEGORY_SHIP: _ClassVar[AirbaseCategory]

class Coalition(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    COALITION_ALL: _ClassVar[Coalition]
    COALITION_NEUTRAL: _ClassVar[Coalition]
    COALITION_RED: _ClassVar[Coalition]
    COALITION_BLUE: _ClassVar[Coalition]

class Country(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    COUNTRY_UNSPECIFIED: _ClassVar[Country]
    COUNTRY_RUSSIA: _ClassVar[Country]
    COUNTRY_UKRAINE: _ClassVar[Country]
    COUNTRY_UNITED_STATES_OF_AMERICA: _ClassVar[Country]
    COUNTRY_TURKEY: _ClassVar[Country]
    COUNTRY_UNITED_KINGDOM: _ClassVar[Country]
    COUNTRY_FRANCE: _ClassVar[Country]
    COUNTRY_GERMANY: _ClassVar[Country]
    COUNTRY_AGGRESSORS: _ClassVar[Country]
    COUNTRY_CANADA: _ClassVar[Country]
    COUNTRY_SPAIN: _ClassVar[Country]
    COUNTRY_THE_NETHERLANDS: _ClassVar[Country]
    COUNTRY_BELGIUM: _ClassVar[Country]
    COUNTRY_NORWAY: _ClassVar[Country]
    COUNTRY_DENMARK: _ClassVar[Country]
    COUNTRY_UNUSED: _ClassVar[Country]
    COUNTRY_ISRAEL: _ClassVar[Country]
    COUNTRY_GEORGIA: _ClassVar[Country]
    COUNTRY_INSURGENTS: _ClassVar[Country]
    COUNTRY_ABKHAZIA: _ClassVar[Country]
    COUNTRY_SOUTH_OSETIA: _ClassVar[Country]
    COUNTRY_ITALY: _ClassVar[Country]
    COUNTRY_AUSTRALIA: _ClassVar[Country]
    COUNTRY_SWITZERLAND: _ClassVar[Country]
    COUNTRY_AUSTRIA: _ClassVar[Country]
    COUNTRY_BELARUS: _ClassVar[Country]
    COUNTRY_BULGARIA: _ClassVar[Country]
    COUNTRY_CZECH_REPUBLIC: _ClassVar[Country]
    COUNTRY_CHINA: _ClassVar[Country]
    COUNTRY_CROATIA: _ClassVar[Country]
    COUNTRY_EGYPT: _ClassVar[Country]
    COUNTRY_FINLAND: _ClassVar[Country]
    COUNTRY_GREECE: _ClassVar[Country]
    COUNTRY_HUNGARY: _ClassVar[Country]
    COUNTRY_INDIA: _ClassVar[Country]
    COUNTRY_IRAN: _ClassVar[Country]
    COUNTRY_IRAQ: _ClassVar[Country]
    COUNTRY_JAPAN: _ClassVar[Country]
    COUNTRY_KAZAKHSTAN: _ClassVar[Country]
    COUNTRY_NORTH_KOREA: _ClassVar[Country]
    COUNTRY_PAKISTAN: _ClassVar[Country]
    COUNTRY_POLAND: _ClassVar[Country]
    COUNTRY_ROMANIA: _ClassVar[Country]
    COUNTRY_SAUDI_ARABIA: _ClassVar[Country]
    COUNTRY_SERBIA: _ClassVar[Country]
    COUNTRY_SLOVAKIA: _ClassVar[Country]
    COUNTRY_SOUTH_KOREA: _ClassVar[Country]
    COUNTRY_SWEDEN: _ClassVar[Country]
    COUNTRY_SYRIA: _ClassVar[Country]
    COUNTRY_YEMEN: _ClassVar[Country]
    COUNTRY_VIETNAM: _ClassVar[Country]
    COUNTRY_VENEZUELA: _ClassVar[Country]
    COUNTRY_TUNISIA: _ClassVar[Country]
    COUNTRY_THAILAND: _ClassVar[Country]
    COUNTRY_SUDAN: _ClassVar[Country]
    COUNTRY_PHILIPPINES: _ClassVar[Country]
    COUNTRY_MOROCCO: _ClassVar[Country]
    COUNTRY_MEXICO: _ClassVar[Country]
    COUNTRY_MALAYSIA: _ClassVar[Country]
    COUNTRY_LIBYA: _ClassVar[Country]
    COUNTRY_JORDAN: _ClassVar[Country]
    COUNTRY_INDONESIA: _ClassVar[Country]
    COUNTRY_HONDURAS: _ClassVar[Country]
    COUNTRY_ETHIOPIA: _ClassVar[Country]
    COUNTRY_CHILE: _ClassVar[Country]
    COUNTRY_BRAZIL: _ClassVar[Country]
    COUNTRY_BAHRAIN: _ClassVar[Country]
    COUNTRY_THIRDREICH: _ClassVar[Country]
    COUNTRY_YUGOSLAVIA: _ClassVar[Country]
    COUNTRY_SOVIET_UNION: _ClassVar[Country]
    COUNTRY_ITALIAN_SOCIAL_REPUBLIC: _ClassVar[Country]
    COUNTRY_ALGERIA: _ClassVar[Country]
    COUNTRY_KUWAIT: _ClassVar[Country]
    COUNTRY_QATAR: _ClassVar[Country]
    COUNTRY_OMAN: _ClassVar[Country]
    COUNTRY_UNITED_ARAB_EMIRATES: _ClassVar[Country]
    COUNTRY_SOUTH_AFRICA: _ClassVar[Country]
    COUNTRY_CUBA: _ClassVar[Country]
    COUNTRY_PORTUGAL: _ClassVar[Country]
    COUNTRY_GERMAN_DEMOCRATIC_REPUBLIC: _ClassVar[Country]
    COUNTRY_LEBANON: _ClassVar[Country]
    COUNTRY_COMBINED_JOINT_TASK_FORCE_BLUE: _ClassVar[Country]
    COUNTRY_COMBINED_JOINT_TASK_FORCE_RED: _ClassVar[Country]
    COUNTRY_UNITED_NATIONS_PEACEKEEPERS: _ClassVar[Country]
    COUNTRY_ARGENTINA: _ClassVar[Country]
    COUNTRY_CYPRUS: _ClassVar[Country]
    COUNTRY_SLOVENIA: _ClassVar[Country]

class GroupCategory(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    GROUP_CATEGORY_UNSPECIFIED: _ClassVar[GroupCategory]
    GROUP_CATEGORY_AIRPLANE: _ClassVar[GroupCategory]
    GROUP_CATEGORY_HELICOPTER: _ClassVar[GroupCategory]
    GROUP_CATEGORY_GROUND: _ClassVar[GroupCategory]
    GROUP_CATEGORY_SHIP: _ClassVar[GroupCategory]
    GROUP_CATEGORY_TRAIN: _ClassVar[GroupCategory]
OBJECT_CATEGORY_UNSPECIFIED: ObjectCategory
OBJECT_CATEGORY_UNIT: ObjectCategory
OBJECT_CATEGORY_WEAPON: ObjectCategory
OBJECT_CATEGORY_STATIC: ObjectCategory
OBJECT_CATEGORY_SCENERY: ObjectCategory
OBJECT_CATEGORY_BASE: ObjectCategory
OBJECT_CATEGORY_CARGO: ObjectCategory
AIRBASE_CATEGORY_UNSPECIFIED: AirbaseCategory
AIRBASE_CATEGORY_AIRDROME: AirbaseCategory
AIRBASE_CATEGORY_HELIPAD: AirbaseCategory
AIRBASE_CATEGORY_SHIP: AirbaseCategory
COALITION_ALL: Coalition
COALITION_NEUTRAL: Coalition
COALITION_RED: Coalition
COALITION_BLUE: Coalition
COUNTRY_UNSPECIFIED: Country
COUNTRY_RUSSIA: Country
COUNTRY_UKRAINE: Country
COUNTRY_UNITED_STATES_OF_AMERICA: Country
COUNTRY_TURKEY: Country
COUNTRY_UNITED_KINGDOM: Country
COUNTRY_FRANCE: Country
COUNTRY_GERMANY: Country
COUNTRY_AGGRESSORS: Country
COUNTRY_CANADA: Country
COUNTRY_SPAIN: Country
COUNTRY_THE_NETHERLANDS: Country
COUNTRY_BELGIUM: Country
COUNTRY_NORWAY: Country
COUNTRY_DENMARK: Country
COUNTRY_UNUSED: Country
COUNTRY_ISRAEL: Country
COUNTRY_GEORGIA: Country
COUNTRY_INSURGENTS: Country
COUNTRY_ABKHAZIA: Country
COUNTRY_SOUTH_OSETIA: Country
COUNTRY_ITALY: Country
COUNTRY_AUSTRALIA: Country
COUNTRY_SWITZERLAND: Country
COUNTRY_AUSTRIA: Country
COUNTRY_BELARUS: Country
COUNTRY_BULGARIA: Country
COUNTRY_CZECH_REPUBLIC: Country
COUNTRY_CHINA: Country
COUNTRY_CROATIA: Country
COUNTRY_EGYPT: Country
COUNTRY_FINLAND: Country
COUNTRY_GREECE: Country
COUNTRY_HUNGARY: Country
COUNTRY_INDIA: Country
COUNTRY_IRAN: Country
COUNTRY_IRAQ: Country
COUNTRY_JAPAN: Country
COUNTRY_KAZAKHSTAN: Country
COUNTRY_NORTH_KOREA: Country
COUNTRY_PAKISTAN: Country
COUNTRY_POLAND: Country
COUNTRY_ROMANIA: Country
COUNTRY_SAUDI_ARABIA: Country
COUNTRY_SERBIA: Country
COUNTRY_SLOVAKIA: Country
COUNTRY_SOUTH_KOREA: Country
COUNTRY_SWEDEN: Country
COUNTRY_SYRIA: Country
COUNTRY_YEMEN: Country
COUNTRY_VIETNAM: Country
COUNTRY_VENEZUELA: Country
COUNTRY_TUNISIA: Country
COUNTRY_THAILAND: Country
COUNTRY_SUDAN: Country
COUNTRY_PHILIPPINES: Country
COUNTRY_MOROCCO: Country
COUNTRY_MEXICO: Country
COUNTRY_MALAYSIA: Country
COUNTRY_LIBYA: Country
COUNTRY_JORDAN: Country
COUNTRY_INDONESIA: Country
COUNTRY_HONDURAS: Country
COUNTRY_ETHIOPIA: Country
COUNTRY_CHILE: Country
COUNTRY_BRAZIL: Country
COUNTRY_BAHRAIN: Country
COUNTRY_THIRDREICH: Country
COUNTRY_YUGOSLAVIA: Country
COUNTRY_SOVIET_UNION: Country
COUNTRY_ITALIAN_SOCIAL_REPUBLIC: Country
COUNTRY_ALGERIA: Country
COUNTRY_KUWAIT: Country
COUNTRY_QATAR: Country
COUNTRY_OMAN: Country
COUNTRY_UNITED_ARAB_EMIRATES: Country
COUNTRY_SOUTH_AFRICA: Country
COUNTRY_CUBA: Country
COUNTRY_PORTUGAL: Country
COUNTRY_GERMAN_DEMOCRATIC_REPUBLIC: Country
COUNTRY_LEBANON: Country
COUNTRY_COMBINED_JOINT_TASK_FORCE_BLUE: Country
COUNTRY_COMBINED_JOINT_TASK_FORCE_RED: Country
COUNTRY_UNITED_NATIONS_PEACEKEEPERS: Country
COUNTRY_ARGENTINA: Country
COUNTRY_CYPRUS: Country
COUNTRY_SLOVENIA: Country
GROUP_CATEGORY_UNSPECIFIED: GroupCategory
GROUP_CATEGORY_AIRPLANE: GroupCategory
GROUP_CATEGORY_HELICOPTER: GroupCategory
GROUP_CATEGORY_GROUND: GroupCategory
GROUP_CATEGORY_SHIP: GroupCategory
GROUP_CATEGORY_TRAIN: GroupCategory

class Position(_message.Message):
    __slots__ = ("lat", "lon", "alt", "u", "v")
    LAT_FIELD_NUMBER: _ClassVar[int]
    LON_FIELD_NUMBER: _ClassVar[int]
    ALT_FIELD_NUMBER: _ClassVar[int]
    U_FIELD_NUMBER: _ClassVar[int]
    V_FIELD_NUMBER: _ClassVar[int]
    lat: float
    lon: float
    alt: float
    u: float
    v: float
    def __init__(self, lat: _Optional[float] = ..., lon: _Optional[float] = ..., alt: _Optional[float] = ..., u: _Optional[float] = ..., v: _Optional[float] = ...) -> None: ...

class InputPosition(_message.Message):
    __slots__ = ("lat", "lon", "alt")
    LAT_FIELD_NUMBER: _ClassVar[int]
    LON_FIELD_NUMBER: _ClassVar[int]
    ALT_FIELD_NUMBER: _ClassVar[int]
    lat: float
    lon: float
    alt: float
    def __init__(self, lat: _Optional[float] = ..., lon: _Optional[float] = ..., alt: _Optional[float] = ...) -> None: ...

class Unknown(_message.Message):
    __slots__ = ("name",)
    NAME_FIELD_NUMBER: _ClassVar[int]
    name: str
    def __init__(self, name: _Optional[str] = ...) -> None: ...

class Unit(_message.Message):
    __slots__ = ("id", "name", "callsign", "coalition", "type", "position", "orientation", "velocity", "player_name", "group", "number_in_group")
    ID_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    CALLSIGN_FIELD_NUMBER: _ClassVar[int]
    COALITION_FIELD_NUMBER: _ClassVar[int]
    TYPE_FIELD_NUMBER: _ClassVar[int]
    POSITION_FIELD_NUMBER: _ClassVar[int]
    ORIENTATION_FIELD_NUMBER: _ClassVar[int]
    VELOCITY_FIELD_NUMBER: _ClassVar[int]
    PLAYER_NAME_FIELD_NUMBER: _ClassVar[int]
    GROUP_FIELD_NUMBER: _ClassVar[int]
    NUMBER_IN_GROUP_FIELD_NUMBER: _ClassVar[int]
    id: int
    name: str
    callsign: str
    coalition: Coalition
    type: str
    position: Position
    orientation: Orientation
    velocity: Velocity
    player_name: str
    group: Group
    number_in_group: int
    def __init__(self, id: _Optional[int] = ..., name: _Optional[str] = ..., callsign: _Optional[str] = ..., coalition: _Optional[_Union[Coalition, str]] = ..., type: _Optional[str] = ..., position: _Optional[_Union[Position, _Mapping]] = ..., orientation: _Optional[_Union[Orientation, _Mapping]] = ..., velocity: _Optional[_Union[Velocity, _Mapping]] = ..., player_name: _Optional[str] = ..., group: _Optional[_Union[Group, _Mapping]] = ..., number_in_group: _Optional[int] = ...) -> None: ...

class Group(_message.Message):
    __slots__ = ("id", "name", "coalition", "category")
    ID_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    COALITION_FIELD_NUMBER: _ClassVar[int]
    CATEGORY_FIELD_NUMBER: _ClassVar[int]
    id: int
    name: str
    coalition: Coalition
    category: GroupCategory
    def __init__(self, id: _Optional[int] = ..., name: _Optional[str] = ..., coalition: _Optional[_Union[Coalition, str]] = ..., category: _Optional[_Union[GroupCategory, str]] = ...) -> None: ...

class Weapon(_message.Message):
    __slots__ = ("id", "type", "position", "orientation", "velocity")
    ID_FIELD_NUMBER: _ClassVar[int]
    TYPE_FIELD_NUMBER: _ClassVar[int]
    POSITION_FIELD_NUMBER: _ClassVar[int]
    ORIENTATION_FIELD_NUMBER: _ClassVar[int]
    VELOCITY_FIELD_NUMBER: _ClassVar[int]
    id: int
    type: str
    position: Position
    orientation: Orientation
    velocity: Velocity
    def __init__(self, id: _Optional[int] = ..., type: _Optional[str] = ..., position: _Optional[_Union[Position, _Mapping]] = ..., orientation: _Optional[_Union[Orientation, _Mapping]] = ..., velocity: _Optional[_Union[Velocity, _Mapping]] = ...) -> None: ...

class Static(_message.Message):
    __slots__ = ("id", "type", "name", "coalition", "position")
    ID_FIELD_NUMBER: _ClassVar[int]
    TYPE_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    COALITION_FIELD_NUMBER: _ClassVar[int]
    POSITION_FIELD_NUMBER: _ClassVar[int]
    id: int
    type: str
    name: str
    coalition: Coalition
    position: Position
    def __init__(self, id: _Optional[int] = ..., type: _Optional[str] = ..., name: _Optional[str] = ..., coalition: _Optional[_Union[Coalition, str]] = ..., position: _Optional[_Union[Position, _Mapping]] = ...) -> None: ...

class Scenery(_message.Message):
    __slots__ = ("id", "type", "position")
    ID_FIELD_NUMBER: _ClassVar[int]
    TYPE_FIELD_NUMBER: _ClassVar[int]
    POSITION_FIELD_NUMBER: _ClassVar[int]
    id: int
    type: str
    position: Position
    def __init__(self, id: _Optional[int] = ..., type: _Optional[str] = ..., position: _Optional[_Union[Position, _Mapping]] = ...) -> None: ...

class Airbase(_message.Message):
    __slots__ = ("unit", "name", "callsign", "coalition", "position", "category", "display_name")
    UNIT_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    CALLSIGN_FIELD_NUMBER: _ClassVar[int]
    COALITION_FIELD_NUMBER: _ClassVar[int]
    POSITION_FIELD_NUMBER: _ClassVar[int]
    CATEGORY_FIELD_NUMBER: _ClassVar[int]
    DISPLAY_NAME_FIELD_NUMBER: _ClassVar[int]
    unit: Unit
    name: str
    callsign: str
    coalition: Coalition
    position: Position
    category: AirbaseCategory
    display_name: str
    def __init__(self, unit: _Optional[_Union[Unit, _Mapping]] = ..., name: _Optional[str] = ..., callsign: _Optional[str] = ..., coalition: _Optional[_Union[Coalition, str]] = ..., position: _Optional[_Union[Position, _Mapping]] = ..., category: _Optional[_Union[AirbaseCategory, str]] = ..., display_name: _Optional[str] = ...) -> None: ...

class Cargo(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class Initiator(_message.Message):
    __slots__ = ("unknown", "unit", "weapon", "static", "scenery", "airbase", "cargo")
    UNKNOWN_FIELD_NUMBER: _ClassVar[int]
    UNIT_FIELD_NUMBER: _ClassVar[int]
    WEAPON_FIELD_NUMBER: _ClassVar[int]
    STATIC_FIELD_NUMBER: _ClassVar[int]
    SCENERY_FIELD_NUMBER: _ClassVar[int]
    AIRBASE_FIELD_NUMBER: _ClassVar[int]
    CARGO_FIELD_NUMBER: _ClassVar[int]
    unknown: Unknown
    unit: Unit
    weapon: Weapon
    static: Static
    scenery: Scenery
    airbase: Airbase
    cargo: Cargo
    def __init__(self, unknown: _Optional[_Union[Unknown, _Mapping]] = ..., unit: _Optional[_Union[Unit, _Mapping]] = ..., weapon: _Optional[_Union[Weapon, _Mapping]] = ..., static: _Optional[_Union[Static, _Mapping]] = ..., scenery: _Optional[_Union[Scenery, _Mapping]] = ..., airbase: _Optional[_Union[Airbase, _Mapping]] = ..., cargo: _Optional[_Union[Cargo, _Mapping]] = ...) -> None: ...

class Target(_message.Message):
    __slots__ = ("unknown", "unit", "weapon", "static", "scenery", "airbase", "cargo")
    UNKNOWN_FIELD_NUMBER: _ClassVar[int]
    UNIT_FIELD_NUMBER: _ClassVar[int]
    WEAPON_FIELD_NUMBER: _ClassVar[int]
    STATIC_FIELD_NUMBER: _ClassVar[int]
    SCENERY_FIELD_NUMBER: _ClassVar[int]
    AIRBASE_FIELD_NUMBER: _ClassVar[int]
    CARGO_FIELD_NUMBER: _ClassVar[int]
    unknown: Unknown
    unit: Unit
    weapon: Weapon
    static: Static
    scenery: Scenery
    airbase: Airbase
    cargo: Cargo
    def __init__(self, unknown: _Optional[_Union[Unknown, _Mapping]] = ..., unit: _Optional[_Union[Unit, _Mapping]] = ..., weapon: _Optional[_Union[Weapon, _Mapping]] = ..., static: _Optional[_Union[Static, _Mapping]] = ..., scenery: _Optional[_Union[Scenery, _Mapping]] = ..., airbase: _Optional[_Union[Airbase, _Mapping]] = ..., cargo: _Optional[_Union[Cargo, _Mapping]] = ...) -> None: ...

class MarkPanel(_message.Message):
    __slots__ = ("id", "time", "initiator", "coalition", "group_id", "text", "position")
    ID_FIELD_NUMBER: _ClassVar[int]
    TIME_FIELD_NUMBER: _ClassVar[int]
    INITIATOR_FIELD_NUMBER: _ClassVar[int]
    COALITION_FIELD_NUMBER: _ClassVar[int]
    GROUP_ID_FIELD_NUMBER: _ClassVar[int]
    TEXT_FIELD_NUMBER: _ClassVar[int]
    POSITION_FIELD_NUMBER: _ClassVar[int]
    id: int
    time: float
    initiator: Unit
    coalition: Coalition
    group_id: int
    text: str
    position: Position
    def __init__(self, id: _Optional[int] = ..., time: _Optional[float] = ..., initiator: _Optional[_Union[Unit, _Mapping]] = ..., coalition: _Optional[_Union[Coalition, str]] = ..., group_id: _Optional[int] = ..., text: _Optional[str] = ..., position: _Optional[_Union[Position, _Mapping]] = ...) -> None: ...

class Vector(_message.Message):
    __slots__ = ("x", "y", "z")
    X_FIELD_NUMBER: _ClassVar[int]
    Y_FIELD_NUMBER: _ClassVar[int]
    Z_FIELD_NUMBER: _ClassVar[int]
    x: float
    y: float
    z: float
    def __init__(self, x: _Optional[float] = ..., y: _Optional[float] = ..., z: _Optional[float] = ...) -> None: ...

class Orientation(_message.Message):
    __slots__ = ("heading", "yaw", "pitch", "roll", "forward", "right", "up")
    HEADING_FIELD_NUMBER: _ClassVar[int]
    YAW_FIELD_NUMBER: _ClassVar[int]
    PITCH_FIELD_NUMBER: _ClassVar[int]
    ROLL_FIELD_NUMBER: _ClassVar[int]
    FORWARD_FIELD_NUMBER: _ClassVar[int]
    RIGHT_FIELD_NUMBER: _ClassVar[int]
    UP_FIELD_NUMBER: _ClassVar[int]
    heading: float
    yaw: float
    pitch: float
    roll: float
    forward: Vector
    right: Vector
    up: Vector
    def __init__(self, heading: _Optional[float] = ..., yaw: _Optional[float] = ..., pitch: _Optional[float] = ..., roll: _Optional[float] = ..., forward: _Optional[_Union[Vector, _Mapping]] = ..., right: _Optional[_Union[Vector, _Mapping]] = ..., up: _Optional[_Union[Vector, _Mapping]] = ...) -> None: ...

class Velocity(_message.Message):
    __slots__ = ("heading", "speed", "velocity")
    HEADING_FIELD_NUMBER: _ClassVar[int]
    SPEED_FIELD_NUMBER: _ClassVar[int]
    VELOCITY_FIELD_NUMBER: _ClassVar[int]
    heading: float
    speed: float
    velocity: Vector
    def __init__(self, heading: _Optional[float] = ..., speed: _Optional[float] = ..., velocity: _Optional[_Union[Vector, _Mapping]] = ...) -> None: ...

class Contact(_message.Message):
    __slots__ = ("id", "visible", "distance", "object", "unit", "weapon")
    ID_FIELD_NUMBER: _ClassVar[int]
    VISIBLE_FIELD_NUMBER: _ClassVar[int]
    DISTANCE_FIELD_NUMBER: _ClassVar[int]
    OBJECT_FIELD_NUMBER: _ClassVar[int]
    UNIT_FIELD_NUMBER: _ClassVar[int]
    WEAPON_FIELD_NUMBER: _ClassVar[int]
    id: int
    visible: bool
    distance: bool
    object: Unknown
    unit: Unit
    weapon: Weapon
    def __init__(self, id: _Optional[int] = ..., visible: bool = ..., distance: bool = ..., object: _Optional[_Union[Unknown, _Mapping]] = ..., unit: _Optional[_Union[Unit, _Mapping]] = ..., weapon: _Optional[_Union[Weapon, _Mapping]] = ...) -> None: ...
