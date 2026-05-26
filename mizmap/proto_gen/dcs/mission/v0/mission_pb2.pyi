from dcs.common.v0 import common_pb2 as _common_pb2
from google.protobuf import struct_pb2 as _struct_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class StreamEventsRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class StreamEventsResponse(_message.Message):
    __slots__ = ("time", "shot", "hit", "takeoff", "land", "crash", "ejection", "refueling", "dead", "pilot_dead", "base_capture", "mission_start", "mission_end", "refueling_stop", "birth", "human_failure", "detailed_failure", "engine_startup", "engine_shutdown", "player_enter_unit", "player_leave_unit", "shooting_start", "shooting_end", "mark_add", "mark_change", "mark_remove", "kill", "score", "unit_lost", "landing_after_ejection", "discard_chair_after_ejection", "weapon_add", "landing_quality_mark", "runway_takeoff", "runway_touch", "connect", "disconnect", "player_send_chat", "player_change_slot", "mission_command", "coalition_command", "group_command", "simulation_fps", "tts", "srs_connect", "srs_disconnect")
    class DisconnectReason(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        DISCONNECT_REASON_UNSPECIFIED: _ClassVar[StreamEventsResponse.DisconnectReason]
        DISCONNECT_REASON_THATS_OKAY: _ClassVar[StreamEventsResponse.DisconnectReason]
        DISCONNECT_REASON_INVALID_ADDRESS: _ClassVar[StreamEventsResponse.DisconnectReason]
        DISCONNECT_REASON_CONNECT_FAILED: _ClassVar[StreamEventsResponse.DisconnectReason]
        DISCONNECT_REASON_WRONG_VERSION: _ClassVar[StreamEventsResponse.DisconnectReason]
        DISCONNECT_REASON_PROTOCOL_ERROR: _ClassVar[StreamEventsResponse.DisconnectReason]
        DISCONNECT_REASON_TIMEOUT: _ClassVar[StreamEventsResponse.DisconnectReason]
        DISCONNECT_REASON_INVALID_PASSWORD: _ClassVar[StreamEventsResponse.DisconnectReason]
        DISCONNECT_REASON_BANNED: _ClassVar[StreamEventsResponse.DisconnectReason]
        DISCONNECT_REASON_BAD_CALLSIGN: _ClassVar[StreamEventsResponse.DisconnectReason]
        DISCONNECT_REASON_TAINTED_CLIENT: _ClassVar[StreamEventsResponse.DisconnectReason]
        DISCONNECT_REASON_KICKED: _ClassVar[StreamEventsResponse.DisconnectReason]
        DISCONNECT_REASON_REFUSED: _ClassVar[StreamEventsResponse.DisconnectReason]
        DISCONNECT_REASON_DENIED_TRIAL_ONLY: _ClassVar[StreamEventsResponse.DisconnectReason]
    DISCONNECT_REASON_UNSPECIFIED: StreamEventsResponse.DisconnectReason
    DISCONNECT_REASON_THATS_OKAY: StreamEventsResponse.DisconnectReason
    DISCONNECT_REASON_INVALID_ADDRESS: StreamEventsResponse.DisconnectReason
    DISCONNECT_REASON_CONNECT_FAILED: StreamEventsResponse.DisconnectReason
    DISCONNECT_REASON_WRONG_VERSION: StreamEventsResponse.DisconnectReason
    DISCONNECT_REASON_PROTOCOL_ERROR: StreamEventsResponse.DisconnectReason
    DISCONNECT_REASON_TIMEOUT: StreamEventsResponse.DisconnectReason
    DISCONNECT_REASON_INVALID_PASSWORD: StreamEventsResponse.DisconnectReason
    DISCONNECT_REASON_BANNED: StreamEventsResponse.DisconnectReason
    DISCONNECT_REASON_BAD_CALLSIGN: StreamEventsResponse.DisconnectReason
    DISCONNECT_REASON_TAINTED_CLIENT: StreamEventsResponse.DisconnectReason
    DISCONNECT_REASON_KICKED: StreamEventsResponse.DisconnectReason
    DISCONNECT_REASON_REFUSED: StreamEventsResponse.DisconnectReason
    DISCONNECT_REASON_DENIED_TRIAL_ONLY: StreamEventsResponse.DisconnectReason
    class ShotEvent(_message.Message):
        __slots__ = ("initiator", "weapon")
        INITIATOR_FIELD_NUMBER: _ClassVar[int]
        WEAPON_FIELD_NUMBER: _ClassVar[int]
        initiator: _common_pb2.Initiator
        weapon: _common_pb2.Weapon
        def __init__(self, initiator: _Optional[_Union[_common_pb2.Initiator, _Mapping]] = ..., weapon: _Optional[_Union[_common_pb2.Weapon, _Mapping]] = ...) -> None: ...
    class HitEvent(_message.Message):
        __slots__ = ("initiator", "weapon", "target", "weapon_name")
        INITIATOR_FIELD_NUMBER: _ClassVar[int]
        WEAPON_FIELD_NUMBER: _ClassVar[int]
        TARGET_FIELD_NUMBER: _ClassVar[int]
        WEAPON_NAME_FIELD_NUMBER: _ClassVar[int]
        initiator: _common_pb2.Initiator
        weapon: _common_pb2.Weapon
        target: _common_pb2.Target
        weapon_name: str
        def __init__(self, initiator: _Optional[_Union[_common_pb2.Initiator, _Mapping]] = ..., weapon: _Optional[_Union[_common_pb2.Weapon, _Mapping]] = ..., target: _Optional[_Union[_common_pb2.Target, _Mapping]] = ..., weapon_name: _Optional[str] = ...) -> None: ...
    class TakeoffEvent(_message.Message):
        __slots__ = ("initiator", "place")
        INITIATOR_FIELD_NUMBER: _ClassVar[int]
        PLACE_FIELD_NUMBER: _ClassVar[int]
        initiator: _common_pb2.Initiator
        place: _common_pb2.Airbase
        def __init__(self, initiator: _Optional[_Union[_common_pb2.Initiator, _Mapping]] = ..., place: _Optional[_Union[_common_pb2.Airbase, _Mapping]] = ...) -> None: ...
    class RunwayTakeoffEvent(_message.Message):
        __slots__ = ("initiator", "place")
        INITIATOR_FIELD_NUMBER: _ClassVar[int]
        PLACE_FIELD_NUMBER: _ClassVar[int]
        initiator: _common_pb2.Initiator
        place: _common_pb2.Airbase
        def __init__(self, initiator: _Optional[_Union[_common_pb2.Initiator, _Mapping]] = ..., place: _Optional[_Union[_common_pb2.Airbase, _Mapping]] = ...) -> None: ...
    class LandEvent(_message.Message):
        __slots__ = ("initiator", "place")
        INITIATOR_FIELD_NUMBER: _ClassVar[int]
        PLACE_FIELD_NUMBER: _ClassVar[int]
        initiator: _common_pb2.Initiator
        place: _common_pb2.Airbase
        def __init__(self, initiator: _Optional[_Union[_common_pb2.Initiator, _Mapping]] = ..., place: _Optional[_Union[_common_pb2.Airbase, _Mapping]] = ...) -> None: ...
    class RunwayTouchEvent(_message.Message):
        __slots__ = ("initiator", "place")
        INITIATOR_FIELD_NUMBER: _ClassVar[int]
        PLACE_FIELD_NUMBER: _ClassVar[int]
        initiator: _common_pb2.Initiator
        place: _common_pb2.Airbase
        def __init__(self, initiator: _Optional[_Union[_common_pb2.Initiator, _Mapping]] = ..., place: _Optional[_Union[_common_pb2.Airbase, _Mapping]] = ...) -> None: ...
    class CrashEvent(_message.Message):
        __slots__ = ("initiator",)
        INITIATOR_FIELD_NUMBER: _ClassVar[int]
        initiator: _common_pb2.Initiator
        def __init__(self, initiator: _Optional[_Union[_common_pb2.Initiator, _Mapping]] = ...) -> None: ...
    class EjectionEvent(_message.Message):
        __slots__ = ("initiator", "target")
        INITIATOR_FIELD_NUMBER: _ClassVar[int]
        TARGET_FIELD_NUMBER: _ClassVar[int]
        initiator: _common_pb2.Initiator
        target: _common_pb2.Target
        def __init__(self, initiator: _Optional[_Union[_common_pb2.Initiator, _Mapping]] = ..., target: _Optional[_Union[_common_pb2.Target, _Mapping]] = ...) -> None: ...
    class RefuelingEvent(_message.Message):
        __slots__ = ("initiator",)
        INITIATOR_FIELD_NUMBER: _ClassVar[int]
        initiator: _common_pb2.Initiator
        def __init__(self, initiator: _Optional[_Union[_common_pb2.Initiator, _Mapping]] = ...) -> None: ...
    class DeadEvent(_message.Message):
        __slots__ = ("initiator",)
        INITIATOR_FIELD_NUMBER: _ClassVar[int]
        initiator: _common_pb2.Initiator
        def __init__(self, initiator: _Optional[_Union[_common_pb2.Initiator, _Mapping]] = ...) -> None: ...
    class PilotDeadEvent(_message.Message):
        __slots__ = ("initiator",)
        INITIATOR_FIELD_NUMBER: _ClassVar[int]
        initiator: _common_pb2.Initiator
        def __init__(self, initiator: _Optional[_Union[_common_pb2.Initiator, _Mapping]] = ...) -> None: ...
    class BaseCaptureEvent(_message.Message):
        __slots__ = ("initiator", "place")
        INITIATOR_FIELD_NUMBER: _ClassVar[int]
        PLACE_FIELD_NUMBER: _ClassVar[int]
        initiator: _common_pb2.Initiator
        place: _common_pb2.Airbase
        def __init__(self, initiator: _Optional[_Union[_common_pb2.Initiator, _Mapping]] = ..., place: _Optional[_Union[_common_pb2.Airbase, _Mapping]] = ...) -> None: ...
    class MissionStartEvent(_message.Message):
        __slots__ = ()
        def __init__(self) -> None: ...
    class MissionEndEvent(_message.Message):
        __slots__ = ()
        def __init__(self) -> None: ...
    class RefuelingStopEvent(_message.Message):
        __slots__ = ("initiator",)
        INITIATOR_FIELD_NUMBER: _ClassVar[int]
        initiator: _common_pb2.Initiator
        def __init__(self, initiator: _Optional[_Union[_common_pb2.Initiator, _Mapping]] = ...) -> None: ...
    class BirthEvent(_message.Message):
        __slots__ = ("initiator", "place")
        INITIATOR_FIELD_NUMBER: _ClassVar[int]
        PLACE_FIELD_NUMBER: _ClassVar[int]
        initiator: _common_pb2.Initiator
        place: _common_pb2.Airbase
        def __init__(self, initiator: _Optional[_Union[_common_pb2.Initiator, _Mapping]] = ..., place: _Optional[_Union[_common_pb2.Airbase, _Mapping]] = ...) -> None: ...
    class HumanFailureEvent(_message.Message):
        __slots__ = ("initiator",)
        INITIATOR_FIELD_NUMBER: _ClassVar[int]
        initiator: _common_pb2.Initiator
        def __init__(self, initiator: _Optional[_Union[_common_pb2.Initiator, _Mapping]] = ...) -> None: ...
    class DetailedFailureEvent(_message.Message):
        __slots__ = ("target",)
        TARGET_FIELD_NUMBER: _ClassVar[int]
        target: _common_pb2.Target
        def __init__(self, target: _Optional[_Union[_common_pb2.Target, _Mapping]] = ...) -> None: ...
    class EngineStartupEvent(_message.Message):
        __slots__ = ("initiator", "place")
        INITIATOR_FIELD_NUMBER: _ClassVar[int]
        PLACE_FIELD_NUMBER: _ClassVar[int]
        initiator: _common_pb2.Initiator
        place: _common_pb2.Airbase
        def __init__(self, initiator: _Optional[_Union[_common_pb2.Initiator, _Mapping]] = ..., place: _Optional[_Union[_common_pb2.Airbase, _Mapping]] = ...) -> None: ...
    class EngineShutdownEvent(_message.Message):
        __slots__ = ("initiator", "place")
        INITIATOR_FIELD_NUMBER: _ClassVar[int]
        PLACE_FIELD_NUMBER: _ClassVar[int]
        initiator: _common_pb2.Initiator
        place: _common_pb2.Airbase
        def __init__(self, initiator: _Optional[_Union[_common_pb2.Initiator, _Mapping]] = ..., place: _Optional[_Union[_common_pb2.Airbase, _Mapping]] = ...) -> None: ...
    class PlayerEnterUnitEvent(_message.Message):
        __slots__ = ("initiator",)
        INITIATOR_FIELD_NUMBER: _ClassVar[int]
        initiator: _common_pb2.Initiator
        def __init__(self, initiator: _Optional[_Union[_common_pb2.Initiator, _Mapping]] = ...) -> None: ...
    class PlayerLeaveUnitEvent(_message.Message):
        __slots__ = ("initiator",)
        INITIATOR_FIELD_NUMBER: _ClassVar[int]
        initiator: _common_pb2.Initiator
        def __init__(self, initiator: _Optional[_Union[_common_pb2.Initiator, _Mapping]] = ...) -> None: ...
    class ShootingStartEvent(_message.Message):
        __slots__ = ("initiator", "weapon_name")
        INITIATOR_FIELD_NUMBER: _ClassVar[int]
        WEAPON_NAME_FIELD_NUMBER: _ClassVar[int]
        initiator: _common_pb2.Initiator
        weapon_name: str
        def __init__(self, initiator: _Optional[_Union[_common_pb2.Initiator, _Mapping]] = ..., weapon_name: _Optional[str] = ...) -> None: ...
    class ShootingEndEvent(_message.Message):
        __slots__ = ("initiator", "weapon_name")
        INITIATOR_FIELD_NUMBER: _ClassVar[int]
        WEAPON_NAME_FIELD_NUMBER: _ClassVar[int]
        initiator: _common_pb2.Initiator
        weapon_name: str
        def __init__(self, initiator: _Optional[_Union[_common_pb2.Initiator, _Mapping]] = ..., weapon_name: _Optional[str] = ...) -> None: ...
    class MarkAddEvent(_message.Message):
        __slots__ = ("initiator", "group_id", "coalition", "id", "position", "text")
        INITIATOR_FIELD_NUMBER: _ClassVar[int]
        GROUP_ID_FIELD_NUMBER: _ClassVar[int]
        COALITION_FIELD_NUMBER: _ClassVar[int]
        ID_FIELD_NUMBER: _ClassVar[int]
        POSITION_FIELD_NUMBER: _ClassVar[int]
        TEXT_FIELD_NUMBER: _ClassVar[int]
        initiator: _common_pb2.Initiator
        group_id: int
        coalition: _common_pb2.Coalition
        id: int
        position: _common_pb2.Position
        text: str
        def __init__(self, initiator: _Optional[_Union[_common_pb2.Initiator, _Mapping]] = ..., group_id: _Optional[int] = ..., coalition: _Optional[_Union[_common_pb2.Coalition, str]] = ..., id: _Optional[int] = ..., position: _Optional[_Union[_common_pb2.Position, _Mapping]] = ..., text: _Optional[str] = ...) -> None: ...
    class MarkChangeEvent(_message.Message):
        __slots__ = ("initiator", "group_id", "coalition", "id", "position", "text")
        INITIATOR_FIELD_NUMBER: _ClassVar[int]
        GROUP_ID_FIELD_NUMBER: _ClassVar[int]
        COALITION_FIELD_NUMBER: _ClassVar[int]
        ID_FIELD_NUMBER: _ClassVar[int]
        POSITION_FIELD_NUMBER: _ClassVar[int]
        TEXT_FIELD_NUMBER: _ClassVar[int]
        initiator: _common_pb2.Initiator
        group_id: int
        coalition: _common_pb2.Coalition
        id: int
        position: _common_pb2.Position
        text: str
        def __init__(self, initiator: _Optional[_Union[_common_pb2.Initiator, _Mapping]] = ..., group_id: _Optional[int] = ..., coalition: _Optional[_Union[_common_pb2.Coalition, str]] = ..., id: _Optional[int] = ..., position: _Optional[_Union[_common_pb2.Position, _Mapping]] = ..., text: _Optional[str] = ...) -> None: ...
    class MarkRemoveEvent(_message.Message):
        __slots__ = ("initiator", "group_id", "coalition", "id", "position", "text")
        INITIATOR_FIELD_NUMBER: _ClassVar[int]
        GROUP_ID_FIELD_NUMBER: _ClassVar[int]
        COALITION_FIELD_NUMBER: _ClassVar[int]
        ID_FIELD_NUMBER: _ClassVar[int]
        POSITION_FIELD_NUMBER: _ClassVar[int]
        TEXT_FIELD_NUMBER: _ClassVar[int]
        initiator: _common_pb2.Initiator
        group_id: int
        coalition: _common_pb2.Coalition
        id: int
        position: _common_pb2.Position
        text: str
        def __init__(self, initiator: _Optional[_Union[_common_pb2.Initiator, _Mapping]] = ..., group_id: _Optional[int] = ..., coalition: _Optional[_Union[_common_pb2.Coalition, str]] = ..., id: _Optional[int] = ..., position: _Optional[_Union[_common_pb2.Position, _Mapping]] = ..., text: _Optional[str] = ...) -> None: ...
    class KillEvent(_message.Message):
        __slots__ = ("initiator", "weapon", "target", "weapon_name")
        INITIATOR_FIELD_NUMBER: _ClassVar[int]
        WEAPON_FIELD_NUMBER: _ClassVar[int]
        TARGET_FIELD_NUMBER: _ClassVar[int]
        WEAPON_NAME_FIELD_NUMBER: _ClassVar[int]
        initiator: _common_pb2.Initiator
        weapon: _common_pb2.Weapon
        target: _common_pb2.Target
        weapon_name: str
        def __init__(self, initiator: _Optional[_Union[_common_pb2.Initiator, _Mapping]] = ..., weapon: _Optional[_Union[_common_pb2.Weapon, _Mapping]] = ..., target: _Optional[_Union[_common_pb2.Target, _Mapping]] = ..., weapon_name: _Optional[str] = ...) -> None: ...
    class ScoreEvent(_message.Message):
        __slots__ = ()
        def __init__(self) -> None: ...
    class UnitLostEvent(_message.Message):
        __slots__ = ("initiator",)
        INITIATOR_FIELD_NUMBER: _ClassVar[int]
        initiator: _common_pb2.Initiator
        def __init__(self, initiator: _Optional[_Union[_common_pb2.Initiator, _Mapping]] = ...) -> None: ...
    class LandingAfterEjectionEvent(_message.Message):
        __slots__ = ("initiator", "place")
        INITIATOR_FIELD_NUMBER: _ClassVar[int]
        PLACE_FIELD_NUMBER: _ClassVar[int]
        initiator: _common_pb2.Initiator
        place: _common_pb2.Position
        def __init__(self, initiator: _Optional[_Union[_common_pb2.Initiator, _Mapping]] = ..., place: _Optional[_Union[_common_pb2.Position, _Mapping]] = ...) -> None: ...
    class DiscardChairAfterEjectionEvent(_message.Message):
        __slots__ = ("initiator", "target")
        INITIATOR_FIELD_NUMBER: _ClassVar[int]
        TARGET_FIELD_NUMBER: _ClassVar[int]
        initiator: _common_pb2.Initiator
        target: _common_pb2.Target
        def __init__(self, initiator: _Optional[_Union[_common_pb2.Initiator, _Mapping]] = ..., target: _Optional[_Union[_common_pb2.Target, _Mapping]] = ...) -> None: ...
    class WeaponAddEvent(_message.Message):
        __slots__ = ("initiator", "weapon_name")
        INITIATOR_FIELD_NUMBER: _ClassVar[int]
        WEAPON_NAME_FIELD_NUMBER: _ClassVar[int]
        initiator: _common_pb2.Initiator
        weapon_name: str
        def __init__(self, initiator: _Optional[_Union[_common_pb2.Initiator, _Mapping]] = ..., weapon_name: _Optional[str] = ...) -> None: ...
    class LandingQualityMarkEvent(_message.Message):
        __slots__ = ("initiator", "comment", "place")
        INITIATOR_FIELD_NUMBER: _ClassVar[int]
        COMMENT_FIELD_NUMBER: _ClassVar[int]
        PLACE_FIELD_NUMBER: _ClassVar[int]
        initiator: _common_pb2.Initiator
        comment: str
        place: _common_pb2.Airbase
        def __init__(self, initiator: _Optional[_Union[_common_pb2.Initiator, _Mapping]] = ..., comment: _Optional[str] = ..., place: _Optional[_Union[_common_pb2.Airbase, _Mapping]] = ...) -> None: ...
    class PlayerSendChatEvent(_message.Message):
        __slots__ = ("player_id", "message")
        PLAYER_ID_FIELD_NUMBER: _ClassVar[int]
        MESSAGE_FIELD_NUMBER: _ClassVar[int]
        player_id: int
        message: str
        def __init__(self, player_id: _Optional[int] = ..., message: _Optional[str] = ...) -> None: ...
    class PlayerChangeSlotEvent(_message.Message):
        __slots__ = ("player_id", "coalition", "slot_id")
        PLAYER_ID_FIELD_NUMBER: _ClassVar[int]
        COALITION_FIELD_NUMBER: _ClassVar[int]
        SLOT_ID_FIELD_NUMBER: _ClassVar[int]
        player_id: int
        coalition: _common_pb2.Coalition
        slot_id: str
        def __init__(self, player_id: _Optional[int] = ..., coalition: _Optional[_Union[_common_pb2.Coalition, str]] = ..., slot_id: _Optional[str] = ...) -> None: ...
    class ConnectEvent(_message.Message):
        __slots__ = ("addr", "name", "ucid", "id")
        ADDR_FIELD_NUMBER: _ClassVar[int]
        NAME_FIELD_NUMBER: _ClassVar[int]
        UCID_FIELD_NUMBER: _ClassVar[int]
        ID_FIELD_NUMBER: _ClassVar[int]
        addr: str
        name: str
        ucid: str
        id: int
        def __init__(self, addr: _Optional[str] = ..., name: _Optional[str] = ..., ucid: _Optional[str] = ..., id: _Optional[int] = ...) -> None: ...
    class DisconnectEvent(_message.Message):
        __slots__ = ("id", "reason")
        ID_FIELD_NUMBER: _ClassVar[int]
        REASON_FIELD_NUMBER: _ClassVar[int]
        id: int
        reason: StreamEventsResponse.DisconnectReason
        def __init__(self, id: _Optional[int] = ..., reason: _Optional[_Union[StreamEventsResponse.DisconnectReason, str]] = ...) -> None: ...
    class MissionCommandEvent(_message.Message):
        __slots__ = ("details",)
        DETAILS_FIELD_NUMBER: _ClassVar[int]
        details: _struct_pb2.Struct
        def __init__(self, details: _Optional[_Union[_struct_pb2.Struct, _Mapping]] = ...) -> None: ...
    class CoalitionCommandEvent(_message.Message):
        __slots__ = ("coalition", "details")
        COALITION_FIELD_NUMBER: _ClassVar[int]
        DETAILS_FIELD_NUMBER: _ClassVar[int]
        coalition: _common_pb2.Coalition
        details: _struct_pb2.Struct
        def __init__(self, coalition: _Optional[_Union[_common_pb2.Coalition, str]] = ..., details: _Optional[_Union[_struct_pb2.Struct, _Mapping]] = ...) -> None: ...
    class GroupCommandEvent(_message.Message):
        __slots__ = ("group", "details")
        GROUP_FIELD_NUMBER: _ClassVar[int]
        DETAILS_FIELD_NUMBER: _ClassVar[int]
        group: _common_pb2.Group
        details: _struct_pb2.Struct
        def __init__(self, group: _Optional[_Union[_common_pb2.Group, _Mapping]] = ..., details: _Optional[_Union[_struct_pb2.Struct, _Mapping]] = ...) -> None: ...
    class SimulationFpsEvent(_message.Message):
        __slots__ = ("average",)
        AVERAGE_FIELD_NUMBER: _ClassVar[int]
        average: float
        def __init__(self, average: _Optional[float] = ...) -> None: ...
    class TtsEvent(_message.Message):
        __slots__ = ("text", "frequency", "coalition", "srs_client_name")
        TEXT_FIELD_NUMBER: _ClassVar[int]
        FREQUENCY_FIELD_NUMBER: _ClassVar[int]
        COALITION_FIELD_NUMBER: _ClassVar[int]
        SRS_CLIENT_NAME_FIELD_NUMBER: _ClassVar[int]
        text: str
        frequency: int
        coalition: _common_pb2.Coalition
        srs_client_name: str
        def __init__(self, text: _Optional[str] = ..., frequency: _Optional[int] = ..., coalition: _Optional[_Union[_common_pb2.Coalition, str]] = ..., srs_client_name: _Optional[str] = ...) -> None: ...
    class SrsConnectEvent(_message.Message):
        __slots__ = ("unit", "frequency")
        UNIT_FIELD_NUMBER: _ClassVar[int]
        FREQUENCY_FIELD_NUMBER: _ClassVar[int]
        unit: _common_pb2.Unit
        frequency: int
        def __init__(self, unit: _Optional[_Union[_common_pb2.Unit, _Mapping]] = ..., frequency: _Optional[int] = ...) -> None: ...
    class SrsDisconnectEvent(_message.Message):
        __slots__ = ("unit", "frequency")
        UNIT_FIELD_NUMBER: _ClassVar[int]
        FREQUENCY_FIELD_NUMBER: _ClassVar[int]
        unit: _common_pb2.Unit
        frequency: int
        def __init__(self, unit: _Optional[_Union[_common_pb2.Unit, _Mapping]] = ..., frequency: _Optional[int] = ...) -> None: ...
    TIME_FIELD_NUMBER: _ClassVar[int]
    SHOT_FIELD_NUMBER: _ClassVar[int]
    HIT_FIELD_NUMBER: _ClassVar[int]
    TAKEOFF_FIELD_NUMBER: _ClassVar[int]
    LAND_FIELD_NUMBER: _ClassVar[int]
    CRASH_FIELD_NUMBER: _ClassVar[int]
    EJECTION_FIELD_NUMBER: _ClassVar[int]
    REFUELING_FIELD_NUMBER: _ClassVar[int]
    DEAD_FIELD_NUMBER: _ClassVar[int]
    PILOT_DEAD_FIELD_NUMBER: _ClassVar[int]
    BASE_CAPTURE_FIELD_NUMBER: _ClassVar[int]
    MISSION_START_FIELD_NUMBER: _ClassVar[int]
    MISSION_END_FIELD_NUMBER: _ClassVar[int]
    REFUELING_STOP_FIELD_NUMBER: _ClassVar[int]
    BIRTH_FIELD_NUMBER: _ClassVar[int]
    HUMAN_FAILURE_FIELD_NUMBER: _ClassVar[int]
    DETAILED_FAILURE_FIELD_NUMBER: _ClassVar[int]
    ENGINE_STARTUP_FIELD_NUMBER: _ClassVar[int]
    ENGINE_SHUTDOWN_FIELD_NUMBER: _ClassVar[int]
    PLAYER_ENTER_UNIT_FIELD_NUMBER: _ClassVar[int]
    PLAYER_LEAVE_UNIT_FIELD_NUMBER: _ClassVar[int]
    SHOOTING_START_FIELD_NUMBER: _ClassVar[int]
    SHOOTING_END_FIELD_NUMBER: _ClassVar[int]
    MARK_ADD_FIELD_NUMBER: _ClassVar[int]
    MARK_CHANGE_FIELD_NUMBER: _ClassVar[int]
    MARK_REMOVE_FIELD_NUMBER: _ClassVar[int]
    KILL_FIELD_NUMBER: _ClassVar[int]
    SCORE_FIELD_NUMBER: _ClassVar[int]
    UNIT_LOST_FIELD_NUMBER: _ClassVar[int]
    LANDING_AFTER_EJECTION_FIELD_NUMBER: _ClassVar[int]
    DISCARD_CHAIR_AFTER_EJECTION_FIELD_NUMBER: _ClassVar[int]
    WEAPON_ADD_FIELD_NUMBER: _ClassVar[int]
    LANDING_QUALITY_MARK_FIELD_NUMBER: _ClassVar[int]
    RUNWAY_TAKEOFF_FIELD_NUMBER: _ClassVar[int]
    RUNWAY_TOUCH_FIELD_NUMBER: _ClassVar[int]
    CONNECT_FIELD_NUMBER: _ClassVar[int]
    DISCONNECT_FIELD_NUMBER: _ClassVar[int]
    PLAYER_SEND_CHAT_FIELD_NUMBER: _ClassVar[int]
    PLAYER_CHANGE_SLOT_FIELD_NUMBER: _ClassVar[int]
    MISSION_COMMAND_FIELD_NUMBER: _ClassVar[int]
    COALITION_COMMAND_FIELD_NUMBER: _ClassVar[int]
    GROUP_COMMAND_FIELD_NUMBER: _ClassVar[int]
    SIMULATION_FPS_FIELD_NUMBER: _ClassVar[int]
    TTS_FIELD_NUMBER: _ClassVar[int]
    SRS_CONNECT_FIELD_NUMBER: _ClassVar[int]
    SRS_DISCONNECT_FIELD_NUMBER: _ClassVar[int]
    time: float
    shot: StreamEventsResponse.ShotEvent
    hit: StreamEventsResponse.HitEvent
    takeoff: StreamEventsResponse.TakeoffEvent
    land: StreamEventsResponse.LandEvent
    crash: StreamEventsResponse.CrashEvent
    ejection: StreamEventsResponse.EjectionEvent
    refueling: StreamEventsResponse.RefuelingEvent
    dead: StreamEventsResponse.DeadEvent
    pilot_dead: StreamEventsResponse.PilotDeadEvent
    base_capture: StreamEventsResponse.BaseCaptureEvent
    mission_start: StreamEventsResponse.MissionStartEvent
    mission_end: StreamEventsResponse.MissionEndEvent
    refueling_stop: StreamEventsResponse.RefuelingStopEvent
    birth: StreamEventsResponse.BirthEvent
    human_failure: StreamEventsResponse.HumanFailureEvent
    detailed_failure: StreamEventsResponse.DetailedFailureEvent
    engine_startup: StreamEventsResponse.EngineStartupEvent
    engine_shutdown: StreamEventsResponse.EngineShutdownEvent
    player_enter_unit: StreamEventsResponse.PlayerEnterUnitEvent
    player_leave_unit: StreamEventsResponse.PlayerLeaveUnitEvent
    shooting_start: StreamEventsResponse.ShootingStartEvent
    shooting_end: StreamEventsResponse.ShootingEndEvent
    mark_add: StreamEventsResponse.MarkAddEvent
    mark_change: StreamEventsResponse.MarkChangeEvent
    mark_remove: StreamEventsResponse.MarkRemoveEvent
    kill: StreamEventsResponse.KillEvent
    score: StreamEventsResponse.ScoreEvent
    unit_lost: StreamEventsResponse.UnitLostEvent
    landing_after_ejection: StreamEventsResponse.LandingAfterEjectionEvent
    discard_chair_after_ejection: StreamEventsResponse.DiscardChairAfterEjectionEvent
    weapon_add: StreamEventsResponse.WeaponAddEvent
    landing_quality_mark: StreamEventsResponse.LandingQualityMarkEvent
    runway_takeoff: StreamEventsResponse.RunwayTakeoffEvent
    runway_touch: StreamEventsResponse.RunwayTouchEvent
    connect: StreamEventsResponse.ConnectEvent
    disconnect: StreamEventsResponse.DisconnectEvent
    player_send_chat: StreamEventsResponse.PlayerSendChatEvent
    player_change_slot: StreamEventsResponse.PlayerChangeSlotEvent
    mission_command: StreamEventsResponse.MissionCommandEvent
    coalition_command: StreamEventsResponse.CoalitionCommandEvent
    group_command: StreamEventsResponse.GroupCommandEvent
    simulation_fps: StreamEventsResponse.SimulationFpsEvent
    tts: StreamEventsResponse.TtsEvent
    srs_connect: StreamEventsResponse.SrsConnectEvent
    srs_disconnect: StreamEventsResponse.SrsDisconnectEvent
    def __init__(self, time: _Optional[float] = ..., shot: _Optional[_Union[StreamEventsResponse.ShotEvent, _Mapping]] = ..., hit: _Optional[_Union[StreamEventsResponse.HitEvent, _Mapping]] = ..., takeoff: _Optional[_Union[StreamEventsResponse.TakeoffEvent, _Mapping]] = ..., land: _Optional[_Union[StreamEventsResponse.LandEvent, _Mapping]] = ..., crash: _Optional[_Union[StreamEventsResponse.CrashEvent, _Mapping]] = ..., ejection: _Optional[_Union[StreamEventsResponse.EjectionEvent, _Mapping]] = ..., refueling: _Optional[_Union[StreamEventsResponse.RefuelingEvent, _Mapping]] = ..., dead: _Optional[_Union[StreamEventsResponse.DeadEvent, _Mapping]] = ..., pilot_dead: _Optional[_Union[StreamEventsResponse.PilotDeadEvent, _Mapping]] = ..., base_capture: _Optional[_Union[StreamEventsResponse.BaseCaptureEvent, _Mapping]] = ..., mission_start: _Optional[_Union[StreamEventsResponse.MissionStartEvent, _Mapping]] = ..., mission_end: _Optional[_Union[StreamEventsResponse.MissionEndEvent, _Mapping]] = ..., refueling_stop: _Optional[_Union[StreamEventsResponse.RefuelingStopEvent, _Mapping]] = ..., birth: _Optional[_Union[StreamEventsResponse.BirthEvent, _Mapping]] = ..., human_failure: _Optional[_Union[StreamEventsResponse.HumanFailureEvent, _Mapping]] = ..., detailed_failure: _Optional[_Union[StreamEventsResponse.DetailedFailureEvent, _Mapping]] = ..., engine_startup: _Optional[_Union[StreamEventsResponse.EngineStartupEvent, _Mapping]] = ..., engine_shutdown: _Optional[_Union[StreamEventsResponse.EngineShutdownEvent, _Mapping]] = ..., player_enter_unit: _Optional[_Union[StreamEventsResponse.PlayerEnterUnitEvent, _Mapping]] = ..., player_leave_unit: _Optional[_Union[StreamEventsResponse.PlayerLeaveUnitEvent, _Mapping]] = ..., shooting_start: _Optional[_Union[StreamEventsResponse.ShootingStartEvent, _Mapping]] = ..., shooting_end: _Optional[_Union[StreamEventsResponse.ShootingEndEvent, _Mapping]] = ..., mark_add: _Optional[_Union[StreamEventsResponse.MarkAddEvent, _Mapping]] = ..., mark_change: _Optional[_Union[StreamEventsResponse.MarkChangeEvent, _Mapping]] = ..., mark_remove: _Optional[_Union[StreamEventsResponse.MarkRemoveEvent, _Mapping]] = ..., kill: _Optional[_Union[StreamEventsResponse.KillEvent, _Mapping]] = ..., score: _Optional[_Union[StreamEventsResponse.ScoreEvent, _Mapping]] = ..., unit_lost: _Optional[_Union[StreamEventsResponse.UnitLostEvent, _Mapping]] = ..., landing_after_ejection: _Optional[_Union[StreamEventsResponse.LandingAfterEjectionEvent, _Mapping]] = ..., discard_chair_after_ejection: _Optional[_Union[StreamEventsResponse.DiscardChairAfterEjectionEvent, _Mapping]] = ..., weapon_add: _Optional[_Union[StreamEventsResponse.WeaponAddEvent, _Mapping]] = ..., landing_quality_mark: _Optional[_Union[StreamEventsResponse.LandingQualityMarkEvent, _Mapping]] = ..., runway_takeoff: _Optional[_Union[StreamEventsResponse.RunwayTakeoffEvent, _Mapping]] = ..., runway_touch: _Optional[_Union[StreamEventsResponse.RunwayTouchEvent, _Mapping]] = ..., connect: _Optional[_Union[StreamEventsResponse.ConnectEvent, _Mapping]] = ..., disconnect: _Optional[_Union[StreamEventsResponse.DisconnectEvent, _Mapping]] = ..., player_send_chat: _Optional[_Union[StreamEventsResponse.PlayerSendChatEvent, _Mapping]] = ..., player_change_slot: _Optional[_Union[StreamEventsResponse.PlayerChangeSlotEvent, _Mapping]] = ..., mission_command: _Optional[_Union[StreamEventsResponse.MissionCommandEvent, _Mapping]] = ..., coalition_command: _Optional[_Union[StreamEventsResponse.CoalitionCommandEvent, _Mapping]] = ..., group_command: _Optional[_Union[StreamEventsResponse.GroupCommandEvent, _Mapping]] = ..., simulation_fps: _Optional[_Union[StreamEventsResponse.SimulationFpsEvent, _Mapping]] = ..., tts: _Optional[_Union[StreamEventsResponse.TtsEvent, _Mapping]] = ..., srs_connect: _Optional[_Union[StreamEventsResponse.SrsConnectEvent, _Mapping]] = ..., srs_disconnect: _Optional[_Union[StreamEventsResponse.SrsDisconnectEvent, _Mapping]] = ...) -> None: ...

class StreamUnitsRequest(_message.Message):
    __slots__ = ("poll_rate", "max_backoff", "category")
    POLL_RATE_FIELD_NUMBER: _ClassVar[int]
    MAX_BACKOFF_FIELD_NUMBER: _ClassVar[int]
    CATEGORY_FIELD_NUMBER: _ClassVar[int]
    poll_rate: int
    max_backoff: int
    category: _common_pb2.GroupCategory
    def __init__(self, poll_rate: _Optional[int] = ..., max_backoff: _Optional[int] = ..., category: _Optional[_Union[_common_pb2.GroupCategory, str]] = ...) -> None: ...

class StreamUnitsResponse(_message.Message):
    __slots__ = ("time", "unit", "gone")
    class UnitGone(_message.Message):
        __slots__ = ("id", "name")
        ID_FIELD_NUMBER: _ClassVar[int]
        NAME_FIELD_NUMBER: _ClassVar[int]
        id: int
        name: str
        def __init__(self, id: _Optional[int] = ..., name: _Optional[str] = ...) -> None: ...
    TIME_FIELD_NUMBER: _ClassVar[int]
    UNIT_FIELD_NUMBER: _ClassVar[int]
    GONE_FIELD_NUMBER: _ClassVar[int]
    time: float
    unit: _common_pb2.Unit
    gone: StreamUnitsResponse.UnitGone
    def __init__(self, time: _Optional[float] = ..., unit: _Optional[_Union[_common_pb2.Unit, _Mapping]] = ..., gone: _Optional[_Union[StreamUnitsResponse.UnitGone, _Mapping]] = ...) -> None: ...

class GetScenarioStartTimeRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class GetScenarioStartTimeResponse(_message.Message):
    __slots__ = ("datetime",)
    DATETIME_FIELD_NUMBER: _ClassVar[int]
    datetime: str
    def __init__(self, datetime: _Optional[str] = ...) -> None: ...

class GetScenarioCurrentTimeRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class GetScenarioCurrentTimeResponse(_message.Message):
    __slots__ = ("datetime",)
    DATETIME_FIELD_NUMBER: _ClassVar[int]
    datetime: str
    def __init__(self, datetime: _Optional[str] = ...) -> None: ...

class AddMissionCommandRequest(_message.Message):
    __slots__ = ("name", "path", "details")
    NAME_FIELD_NUMBER: _ClassVar[int]
    PATH_FIELD_NUMBER: _ClassVar[int]
    DETAILS_FIELD_NUMBER: _ClassVar[int]
    name: str
    path: _containers.RepeatedScalarFieldContainer[str]
    details: _struct_pb2.Struct
    def __init__(self, name: _Optional[str] = ..., path: _Optional[_Iterable[str]] = ..., details: _Optional[_Union[_struct_pb2.Struct, _Mapping]] = ...) -> None: ...

class AddMissionCommandResponse(_message.Message):
    __slots__ = ("path",)
    PATH_FIELD_NUMBER: _ClassVar[int]
    path: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, path: _Optional[_Iterable[str]] = ...) -> None: ...

