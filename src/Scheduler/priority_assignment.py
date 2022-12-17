"""
    There are two kinds of priority assignment provided:
        1. static assignment
            Priorities can be determined before execution, and can not be changed when executing.
        2. dynamic assignment
            Priorities are changing during execution.
    Note: The higher the priority, the smaller the value prior.
"""
import networkx as nx
from simpy.core import SimTime
from src.Generator.dag import DAG
from typing import Callable, Dict, Any, List, NamedTuple
from collections import OrderedDict


# ----------------------------------- Static -----------------------------------
def RMS(dag: DAG) -> Dict[Any, int]:
    pass


def DMS(dag: DAG) -> Dict[Any, int]:
    pass


def FPS(dag: DAG) -> Dict[Any, int]:
    prior_dict = {}
    for vertex in dag:
        prior_dict.update({vertex: dag.nodes[vertex]['priority']})
    return prior_dict


def SJF(dag: DAG) -> Dict[Any, int]:
    prior_dict = {}
    for vertex in dag:
        prior_dict.update({vertex: dag.nodes[vertex]['execution_time']})
    return prior_dict


def CPFE(dag: DAG) -> Dict[Any, int]:
    def CPC(dag: DAG) -> List[List]:
        cri_path = dag.longest_paths[0]
        providers = [[cri_path[0]]]
        for cri_node in cri_path[1:]:
            preds = list(dag.predecessors(cri_node))
            if len(preds) == 1 and providers[-1][-1] in preds:
                providers[-1].append(cri_node)
            else:
                providers.append([cri_node])
        return providers

    # priority assignment



def EDF(dag: DAG) -> Dict[Any, int]:
    prior_dict = {}
    ddl_dict = OrderedDict()
    # compute ddl
    for vertex in dag.nodes:
        ddl_dict.update({vertex: dag.nodes[vertex]['start_time'] + dag.nodes[vertex]['deadline']})
    # Sort
    ddl_dict = OrderedDict(sorted(ddl_dict.items(), key=lambda item: item[1]))
    # Set priority_dict
    prior = 0
    for vertex, value in ddl_dict.items():
        prior_dict.update({vertex: prior})
        prior += 1
    return prior_dict


# ----------------------------------- Dynamic -----------------------------------
def LLF(dag: DAG,
        request_info_dict,
        t: SimTime
        ) -> None:
    laxity_dict = OrderedDict()
    # Compute Laxity
    for event, info in request_info_dict.items():
        execution_time = info['execution_time']
        deadline = info['deadline']
        start_time = info['start_time']
        usage = info['usage']
        laxity = (start_time + deadline) - (execution_time - usage) - t
        laxity_dict.update({event: laxity})
    # Sort
    laxity_dict = OrderedDict(sorted(laxity_dict.items(), key=lambda item: item[1]))
    # Update Priority
    prior = 0
    for event, laxity in laxity_dict.items():
        event.priority = prior
        event.key = (event.priority, event.time, not event.preempt)
        vertex_name = event.vertex_name
        vertex = dag.nodes[vertex_name]
        vertex.update({'priority': prior})
        prior += 1

    # print(t)
    # for request, info in request_info_dict.items():
    #     print(f"\t{request}  ---  优先级:{info['priority']},松弛度:{laxity_dict[request]}")


assignment_type = {
    'static': [RMS, DMS, FPS, SJF, CPFE, EDF],
    'dynamic': [LLF]
}


if __name__ == "__main__":
    d = DAG(periodic=False)
    d.add_node('t1', execution_time=1, start_time=0, deadline=180)
    d.add_node('t2', execution_time=7, start_time=0, deadline=180)
    d.add_node('t3', execution_time=3, start_time=0, deadline=180)
    d.add_node('t4', execution_time=3, start_time=0, deadline=180)
    d.add_node('t5', execution_time=6, start_time=0, deadline=180)
    d.add_node('t6', execution_time=1, start_time=0, deadline=180)
    d.add_node('t7', execution_time=2, start_time=0, deadline=180)
    d.add_node('t8', execution_time=1, start_time=0, deadline=180)
    d.add_edges_from([('t1', 't2'), ('t1', 't3'), ('t1', 't4'), ('t1', 't5'), ('t1', 't6'),
                      ('t5', 't7'), ('t6', 't7'), ('t2', 't8'), ('t3', 't8'), ('t4', 't8'),
                      ('t7', 't8')
                      ])
    print(CPFE(d))
