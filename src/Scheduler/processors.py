from types import TracebackType
from typing import (
    TYPE_CHECKING,
    Any,
    Optional,
    Type,
    ContextManager,
    Generic,
    TypeVar,
    List,
    Dict
)

from simpy.core import BoundClass, Environment, SimTime
from simpy.events import Process, Event
from simpy.resources import base
from src.Generator.dag import DAG
from src.Scheduler.priority_assignment import assignment_type


class Preempted:
    """Cause of an preemption :class:`~simpy.exceptions.Interrupt` containing
    information about the preemption.

    """

    def __init__(
        self,
        by: Optional[Process],
        usage_since: Optional[SimTime],
        resource: 'Processor',
    ):
        self.by = by
        """The preempting :class:`simpy.events.Process`."""
        self.usage_since = usage_since
        """The simulation time at which the preempted process started to use
        the resource."""
        self.resource = resource
        """The resource which was lost, i.e., caused the preemption."""


ResourceType = TypeVar('ResourceType', bound='BaseResource')


class Request(Event, ContextManager['Put'], Generic[ResourceType]):
    """Request usage of the *resource*. The event is triggered once access is
    granted. Subclass of :class:`simpy.resources.base.Put`.

    If the maximum capacity of users has not yet been reached, the request is
    triggered immediately. If the maximum capacity has been
    reached, the request is triggered once an earlier usage request on the
    resource is released.

    The request is automatically released when the request was created within
    a :keyword:`with` statement.

    """

    resource: 'Processor'

    process_on: Optional[int] = None

    #: The time at which the request succeeded.
    usage_since: Optional[SimTime] = None

    def __init__(self,
                 resource: ResourceType,
                 vertex_name: Any):
        super().__init__(resource._env)
        self.resource = resource
        self.vertex_name = vertex_name
        self.proc: Optional[Process] = self.env.active_process

        resource.put_queue.append(self)
        self.callbacks.append(resource._trigger_get)

    def __enter__(self) -> 'Request':
        return self

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_value: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> Optional[bool]:
        super().__exit__(exc_type, exc_value, traceback)
        # Don't release the resource on generator cleanups. This seems to
        # create unclaimable circular references otherwise.
        if exc_type is not GeneratorExit:
            self.resource.release(self)
        return None

    def cancel(self) -> None:
        """Cancel this get request.

        This method has to be called if the put request must be aborted, for
        example if a process needs to handle an exception like an
        :class:`~simpy.exceptions.Interrupt`.

        If the put request was created in a :keyword:`with` statement, this
        method is called automatically.

        """
        if not self.triggered:
            self.resource.put_queue.remove(self)

    def __str__(self):
        return str(self.vertex_name)

    def __repr__(self):
        return str(self.vertex_name)


class Release(Event, ContextManager['Get'], Generic[ResourceType]):
    """Releases the usage of *resource* granted by *request*. This event is
    triggered immediately. Subclass of :class:`simpy.resources.base.Get`.

    """

    def __init__(self, resource: ResourceType, request: Request):
        super().__init__(resource._env)
        self.resource = resource
        self.request = request
        self.proc = self.env.active_process

        resource.get_queue.append(self)
        resource._trigger_get(None)

    def __enter__(self) -> 'Release':
        return self

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_value: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> Optional[bool]:
        self.cancel()
        return None

    def cancel(self) -> None:
        """Cancel this get request.

        This method has to be called if the get request must be aborted, for
        example if a process needs to handle an exception like an
        :class:`~simpy.exceptions.Interrupt`.

        If the get request was created in a :keyword:`with` statement, this
        method is called automatically.

        """
        if not self.triggered:
            self.resource.get_queue.remove(self)