class AddMissionCommandSubMenuRequest(_message.Message):
    __slots__ = ("name", "path")
    NAME_FIELD_NUMBER: _ClassVar[int]
    PATH_FIELD_NUMBER: _ClassVar[int]
    name: str
    path: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, name: _Optional[str] = ..., path: _Optional[_Iterable[str]] = ...) -> None: ...

class AddMissionCommandSubMenuResponse(_message.Message):
    __slots__ = ("path",)
    PATH_FIELD_NUMBER: _ClassVar[int]
    path: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, path: _Optional[_Iterable[str]] = ...) -> None: ...

class RemoveMissionCommandItemRequest(_message.Message):
    __slots__ = ("path",)
    PATH_FIELD_NUMBER: _ClassVar[int]
    path: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, path: _Optional[_Iterable[str]] = ...) -> None: ...

class RemoveMissionCommandItemResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class AddCoalitionCommandRequest(_message.Message):
    __slots__ = ("coalition", "name", "path", "details")
    COALITION_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    PATH_FIELD_NUMBER: _ClassVar[int]
    DETAILS_FIELD_NUMBER: _ClassVar[int]
    coalition: _common_pb2.Coalition
    name: str
    path: _containers.RepeatedScalarFieldContainer[str]
    details: _struct_pb2.Struct
    def __init__(self, coalition: _Optional[_Union[_common_pb2.Coalition, str]] = ..., name: _Optional[str] = ..., path: _Optional[_Iterable[str]] = ..., details: _Optional[_Union[_struct_pb2.Struct, _Mapping]] = ...) -> None: ...

