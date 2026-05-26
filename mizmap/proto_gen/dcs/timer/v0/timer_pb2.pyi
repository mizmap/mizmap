from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Optional as _Optional

DESCRIPTOR: _descriptor.FileDescriptor

class GetTimeRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class GetTimeResponse(_message.Message):
    __slots__ = ("time",)
    TIME_FIELD_NUMBER: _ClassVar[int]
    time: float
    def __init__(self, time: _Optional[float] = ...) -> None: ...

class GetAbsoluteTimeRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class GetAbsoluteTimeResponse(_message.Message):
    __slots__ = ("time", "day", "month", "year")
    TIME_FIELD_NUMBER: _ClassVar[int]
    DAY_FIELD_NUMBER: _ClassVar[int]
    MONTH_FIELD_NUMBER: _ClassVar[int]
    YEAR_FIELD_NUMBER: _ClassVar[int]
    time: float
    day: int
    month: int
    year: int
    def __init__(self, time: _Optional[float] = ..., day: _Optional[int] = ..., month: _Optional[int] = ..., year: _Optional[int] = ...) -> None: ...

class GetTimeZeroRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class GetTimeZeroResponse(_message.Message):
    __slots__ = ("time", "day", "month", "year")
    TIME_FIELD_NUMBER: _ClassVar[int]
    DAY_FIELD_NUMBER: _ClassVar[int]
    MONTH_FIELD_NUMBER: _ClassVar[int]
    YEAR_FIELD_NUMBER: _ClassVar[int]
    time: float
    day: int
    month: int
    year: int
    def __init__(self, time: _Optional[float] = ..., day: _Optional[int] = ..., month: _Optional[int] = ..., year: _Optional[int] = ...) -> None: ...