class PriorityRequest(Request):
    """Request the usage of *resource* with a given *priority*. If the
    *resource* supports preemption and *preempt* is ``True`` other usage
    requests of the *resource* may be preempted (see
    :class:`PreemptiveResource` for details).

    This event type inherits :class:`Request` and adds some additional
    attributes needed by :class:`PriorityResource` and
    :class:`PreemptiveResource`

    """

    def __init__(self,
                 resource: 'Processor',
                 vertex_name: Any,
                 priority: int = 0,
                 preempt: bool = True
    ):
        self.priority = priority
        """The priority of this request. A smaller number means higher
        priority."""

        self.preempt = preempt
        """Indicates whether the request should preempt a resource user or not
        (:class:`PriorityResource` ignores this flag)."""

        self.time = resource._env.now
        """The time at which the request was made."""

        self.key = (self.priority, self.time, not self.preempt)
        """Key for sorting events. Consists of the priority (lower value is
        more important), the time at which the request was made (earlier
        requests are more important) and finally the preemption flag (preempt
        requests are more important)."""

        super().__init__(resource, vertex_name)


class SortedQueue(list):
    """Queue for sorting events by their :attr:`~PriorityRequest.key`
    attribute.

    """

    def __init__(self, maxlen: Optional[int] = None):
        super().__init__()
        self.maxlen = maxlen
        """Maximum length of the queue."""

    def append(self, item: Any) -> None:
        """Sort *item* into the queue.

        Raise a :exc:`RuntimeError` if the queue is full.

        """
        if self.maxlen is not None and len(self) >= self.maxlen:
            raise RuntimeError('Cannot append event. Queue is full.')

        super().append(item)
        super().sort(key=lambda e: e.key)

    def sort_queue(self):
        super().sort(key=lambda e: e.key)


class Users(dict):
    """ Dict for monitoring every processor and its user.

    """
    def __init__(self, capacity):
        super().__init__()
        self.capacity = capacity
        """ capacity of processors """

    def count(self):
        return len(self)

    def get_idle(self):
        lst = [processor for processor in range(self.capacity) if self.get(processor) is None]
        if not lst:
            return None
        return lst

    def append(self, req: Request):
        idle_processor = self.get_idle()[0]
        self.update({idle_processor: req})
        req.process_on = idle_processor

    def find(self, item: Any):
        for key, value in self.items():
            if value == item:
                return key
        return None

    def remove(self, req: Request):
        processor = self.find(req)
        if processor is None:
            raise ValueError()
        self.pop(processor)
        req.process_on = None


class Processor(base.BaseResource):
    """Resource with *capacity* of usage slots that can be requested by
    processes.

    If all slots are taken, requests are enqueued. Once a usage request is
    released, a pending request will be triggered.

    The *env* parameter is the :class:`~simpy.core.Environment` instance the
    resource is bound to.

    """

    def __init__(self, env: Environment, capacity: int = 1):
        if capacity <= 0:
            raise ValueError('"capacity" must be > 0.')

        super().__init__(env, capacity)

        self.users: Users = Users(capacity)
        """List of :class:`Request` events for the processes that are currently
        using the resource."""
        self.queue = self.put_queue
        """Queue of pending :class:`Request` events. Alias of
        :attr:`~simpy.resources.base.BaseResource.put_queue`.
        """

    @property
    def count(self) -> int:
        """Number of users currently using the resource."""
        return len(self.users)

    if TYPE_CHECKING:

        def request(self, vertex_name) -> Request:
            """Request a usage slot."""
            return Request(self, vertex_name)

        def release(self, request: Request) -> Release:
            """Release a usage slot."""
            return Release(self, request)

    else:
        request = BoundClass(Request)
        release = BoundClass(Release)

    def _do_put(self, event: Request) -> bool:
        if len(self.users) < self.capacity:
            self.users.append(event)
            event.usage_since = self._env.now
            event.succeed()

        if len(self.users) < self.capacity:
            return True
        return False

    def _do_get(self, event: Release) -> None:
        try:
            self.users.remove(event.request)  # type: ignore
        except ValueError:
            pass
        event.succeed()


