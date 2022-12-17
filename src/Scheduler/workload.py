import simpy
from simpy.events import AllOf
from typing import Dict, List, Tuple, Any, Optional, Callable, Union, NamedTuple
from collections import namedtuple
from simpy.core import SimTime
from src.Scheduler.vertexstatus import VertexStatus
from src.Scheduler.processors import *
from src.Generator.dag import DAG
from src.Scheduler.priority_assignment import assignment_type


Log = namedtuple('log', ['t', 'status', 'message'])


def vertex(vertex: Dict[str, int],
           vertex_name: Any,
           pred_events: List[simpy.Event],
           env: simpy.Environment,
           processors: Processor,
           runtime_info: List[NamedTuple],
           ) -> None:
    """ Representing a vertex in DAG.
        Use env.process(vertex(env, processors, execution_time)) to call.
        :parameter
        ----------
        vertex_name:
            Name of this vertex.
        env:
            Environment of vertex.
        processors:
            A node can be executed only after applied to a processor.
        execution_time:
            The execution time of this vertex.
        runtime_info:
            Representing all the status change.
            Example:
                [(0, VertexStatus.Initialized),
                 (1, VertexStatus.Eligible),
                 (1, VertexStatus.Running),
                 (2, VertexStatus.Success),
                ]
        pred_events:
            Predecessors that have to wait.
        prior:
            Priority of processor scheduling
        ----------
    """
    def log(t: int, status: VertexStatus, message: Optional[Dict] = None):
        runtime_info.append(Log(t, status, message))

    execution_time = vertex['execution_time']
    start_time = vertex['start_time']
    deadline = vertex['deadline']
    prior = vertex['priority']
    ab_ddl = start_time + deadline

    if vertex_name == 'S' or vertex_name == 'E':
        yield AllOf(env, pred_events)
        log(env.now, VertexStatus.Success)
        return

    # Record the total running time of Vertex.
    vertex.update({'usage': 0})

    log(env.now, VertexStatus.Initialized)
    if start_time != 0:
        yield env.timeout(start_time)

    if pred_events:
        yield AllOf(env, pred_events)
    log(env.now, VertexStatus.Eligible)
    if env.now >= ab_ddl and execution_time - vertex.get('usage') != 0:
        log(env.now, VertexStatus.Fail)
        raise RuntimeError([vertex_name, ab_ddl])

    # Try to request for processor until Success or Fail.
    while True:
        # Request for processor
        with processors.request(priority=prior, vertex_name=vertex_name) as req:
            yield req
            if env.now >= ab_ddl and execution_time - vertex.get('usage') != 0:
                log(env.now, VertexStatus.Fail)
                raise RuntimeError([vertex_name, ab_ddl])
            log(env.now, VertexStatus.Running, {'on': req.process_on})
            try:
                # Running vertex on processor...
                req_time = execution_time - vertex.get('usage')
                yield env.timeout(req_time)

                if env.now > ab_ddl:
                    vertex.update({'usage': vertex.get('usage') + req_time - env.now + ab_ddl})
                    log(env.now, VertexStatus.Fail)
                    raise RuntimeError([vertex_name, ab_ddl])
                else:
                    vertex.update({'usage': execution_time})
                    log(env.now, VertexStatus.Success)
            # Interrupted
            except simpy.Interrupt as interrupt:
                by = interrupt.cause.by
                usage = env.now - interrupt.cause.usage_since

                if env.now >= ab_ddl:
                    vertex.update({'usage': vertex.get('usage') + usage - env.now + ab_ddl})
                    log(env.now, VertexStatus.Fail)
                    raise RuntimeError([vertex_name, ab_ddl])
                else:
                    vertex.update({'usage': vertex.get('usage') + usage})
                    log(env.now, VertexStatus.Interrupted, {'by': by, 'usage': usage})
        # Note: Do not use while total_usage == execution_time:
        # to ensure vertex with execution time == 0 can be triggered.
        if vertex.get('usage') == execution_time:
            break


def dag2task(dag: DAG,
             env: simpy.Environment,
             processors: Union[Processor, PriorityProcessor, PreemptiveProcessor],
             priority_assignment: Optional[Callable] = None,
             ) -> Tuple[Dict[Any, simpy.Process], Dict[Any, List[NamedTuple]]]:
    """ Generate tasks based on dependencies.
        Create process for each vertex in dag.
        ----------
        :parameter
        dag:
            DAG needed to be transformed.
        env:
            Environment of vertex.
        processors:
            A node can be executed only after applied to a processor.
        priority_assignment:
            priority assignment function, See priority_assignment.py
            Default: None, set all the prior of vertex to 0.
        ----------
        :return
        process_dict:
            key - vertex,
            value - event corresponding to it.
        runtime_info_dict:
            key - vertex,
            value - runtime_info. (See function vertex)
        ----------
    """
    """ Priority Assignment """
    # if not priority assignment strategy, set all priority to 0.
    # if priority assignment strategy is dynamic, set all priority to 0.
    # if priority assignment strategy is static, get prior_dict.
    if priority_assignment is None:
        prior_dict = dict()
        for node in dag.nodes:
            prior_dict.update({node: 0})
            dag.nodes[node].update({'priority': 0})
    elif priority_assignment in assignment_type['dynamic']:
        prior_dict = dict()
        for node in dag.nodes:
            prior_dict.update({node: 255})
            dag.nodes[node].update({'priority': 255})
    else:
        prior_dict = priority_assignment(dag)
        for node in dag.nodes:
            dag.nodes[node].update({'priority': prior_dict.get(node)})

    # ----test output----
    # print(f'priority dict:')
    # for key, value in prior_dict.items():
    #     print(f"{key}'s priority is {value}")
    # -------------------

    """ Process Initialization """
    process_dict = dict()  # Store all {vertex: event} corresponding to dag(DAG).
    runtime_info_dict = dict()  # Store all {vertex: {time, Status}} corresponding to dag(DAG).
    initialize_dict = {node: False for node in dag.nodes}  # False if node haven't initialized, True otherwise.
    # If there is node haven't been initialized, keep doing...
    while False in initialize_dict.values():
        # Walk through all the nodes haven't been initialized.
        for node in [node for node in initialize_dict.keys() if not initialize_dict[node]]:
            # If all the predecessors have been initialized.
            if False not in [initialize_dict.get(pred) for pred in dag.predecessors(node)]:
                # Get pred events of node.
                pred_events = [process_dict.get(pred_node) for pred_node in dag.predecessors(node)]
                # Init runtime_info of node and update into runtime_info_dict.
                runtime_info = list()
                runtime_info_dict.update({node: runtime_info})
                # process this node, bind pred_events and runtime_info to it.
                process_dict.update({node: env.process(vertex(vertex=dag.nodes[node],
                                                              vertex_name=node,
                                                              pred_events=pred_events,
                                                              env=env,
                                                              processors=processors,
                                                              runtime_info=runtime_info,
                                                              ))})
                # node is initialized successfully.
                initialize_dict.update({node: True})
    return process_dict, runtime_info_dict