class AddCoalitionCommandResponse(_message.Message):
    __slots__ = ("path",)
    PATH_FIELD_NUMBER: _ClassVar[int]
    path: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, path: _Optional[_Iterable[str]] = ...) -> None: ...

class AddCoalitionCommandSubMenuRequest(_message.Message):
    __slots__ = ("coalition", "name", "path")
    COALITION_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    PATH_FIELD_NUMBER: _ClassVar[int]
    coalition: _common_pb2.Coalition
    name: str
    path: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, coalition: _Optional[_Union[_common_pb2.Coalition, str]] = ..., name: _Optional[str] = ..., path: _Optional[_Iterable[str]] = ...) -> None: ...

class AddCoalitionCommandSubMenuResponse(_message.Message):
    __slots__ = ("path",)
    PATH_FIELD_NUMBER: _ClassVar[int]
    path: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, path: _Optional[_Iterable[str]] = ...) -> None: ...

class RemoveCoalitionCommandItemRequest(_message.Message):
    __slots__ = ("coalition", "path")
    COALITION_FIELD_NUMBER: _ClassVar[int]
    PATH_FIELD_NUMBER: _ClassVar[int]
    coalition: _common_pb2.Coalition
    path: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, coalition: _Optional[_Union[_common_pb2.Coalition, str]] = ..., path: _Optional[_Iterable[str]] = ...) -> None: ...

class RemoveCoalitionCommandItemResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class AddGroupCommandRequest(_message.Message):
    __slots__ = ("group_name", "name", "path", "details")
    GROUP_NAME_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    PATH_FIELD_NUMBER: _ClassVar[int]
    DETAILS_FIELD_NUMBER: _ClassVar[int]
    group_name: str
    name: str
    path: _containers.RepeatedScalarFieldContainer[str]
    details: _struct_pb2.Struct
    def __init__(self, group_name: _Optional[str] = ..., name: _Optional[str] = ..., path: _Optional[_Iterable[str]] = ..., details: _Optional[_Union[_struct_pb2.Struct, _Mapping]] = ...) -> None: ...

class AddGroupCommandResponse(_message.Message):
    __slots__ = ("path",)
    PATH_FIELD_NUMBER: _ClassVar[int]
    path: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, path: _Optional[_Iterable[str]] = ...) -> None: ...

class AddGroupCommandSubMenuRequest(_message.Message):
    __slots__ = ("group_name", "name", "path")
    GROUP_NAME_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    PATH_FIELD_NUMBER: _ClassVar[int]
    group_name: str
    name: str
    path: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, group_name: _Optional[str] = ..., name: _Optional[str] = ..., path: _Optional[_Iterable[str]] = ...) -> None: ...

class AddGroupCommandSubMenuResponse(_message.Message):
    __slots__ = ("path",)
    PATH_FIELD_NUMBER: _ClassVar[int]
    path: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, path: _Optional[_Iterable[str]] = ...) -> None: ...

class RemoveGroupCommandItemRequest(_message.Message):
    __slots__ = ("group_name", "path")
    GROUP_NAME_FIELD_NUMBER: _ClassVar[int]
    PATH_FIELD_NUMBER: _ClassVar[int]
    group_name: str
    path: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, group_name: _Optional[str] = ..., path: _Optional[_Iterable[str]] = ...) -> None: ...

class RemoveGroupCommandItemResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class GetSessionIdRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class GetSessionIdResponse(_message.Message):
    __slots__ = ("session_id",)
    SESSION_ID_FIELD_NUMBER: _ClassVar[int]
    session_id: int
    def __init__(self, session_id: _Optional[int] = ...) -> None: ...
