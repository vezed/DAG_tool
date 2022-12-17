from numpy import lcm
import numpy as np
from src.Generator.multitask.utils import *


def duplication(m_xy, m_yx, _n, x_num, y_num):
    """ Handle HP != SP situation """
    _xy = np.kron(np.eye(_n, _n), m_xy[1: x_num + 1, 0: y_num])
    _yx = np.kron(np.eye(_n, _n), m_yx[0: y_num, 1: x_num + 1])

    if _n != 1:
        if m_xy[0, 0]:
            for p in range(1, _n):
                _xy[p * int(x_num) - 1, p * int(y_num)] = 1

        if m_yx[-1, -1]:
            for p in range(1, _n):
                _yx[p * int(y_num) - 1, p * int(x_num)] = 1

    return [_xy, _yx]


def unit_perm(_q):
    """ Handle q: 1 situation """
    for para in range(_q + 1, 0, -1):
        # 对不同并行度进行枚举，生成表示x,y出入关系的可迭代对象
        pnt = 0
        while pnt + para < _q + 2:
            # init matrix x->y and y->x
            _xy = np.zeros([_q + 2, 1])
            _yx = np.zeros([1, _q + 2])
            _xy[pnt, 0] = 1
            _yx[0, pnt + para] = 1

            yield [_xy, _yx]

            pnt += 1


# non harmonic iterator
def non_har_iter(iter_dict, key, matrix_xy, matrix_yx):
    iterator, _q, (start, end) = iter_dict[key]
    # print('Processing ' + str(start) + "->" + str(end) + ", key = " + str(key))

    while True:
        try:
            _xy, _yx = iterator.__next__()
            # print(_xy, _yx)
        except StopIteration:
            iter_dict[key] = [unit_perm(_q), _q, (start, end)]
            break

        # TODO: 处理第一个
        set_matrix(matrix_xy, matrix_yx, start, end, key, key, _xy[1: -1, 0: 1], _yx[0: 1, 1: -1])

        if key == 0:  # 如果已经在最里面一层
            # TODO: 处理最后一个
            yield [matrix_xy, matrix_yx]
        else:  # 进入下一层迭代
            for [matrix_xy, matrix_yx] in non_har_iter(iter_dict, key - 1, matrix_xy, matrix_yx):
                yield [matrix_xy, matrix_yx]

        reset_matrix(matrix_xy, matrix_yx, start, end, key, key)


class Task:
    """ multi-rate task
        name(str) : 任务名称
        wc(int) : worst case execution time
        bc(int) : best case execution time
        t(int) : period
        deadline(int) : relative deadline
    """
    def __init__(self, name, wc, bc, t, deadline, t_type=Type.task):
        """ The constructor """
        self.name = name  # name of the task
        self.wc = wc  # worst-case execution time
        self.bc = bc  # best-case execution time
        self.t = t  # period time
        self.deadline = deadline  # relative deadline
        self.num = None  # Amount in one Hyper Period
        self.begin = None  # Start No. in Generator.instances
        self.end = None  # End No. in Generator.instances
        self.task_range = None  # range of task nodes
        self.synchro_range = None  # range of synchro nodes
        self.dummy_range = None  # range of dummy nodes
        self.type = t_type  # type of task

    @staticmethod
    def get_super_period(x, y):
        assert type(x) is Task and type(y) is Task, "Task Required"
        return lcm(x.t, y.t)

    @staticmethod
    def perm(x, y, hp):
        """ Return an iterable object including possible arrangement of x and y. """
        # Let period(y) > period(x)
        if x.t > y.t:
            x, y = y, x
        sp = Task.get_super_period(x, y)
        n = int(hp / sp)

        # harmonic
        if y.t % x.t == 0:
            q = int(sp / x.t)
            for xy, yx in unit_perm(q):
                yield duplication(xy, yx, n, int(sp / x.t), int(sp / y.t))

        # TODO: non-harmonic
        else:
            # Divide instances by interaction relationship
            # Example:
            #   period(x) = 3, period(y) = 5  ==> lst = [(1, 2), (2, 4), (4, 5)]
            lst = []
            x_temp = 1
            for x_no in range(1, int(sp / x.t) + 1):
                o_y = (len(lst) + 1) * y.t
                if (x_no - 1) * x.t < o_y <= x_no * x.t:
                    lst.append((x_temp, x_no))
                    x_temp = x_no

            # Make iter_dict
            iter_dict = dict()
            for key, (start, end) in enumerate(lst):
                q = end - start + 1
                iter_dict.update({key: [unit_perm(q), q, (start, end)]})

            # Init matrix
            matrix_xy = np.zeros([int(sp / x.t) + 2, int(sp / y.t)])
            matrix_yx = np.zeros([int(sp / y.t), int(sp / x.t) + 2])

            # Iteration
            for xy, yx in non_har_iter(iter_dict, len(lst) - 1, matrix_xy, matrix_yx):
                # print('Processing' + xy + yx)
                yield duplication(xy, yx, n, int(sp / x.t), int(sp / y.t))

    def __repr__(self):
        return "task: " + self.name + ", WCET: " + str(self.wc) + ", BCET: " + str(self.bc) \
               + ", period: " + str(self.t) + ", deadline: " + str(self.deadline)


class Instance:
    """ Instance of Task
        task(Task) : the instance of task
        no(int) : order of instance
    """
    def __init__(self, task, no):
        self.task = task
        self.no = no

    def __repr__(self):
        if self.task.name == 'S' or self.task.name == 'E':
            return self.task.name
        return self.task.name + "," + str(self.no)


class TaskSet:
    """ multi-rate task set
        taskList(list of Task)
        taskChains(list of chain)
    """
    def __init__(self, tasks, task_chains=None):
        self.taskList = tasks
        self.taskChains = task_chains
        self._get_hp()

    def _get_hp(self):
        self.hp = lcm.reduce([task.t for task in self.taskList])

    def __len__(self):
        return len(self.taskList)

    def __getitem__(self, item):
        return self.taskList[item]

    def __repr__(self):
        return "\n".join([str(task) for task in self.taskList])


if __name__ == '__main__':
    """ Test Example 1: HP == SP, from paper """
    # t1 = Task('t1', 7, 5, 10, 10)
    # t2 = Task('t2', 13, 10, 30, 30)
    # t3 = Task('t3', 10, 8, 30, 30)
    # ts = TaskSet([t1, t2, t3])
    # for i in Task.perm(t1, t3, 30):
    #     print(i)
    """ Test Example 2: HP != SP """
    t1 = Task('t1', 7, 5, 10, 10)
    t2 = Task('t2', 13, 10, 30, 30)
    ts = TaskSet([t1, t2])
    for i in Task.perm(t1, t2, 60):
        print(i)
