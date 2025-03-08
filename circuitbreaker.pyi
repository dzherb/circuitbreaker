import typing
from collections.abc import (
    Iterable,
    Generator,
    Callable,
    Awaitable,
    AsyncGenerator,
    MutableMapping,
)
from datetime import datetime
from types import TracebackType

type _State = typing.Literal['closed', 'open', 'half_open']

STRING_TYPES: tuple[type[bytes], type[str]]

STATE_CLOSED: typing.Final[_State]
STATE_OPEN: typing.Final[_State]
STATE_HALF_OPEN: typing.Final[_State]

type _PredicateFn = Callable[[type[Exception], Exception], bool]
type _ExpectedException = (
    type[Exception] |
    Iterable[type[Exception]] |
    _PredicateFn
)

type _FallbackFn[T] = (
    Callable[..., typing.Any] |
    Callable[..., Generator[T]] |
    Callable[..., Awaitable[T]] |
    Callable[..., AsyncGenerator[T]]
)

def in_exception_list(
    *exc_types: type[Exception]
) -> _PredicateFn: ...

def build_failure_predicate(
    expected_exception: _ExpectedException
) -> _PredicateFn: ...

_N = typing.TypeVar('_N', str, bytes, default=str)

class CircuitBreaker(typing.Generic[_N]):
    FAILURE_THRESHOLD: typing.ClassVar[int]
    RECOVERY_TIMEOUT: typing.ClassVar[float]
    EXPECTED_EXCEPTION: typing.ClassVar[_ExpectedException]
    FALLBACK_FUNCTION: typing.ClassVar[_FallbackFn | None]

    def __init__(
        self,
        failure_threshold: int | None = None,
        recovery_timeout: float | None = None,
        expected_exception: _ExpectedException | None = None,
        name: _N | None = None,
        fallback_function: _FallbackFn | None = None
     ): ...

    _last_failure: Exception | None
    _failure_count: int
    _failure_threshold: int
    _recovery_timeout: float
    is_failure: _PredicateFn
    _fallback_function: _FallbackFn | None
    _name: _N
    _state: _State
    _opened: float

    @typing.overload
    def __call__[**P, T](
        self,
        wrapped: Callable[P, T]
    ) -> Callable[P, T]: ...

    @typing.overload
    def __call__[**P, T](
        self,
        wrapped: Callable[P, Generator[T]]
    ) -> Callable[P, Generator[T]]: ...

    @typing.overload
    def __call__[**P, T](
        self,
        wrapped: Callable[P, Awaitable[T]]
    ) -> Callable[P, Awaitable[T]]: ...

    @typing.overload
    def __call__[**P, T](
        self,
        wrapped: Callable[P, AsyncGenerator[T]]
    ) -> Callable[P, AsyncGenerator[T]]: ...

    def __enter__(self) -> None: ...

    typing.ContextManager
    def __exit__(
        self,
        exc_type: type[Exception] | None,
        exc_value: Exception | None,
        _traceback: TracebackType | None
    ) -> bool: ...

    @typing.overload
    def decorate[**P, T](
        self,
        function: Callable[P, T]
    ) -> Callable[P, T]: ...

    @typing.overload
    def decorate[**P, T](
        self,
        function: Callable[P, Generator[T]]
    ) -> Callable[P, Generator[T]]: ...

    @typing.overload
    def decorate[**P, T](
        self,
        function: Callable[P, Awaitable[T]]
    ) -> Callable[P, Awaitable[T]]: ...

    @typing.overload
    def decorate[**P, T](
        self,
        function: Callable[P, AsyncGenerator[T]]
    ) -> Callable[P, AsyncGenerator[T]]: ...

    @typing.overload
    def _decorate_sync[**P, T](
        self,
        function: Callable[P, T]
    ) -> Callable[P, T]: ...

    @typing.overload
    def _decorate_sync[**P, T](
        self,
        function: Callable[P, Generator[T]]
    ) -> Callable[P, Generator[T]]: ...

    @typing.overload
    def _decorate_async[**P, T](
        self,
        function: Callable[P, Awaitable[T]]
    ) -> Callable[P, Awaitable[T]]: ...

    @typing.overload
    def _decorate_async[**P, T](
        self,
        function: Callable[P, AsyncGenerator[T]]
    ) -> Callable[P, AsyncGenerator[T]]: ...

    def call[**P, T](
        self,
        func: Callable[P, T],
        *args: P.args,
        **kwargs: P.kwargs
    ) -> T: ...

    def call_generator[**P, T](
        self,
        func: Callable[P, Generator[T]],
        *args: P.args,
        **kwargs: P.kwargs
    ) -> Generator[T]: ...

    async def call_async[**P, T](
        self,
        func: Callable[P, Awaitable[T]],
        *args: P.args,
        **kwargs: P.kwargs
    ) -> Awaitable[T]: ...

    async def call_async_generator[**P, T](
        self,
        func: Callable[P, AsyncGenerator[T]],
        *args: P.args,
        **kwargs: P.kwargs
    ) -> AsyncGenerator[T]: ...

    def __call_succeeded(self) -> None: ...

    def __call_failed(self) -> None: ...

    @property
    def state(self) -> _State: ...

    @property
    def open_until(self) -> datetime: ...

    @property
    def open_remaining(self) -> float: ...

    @property
    def failure_count(self) -> int: ...

    @property
    def closed(self) -> bool: ...

    @property
    def opened(self) -> bool: ...

    @property
    def name(self) -> _N: ...

    @property
    def last_failure(self) -> Exception | None: ...

    @property
    def fallback_function(self) -> _FallbackFn | None: ...

class CircuitBreakerError[_CB: CircuitBreaker](Exception):
    def __init__(
        self,
        circuit_breaker: _CB,
        *args: typing.Any,
        **kwargs: typing.Any
    ): ...

    _circuit_breaker: _CB

class CircuitBreakerMonitor:
    circuit_breakers: MutableMapping[
        str | bytes,
        CircuitBreaker[str] | CircuitBreaker[bytes],
    ] = {}

    @classmethod
    def register[_N: (str, bytes)](
        cls,
        circuit_breaker: CircuitBreaker[_N]
    ) -> None: ...

    @classmethod
    def all_closed(cls) -> bool: ...

    @classmethod
    def get_circuits(cls) -> Iterable[CircuitBreaker]: ...

    @classmethod
    def get[_N: (str, bytes)](cls, name: _N) -> CircuitBreaker[_N]: ...

    @classmethod
    def get_open(cls) -> Generator[CircuitBreaker]: ...

    @classmethod
    def get_closed(cls) -> Generator[CircuitBreaker]: ...

@typing.overload
def circuit[_N: (str, bytes)](
    failure_threshold: int | None = None,
    recovery_timeout: float | None = None,
    expected_exception: _ExpectedException | None = None,
    name: _N | None = None,
    fallback_function: _FallbackFn | None = None,
    cls: type[CircuitBreaker[_N]] = CircuitBreaker,
) -> CircuitBreaker[_N]: ...

@typing.overload
def circuit[**P, T](
    failure_threshold: Callable[P, T],
) -> Callable[P, T]: ...

@typing.overload
def circuit[**P, T](
    failure_threshold: Callable[P, Generator[T]],
) -> Callable[P, Generator[T]]: ...

@typing.overload
def circuit[**P, T](
    failure_threshold: Callable[P, Awaitable[T]],
) -> Callable[P, Awaitable[T]]: ...

@typing.overload
def circuit[**P, T](
    failure_threshold: Callable[P, AsyncGenerator[T]],
) -> Callable[P, AsyncGenerator[T]]: ...