from collections import OrderedDict
from simpy.core import SimTime
from typing import Dict
from src.Scheduler.Monitor.processor_gantt import get_processor_gantt_info


def processor_utilization(processor_dict: OrderedDict,
                          capacity: int,
                          end_time: SimTime
                          ) -> Dict[int, float]:
    info_dict = get_processor_gantt_info(processor_dict, capacity, end_time)
    utilization_dict = {}
    for processor, info in info_dict.items():
        idle = 0
        for start, end, run_on in info:
            if start >= end_time:
                break
            if end > end_time:
                end = end_time
            if run_on is None:
                idle += end - start
        utilization_dict.update({processor: round((1 - idle / end_time) * 100, 2)})
    return utilization_dict