class PriorityProcessor(Processor):
    """A :class:`~simpy.resources.resource.Resource` supporting prioritized
    requests.

    Pending requests in the :attr:`~Resource.queue` are sorted in ascending
    order by their *priority* (that means lower values are more important).

    """

    PutQueue = SortedQueue
    """Type of the put queue. See
    :attr:`~simpy.resources.base.BaseResource.put_queue` for details."""

    GetQueue = list
    """Type of the get queue. See
    :attr:`~simpy.resources.base.BaseResource.get_queue` for details."""

    def __init__(self, env: Environment, capacity: int = 1, priority_assignment=None, preempt_clock=None):
        super().__init__(env, capacity)
        self.priority_assignment = priority_assignment

    if TYPE_CHECKING:

        def request(
            self, vertex_name: Any, priority: int = 0, preempt: bool = True
        ) -> PriorityRequest:
            """Request a usage slot with the given *priority*."""
            return PriorityRequest(self,
                                   vertex_name=vertex_name,
                                   priority=priority,
                                   preempt=preempt)

        def release(  # type: ignore[override] # noqa: F821
            self, request: PriorityRequest
        ) -> Release:
            """Release a usage slot."""
            return Release(self, request)

    else:
        request = BoundClass(PriorityRequest)
        release = BoundClass(Release)

    def schedule(self, dag: DAG, t: SimTime, get_event=None) -> None:
        """ Response to request """
        # print(f'schedule @{self._env.now}')
        self.update_priority(dag, t)
        self._trigger_put(get_event=get_event)

    def update_priority(self, dag: DAG, t: SimTime):
        if self.priority_assignment is None or self.priority_assignment not in assignment_type['dynamic']:
            return
        requests: List[PriorityRequest] = list(self.users.values()) + self.put_queue

        request_info_dict: Dict[PriorityRequest, Dict] = {}
        # Temporary update usage
        for request in requests:
            vertex_name = request.vertex_name
            vertex: Dict[str, int] = dag.nodes[vertex_name]
            if request.usage_since is None:
                request_info_dict.update({request: vertex})
                continue
            usage = vertex.get('usage') + (t - request.usage_since)
            vertex.update({'usage': usage})
            request_info_dict.update({request: vertex})
        self.priority_assignment(dag, request_info_dict, t)
        # restore usage
        for request in requests:
            vertex_name = request.vertex_name
            vertex: Dict[str, int] = dag.nodes[vertex_name]
            if request.usage_since is None:
                continue
            usage = vertex.get('usage') - (t - request.usage_since)
            vertex.update({'usage': usage})
        self.put_queue.sort_queue()


class PreemptiveProcessor(PriorityProcessor):
    """A :class:`~simpy.resources.resource.PriorityResource` with preemption.

    If a request is preempted, the process of that request will receive an
    :class:`~simpy.exceptions.Interrupt` with a :class:`Preempted` instance as
    cause.

    """
    def __init__(self,
                 env: Environment,
                 capacity: int = 1,
                 priority_assignment=None,
                 preempt_clock: int = 2):
        super().__init__(env, capacity, priority_assignment)
        self.preempt_clock = int(preempt_clock)

    users: Users  # type: ignore

    def _do_put(  # type: ignore[override] # noqa: F821
        self, event: PriorityRequest
    ) -> bool:
        if self._env.now % self.preempt_clock == 0:
            # print(f'{self._env.now}: 抢占周期')
            if len(self.users) >= self.capacity and event.preempt:
                # Check if we can preempt another process
                preempt = sorted(self.users.values(), key=lambda e: e.key)[-1]
                # print(f'抢占比较\n\t{event}:{event.key} v.s {preempt}:{preempt.key} result:{preempt.key > event.key}')
                if preempt.key > event.key:
                    self.users.remove(preempt)
                    preempt.proc.interrupt(  # type: ignore
                        Preempted(
                            by=event.proc,
                            usage_since=preempt.usage_since,
                            resource=self,
                        )
                    )

            if len(self.users) < self.capacity:
                self.users.append(event)
                event.usage_since = self._env.now
                event.succeed()
            return True

        else:
            # print(f'{self._env.now}: 非抢占周期')
            super()._do_put(event)

