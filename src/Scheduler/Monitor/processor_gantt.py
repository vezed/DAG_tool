from typing import Dict, Any, List, OrderedDict
from simpy.core import SimTime
from collections import OrderedDict
import matplotlib.pyplot as plt
from numpy import arange

from src.Generator.dag import DAG

RdYlGr = ['#d73027', '#f46d43', '#fdae61', '#fee08b', '#ffffbf', '#d9ef8b', '#a6d96a', '#66bd63', '#1a9850', '#90EE90',
          '#FFFFE0', '#48D1CC', '#DA70D6']
POS_STEP = 0.5
POS_START = 1.0


def draw(dag: DAG,
         processors_dict: OrderedDict,
         make_span: int,
         capacity: int
         ) -> None:
    fig, ax = plt.subplots()
    processor_gantt_info = get_processor_gantt_info(processors_dict, capacity, make_span)

    count = len(processor_gantt_info)
    end = count * POS_STEP + POS_START
    pos_x = arange(0, make_span + 1, 1)
    pos_y = arange(POS_START, end, POS_STEP)

    for processor, info in processor_gantt_info.items():
        for (start, end, vertex) in info:
            bottom = processor * POS_STEP + POS_START
            if vertex is None:
                color = '#ffffff'
            else:
                index = list(dag.nodes).index(str(vertex))
                color = RdYlGr[index % len(RdYlGr)]
                plt.text((start + end) / 2, bottom - POS_STEP / 8, vertex, ha='center', fontsize=12)
            ax.barh(bottom, end - start, left=start, height=0.3, align='center', color=color)

    # Set processor_labels(y_axis)
    processor_labels = [f'P{processor}' for processor in processor_gantt_info.keys()]
    ax.set_yticks(pos_y)
    y_labels = ax.set_yticklabels(processor_labels)
    plt.setp(y_labels, size='medium')

    # Set vertex_labels(x_axis)
    time_labels = [t for t in range(0, make_span + 1)]
    ax.set_xticks(pos_x)
    x_labels = ax.set_xticklabels(time_labels)
    plt.setp(x_labels, size='medium')

    plt.savefig('Monitor/img/processor/0.png')
    plt.show()


def get_processors_status(processor_dict: OrderedDict,
                          t: SimTime
                          ) -> Dict[int, Any]:
    """ return the status of processor at time t. """
    if t < 0:
        raise ValueError('SimTime should not be less than 0. ')
    while True:
        status = processor_dict.get(t)
        if status is not None:
            return status
        t -= 1


def get_processor_gantt_info(processor_dict: OrderedDict,
                             capacity: int,
                             end_time: SimTime
                             ) -> Dict[int, List[List]]:
    """ Get Processor's info for drawing gantt graph. """
    processor_gantt_info = {processor: [] for processor in range(capacity)}
    for t in range(end_time):
        processors_status = get_processors_status(processor_dict, t)
        for processor in range(capacity):
            process_on = processors_status.get(processor)
            if not processor_gantt_info[processor] or processor_gantt_info[processor][-1][-1] != process_on:
                processor_gantt_info[processor].append([t, t + 1, process_on])
            else:
                processor_gantt_info[processor][-1][1] = t + 1
    return processor_gantt_info
