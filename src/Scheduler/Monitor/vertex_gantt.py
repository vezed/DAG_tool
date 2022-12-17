from copy import deepcopy
from typing import Dict, Any, List, NamedTuple
from collections import namedtuple
import matplotlib.pyplot as plt
from numpy import arange
from src.Scheduler.vertexstatus import VertexStatus
from src.Generator.dag import DAG


RdYlGr = ['#d73027', '#f46d43', '#fdae61', '#fee08b', '#ffffbf', '#d9ef8b', '#a6d96a', '#66bd63', '#1a9850', '#90EE90',
          '#FFFFE0', '#48D1CC', '#DA70D6']
POS_STEP = 0.5
POS_START = 1.0


def draw(runtime_info_dict: Dict[Any, List],
         dag: DAG,
         make_span: int
         ) -> None:
    fig, ax = plt.subplots()

    count = len(dag)
    end = count * POS_STEP + POS_START
    pos_x = arange(0, make_span + 1, 1)
    pos_y = arange(POS_START, end, POS_STEP)

    for cnt, vertex in enumerate(dag.nodes):
        running_status = get_vertex_running_status(runtime_info_dict, vertex)
        print(vertex, running_status)
        for start, end, on in running_status:
            bottom = cnt * POS_STEP + POS_START
            plt.text((start + end) / 2, bottom - POS_STEP / 6, f'P{on}', ha='center', fontsize=12)
            index = list(dag.nodes).index(str(vertex))
            color = RdYlGr[index % len(RdYlGr)]
            ax.barh(bottom, end - start, left=start, height=0.3, align='center', color=color)

    # Set processor_labels(y_axis)
    vertex_labels = [f'{vertex}' for vertex in dag.nodes]
    ax.set_yticks(pos_y)
    y_labels = ax.set_yticklabels(vertex_labels)
    plt.setp(y_labels, size='medium')

    # Set vertex_labels(x_axis)
    time_labels = [t for t in range(0, make_span + 1)]
    ax.set_xticks(pos_x)
    x_labels = ax.set_xticklabels(time_labels)
    plt.setp(x_labels, size='medium')

    plt.savefig('Monitor/img/vertex/0.png')
    plt.show()


RunningTime = namedtuple('running_time', ['start', 'end', 'on'])


def get_vertex_gantt_info(runtime_info_dict: Dict[Any, List],
                          dag: DAG
                          ) -> Dict[Any, List[NamedTuple]]:
    vertex_gantt_info = {}
    for vertex in dag.nodes:
        gantt_info = get_vertex_running_status(runtime_info_dict, vertex)
        vertex_gantt_info.update({vertex: deepcopy(gantt_info)})
    return vertex_gantt_info


def get_vertex_running_status(runtime_info_dict: Dict[Any, List],
                              vertex: Any,
                              ) -> List[NamedTuple]:
    """ Get vertex running status.
    The tuples of the three ints represent start time, end time and processor running on.
    """
    print(vertex, runtime_info_dict.get(vertex))
    vertex_info_lst = runtime_info_dict[vertex]
    running_time = list()
    for i in range(len(vertex_info_lst) - 1):
        if vertex_info_lst[i].status.value == VertexStatus.Running.value:
            start = vertex_info_lst[i].t
            end = vertex_info_lst[i + 1].t
            on = vertex_info_lst[i].message['on']
            running_time.append(RunningTime(start=start,
                                            end=end,
                                            on=on
                                            ))
    return running_time
