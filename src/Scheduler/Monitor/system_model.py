from collections import namedtuple
from typing import List, OrderedDict, Dict, NamedTuple
from simpy.core import SimTime


system_status = namedtuple('SystemState', ['put_queue', 'users'])


def get_system_status(put_queue_dict: OrderedDict[SimTime, List],
                      users_dict: OrderedDict[SimTime, Dict],
                      t: SimTime
                      ) -> system_status:
    """ return the status of system at time t. """
    if t < 0:
        raise ValueError('SimTime should not be less than 0. ')
    while True:
        user_status = users_dict.get(t)
        put_queue_status = put_queue_dict.get(t)
        if user_status is not None or put_queue_status is not None:
            return system_status(put_queue_status, user_status)
        t -= 1


def get_system_status_iter(put_queue_dict: OrderedDict[SimTime, List],
                           users_dict: OrderedDict[SimTime, Dict],
                           end_time: SimTime
                           ) -> Dict[SimTime, NamedTuple]:
    status_lst = {}
    for t in range(end_time):
        status = get_system_status(put_queue_dict, users_dict, t)
        status_lst.update({t: status})
    return status_lst
