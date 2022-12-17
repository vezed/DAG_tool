"""
    Represents the operating state of Vertex
"""
from enum import Enum


class VertexStatus(Enum):
    """
        Initialized:
            Vertex is created, but in one of following cases:
                1. the processors do not success yet.
                2. does not meet the start time.
        Eligible:
            Vertex's processors success and meet the start time,
            but haven't been scheduled.
        Running:
            Vertex running on processor.
        Interrupted:
            Vertex are interrupted due to:
                1. blocked by critical resource.
                2. interrupted by vertex having higher priority.
        Success:
            Vertex finished executing before deadline.
        Fail:
            Vertex can not finish at deadline.
    """
    Initialized = 0
    Eligible = 1
    Running = 2
    Interrupted = 3
    Success = 4
    Fail = 5
