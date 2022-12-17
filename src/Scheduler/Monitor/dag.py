import shutil
import os.path
from typing import Dict, Any
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import networkx as nx
from graphviz import Digraph
from simpy.core import SimTime
from typing import Optional
from functools import partial

from src.Scheduler.vertexstatus import VertexStatus
from src.Generator.dag import DAG


__all__ = [
    "draw",
]


# Draw different VertexStatus as different color.
color_dict = {
    "Initialized": 'black',
    "Eligible": 'blue',
    "Running": 'orange',
    "Interrupted": 'blue',
    "Success": 'green',
    "Fail": 'red',
}


def get_vertex_status(runtime_info_dict: Dict[Any, list],
                      vertex: Any,
                      t: SimTime
                      ) -> VertexStatus:
    """ Get vertex status at time t """
    if t < 0:
        raise ValueError('SimTime should not be less than 0. ')
    vertex_info_lst = runtime_info_dict[vertex]
    if not vertex_info_lst or vertex_info_lst[0].t > t:
        return VertexStatus.Initialized
    for i in range(len(vertex_info_lst) - 1):
        if vertex_info_lst[i].t <= t < vertex_info_lst[i + 1].t:
            return vertex_info_lst[i].status
    return vertex_info_lst[-1].status


def get_status(runtime_info_dict: Dict[Any, list],
               dag: DAG,
               t: SimTime,
               ) -> Dict[Any, VertexStatus]:
    """ Get all vertex status at time t as a dictionary """
    info_dict = dict()
    for vertex in dag.nodes:
        info_dict.update({vertex: get_vertex_status(runtime_info_dict, vertex, t)})
    return info_dict


def draw(dag: DAG,
         t: Optional[SimTime] = 0,
         info_dict: Optional[Dict[Any, VertexStatus]] = None,
         dir_path: Optional[str] = 'Monitor/img/dag/',
         init: Optional[bool] = False,
         fail: Optional[bool] = False
         ) -> None:
    # Init graphviz graph.
    g_graph = Digraph()

    # Add vertex
    for vertex in dag.nodes:
        if init:
            g_graph.node(name=str(vertex))
        else:
            status = info_dict[vertex]
            if fail:
                if status.name == "Success":
                    color = color_dict["Success"]
                else:
                    color = color_dict["Fail"]
            else:
                color = color_dict[status.name]
            g_graph.node(name=str(vertex), color=color)

    # Add edge
    for (start, end), _ in dag.edges.items():
        g_graph.edge(str(start), str(end))

    g_graph.render(dir_path + str(t), view=False, format='png')


def trigger_draw(runtime_info_dict: Dict[Any, list],
                 dag: DAG,
                 until: SimTime,
                 dir_path: Optional[str] = 'Monitor/img/dag/',
                 init: Optional[bool] = False,
                 is_fail: bool = False,
                 fail_time: int = None
                 ) -> None:
    if init:
        if os.path.exists(dir_path):
            shutil.rmtree(dir_path)
        draw(dag, t=0, init=True)

    for t in range(1, until + 1):
        if is_fail:
            print(f'fail at {fail_time}, until {until}')
            if t == fail_time + 1:
                fail = True
            else:
                fail = False
        else:
            fail = False
        info_dict = get_status(runtime_info_dict=runtime_info_dict, dag=dag, t=t - 1)
        draw(dag, t, info_dict, dir_path, fail=fail)


def data_gen(n):
    for cnt in range(n + 1):
        yield cnt


def init():
    plt.axis('off')
    plt.cla()


def run(cnt):
    img = plt.imread(f'Monitor/img/dag/{cnt}.png')
    ax.imshow(img)


fig, ax = plt.subplots()


def animate(until: SimTime):
    print('Generating animation...')
    ani = animation.FuncAnimation(fig=fig,
                                  func=run,
                                  frames=partial(data_gen, n=until + 1),
                                  interval=1000,
                                  init_func=init)
    ani.save('Monitor/img/dag/runtime.gif')
    print('Generate successfully!')
