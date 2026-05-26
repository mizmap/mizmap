from dcs.common.v0 import common_pb2 as _common_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class TransmitRequest(_message.Message):
    __slots__ = ("ssml", "plaintext", "frequency", "srs_client_name", "position", "coalition", "aws", "azure", "gcloud", "win")
    class Aws(_message.Message):
        __slots__ = ("voice",)
        VOICE_FIELD_NUMBER: _ClassVar[int]
        voice: str
        def __init__(self, voice: _Optional[str] = ...) -> None: ...
    class Azure(_message.Message):
        __slots__ = ("voice",)
        VOICE_FIELD_NUMBER: _ClassVar[int]
        voice: str
        def __init__(self, voice: _Optional[str] = ...) -> None: ...
    class GCloud(_message.Message):
        __slots__ = ("voice",)
        VOICE_FIELD_NUMBER: _ClassVar[int]
        voice: str
        def __init__(self, voice: _Optional[str] = ...) -> None: ...
    class Windows(_message.Message):
        __slots__ = ("voice",)
        VOICE_FIELD_NUMBER: _ClassVar[int]
        voice: str
        def __init__(self, voice: _Optional[str] = ...) -> None: ...
    SSML_FIELD_NUMBER: _ClassVar[int]
    PLAINTEXT_FIELD_NUMBER: _ClassVar[int]
    FREQUENCY_FIELD_NUMBER: _ClassVar[int]
    SRS_CLIENT_NAME_FIELD_NUMBER: _ClassVar[int]
    POSITION_FIELD_NUMBER: _ClassVar[int]
    COALITION_FIELD_NUMBER: _ClassVar[int]
    ASYNC_FIELD_NUMBER: _ClassVar[int]
    AWS_FIELD_NUMBER: _ClassVar[int]
    AZURE_FIELD_NUMBER: _ClassVar[int]
    GCLOUD_FIELD_NUMBER: _ClassVar[int]
    WIN_FIELD_NUMBER: _ClassVar[int]
    ssml: str
    plaintext: str
    frequency: int
    srs_client_name: str
    position: _common_pb2.InputPosition
    coalition: _common_pb2.Coalition
    aws: TransmitRequest.Aws
    azure: TransmitRequest.Azure
    gcloud: TransmitRequest.GCloud
    win: TransmitRequest.Windows
    def __init__(self, ssml: _Optional[str] = ..., plaintext: _Optional[str] = ..., frequency: _Optional[int] = ..., srs_client_name: _Optional[str] = ..., position: _Optional[_Union[_common_pb2.InputPosition, _Mapping]] = ..., coalition: _Optional[_Union[_common_pb2.Coalition, str]] = ..., aws: _Optional[_Union[TransmitRequest.Aws, _Mapping]] = ..., azure: _Optional[_Union[TransmitRequest.Azure, _Mapping]] = ..., gcloud: _Optional[_Union[TransmitRequest.GCloud, _Mapping]] = ..., win: _Optional[_Union[TransmitRequest.Windows, _Mapping]] = ..., **kwargs) -> None: ...

class TransmitResponse(_message.Message):
    __slots__ = ("duration_ms",)
    DURATION_MS_FIELD_NUMBER: _ClassVar[int]
    duration_ms: int
    def __init__(self, duration_ms: _Optional[int] = ...) -> None: ...

class GetClientsRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class GetClientsResponse(_message.Message):
    __slots__ = ("clients",)
    class Client(_message.Message):
        __slots__ = ("unit", "frequencies")
        UNIT_FIELD_NUMBER: _ClassVar[int]
        FREQUENCIES_FIELD_NUMBER: _ClassVar[int]
        unit: _common_pb2.Unit
        frequencies: _containers.RepeatedScalarFieldContainer[int]
        def __init__(self, unit: _Optional[_Union[_common_pb2.Unit, _Mapping]] = ..., frequencies: _Optional[_Iterable[int]] = ...) -> None: ...
    CLIENTS_FIELD_NUMBER: _ClassVar[int]
    clients: _containers.RepeatedCompositeFieldContainer[GetClientsResponse.Client]
    def __init__(self, clients: _Optional[_Iterable[_Union[GetClientsResponse.Client, _Mapping]]] = ...) -> None: ...
