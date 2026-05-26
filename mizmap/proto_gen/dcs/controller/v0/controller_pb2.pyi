from dcs.common.v0 import common_pb2 as _common_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class SetAlarmStateRequest(_message.Message):
    __slots__ = ("group_name", "unit_name", "alarm_state")
    class AlarmState(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        ALARM_STATE_UNSPECIFIED: _ClassVar[SetAlarmStateRequest.AlarmState]
        ALARM_STATE_AUTO: _ClassVar[SetAlarmStateRequest.AlarmState]
        ALARM_STATE_GREEN: _ClassVar[SetAlarmStateRequest.AlarmState]
        ALARM_STATE_RED: _ClassVar[SetAlarmStateRequest.AlarmState]
    ALARM_STATE_UNSPECIFIED: SetAlarmStateRequest.AlarmState
    ALARM_STATE_AUTO: SetAlarmStateRequest.AlarmState
    ALARM_STATE_GREEN: SetAlarmStateRequest.AlarmState
    ALARM_STATE_RED: SetAlarmStateRequest.AlarmState
    GROUP_NAME_FIELD_NUMBER: _ClassVar[int]
    UNIT_NAME_FIELD_NUMBER: _ClassVar[int]
    ALARM_STATE_FIELD_NUMBER: _ClassVar[int]
    group_name: str
    unit_name: str
    alarm_state: SetAlarmStateRequest.AlarmState
    def __init__(self, group_name: _Optional[str] = ..., unit_name: _Optional[str] = ..., alarm_state: _Optional[_Union[SetAlarmStateRequest.AlarmState, str]] = ...) -> None: ...

class SetAlarmStateResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class GetDetectedTargetsRequest(_message.Message):
    __slots__ = ("unit_name", "include_object", "detection_type")
    class DetectionType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        DETECTION_TYPE_UNSPECIFIED: _ClassVar[GetDetectedTargetsRequest.DetectionType]
        DETECTION_TYPE_VISUAL: _ClassVar[GetDetectedTargetsRequest.DetectionType]
        DETECTION_TYPE_OPTIC: _ClassVar[GetDetectedTargetsRequest.DetectionType]
        DETECTION_TYPE_RADAR: _ClassVar[GetDetectedTargetsRequest.DetectionType]
        DETECTION_TYPE_IRST: _ClassVar[GetDetectedTargetsRequest.DetectionType]
        DETECTION_TYPE_RWR: _ClassVar[GetDetectedTargetsRequest.DetectionType]
        DETECTION_TYPE_DLINK: _ClassVar[GetDetectedTargetsRequest.DetectionType]
    DETECTION_TYPE_UNSPECIFIED: GetDetectedTargetsRequest.DetectionType
    DETECTION_TYPE_VISUAL: GetDetectedTargetsRequest.DetectionType
    DETECTION_TYPE_OPTIC: GetDetectedTargetsRequest.DetectionType
    DETECTION_TYPE_RADAR: GetDetectedTargetsRequest.DetectionType
    DETECTION_TYPE_IRST: GetDetectedTargetsRequest.DetectionType
    DETECTION_TYPE_RWR: GetDetectedTargetsRequest.DetectionType
    DETECTION_TYPE_DLINK: GetDetectedTargetsRequest.DetectionType
    UNIT_NAME_FIELD_NUMBER: _ClassVar[int]
    INCLUDE_OBJECT_FIELD_NUMBER: _ClassVar[int]
    DETECTION_TYPE_FIELD_NUMBER: _ClassVar[int]
    unit_name: str
    include_object: bool
    detection_type: GetDetectedTargetsRequest.DetectionType
    def __init__(self, unit_name: _Optional[str] = ..., include_object: bool = ..., detection_type: _Optional[_Union[GetDetectedTargetsRequest.DetectionType, str]] = ...) -> None: ...

class GetDetectedTargetsResponse(_message.Message):
    __slots__ = ("contacts",)
    CONTACTS_FIELD_NUMBER: _ClassVar[int]
    contacts: _containers.RepeatedCompositeFieldContainer[_common_pb2.Contact]
    def __init__(self, contacts: _Optional[_Iterable[_Union[_common_pb2.Contact, _Mapping]]] = ...) -> None: ...
