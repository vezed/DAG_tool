# multi-rate task set -> single DAGs
from copy import deepcopy
from src.Generator.multitask.dag import DAG
from src.Generator.multitask.model import *
from src.Generator.multitask.utils import *


class Generator:
    def __init__(self, tasks):
        """ 构造函数、得到一个HP内的节点和矩阵 """
        self.matrix = None
        self.matrixSet = []
        self.instances = None
        self.taskSet = tasks
        self.DAGs = []
        self.task_nodes_num = None
        self.synchro_nodes_num = None
        self.nodes_num = None
        # self.generate()

    """ Generate """
    def generate(self):
        """ 生成对应的多个DAG """
        self._replication()  # Replication
        self._synchronization()  # Synchronization
        # Permutation and reduction
        for matrix in self._permutation():
            yield DAG(self.taskSet,
                      self.instances,
                      matrix,
                      self.task_nodes_num,
                      self.synchro_nodes_num,
                      self.nodes_num)
        # self.DAGs = [DAG(self.taskSet,
        #                  self.instances,
        #                  matrix,
        #                  self.task_nodes_num,
        #                  self.synchro_nodes_num,
        #                  self.nodes_num)
        #              for matrix in self.matrixSet]  # matrix -> DAG

    """ Replication """
    def _replication(self):
        # Start node
        self.instances = [Instance(Task('S', 0, 0, self.taskSet.hp, self.taskSet.hp, Type.task), 0)]

        # Task nodes
        for task in self.taskSet:
            num = int(self.taskSet.hp / task.t)  # 需要生成Instance的数量
            task.num = num  # 将Instance的数量存入task中
            instances = [Instance(task, count) for count in range(num)]

            task.begin = len(self.instances)
            t_begin = len(self.instances)
            self.instances.extend(instances)
            t_end = len(self.instances)
            task.end = len(self.instances) - 1
            # task nodes of task range from t_begin to t_end
            task.task_range = range(t_begin, t_end)

        # End node
        self.instances.append(Instance(Task('E', 0, 0, self.taskSet.hp, self.taskSet.hp, Type.task), 0))

        # Number of task nodes
        self.task_nodes_num = len(self.instances)

    """ Synchronization """
    def _synchronization(self):
        """ Synchronization """
        # Generate Synchronization nodes
        for task in self.taskSet:
            # Generate synchronization node for task which exists more than one instance in a Hyper Period
            if task.num > 1:
                ''' generate synchro nodes '''
                # WC = BC = deadline = 0, period = hyper-period for synchro nodes
                s_task = Task('s-' + task.name, 0, 0, self.taskSet.hp, 0, Type.synchro)
                # add synchronization instance
                s_begin = len(self.instances)
                instance = [Instance(s_task, s_count) for s_count in range(task.num - 1)]
                self.instances.extend(instance)
                s_end = len(self.instances)
                # s nodes of task range from s_begin to s_end
                task.synchro_range = range(s_begin, s_end)

                ''' generate dummy nodes '''
                # WC = BC = t - t', period = hyper-period for dummy nodes
                d_task = Task('d-' + task.name, task.t, task.t,
                              self.taskSet.hp, task.t, Type.dummy)
                # add dummy instances
                d_begin = len(self.instances)
                instance = [Instance(d_task, d_count) for d_count in range(task.num)]
                self.instances.extend(instance)
                d_end = len(self.instances)
                # d nodes of task range from d_begin to d_end
                task.dummy_range = range(d_begin, d_end)

        # Number of instances nodes
        self.nodes_num = len(self.instances)
        # Number of synchronization nodes
        self.synchro_nodes_num = self.nodes_num - self.task_nodes_num

        # Init matrix
        self.matrix = np.zeros([self.nodes_num] * 2)
        # Link task nodes, synchronization nodes and d nodes
        start = 0
        end = self.task_nodes_num - 1

        for task in self.taskSet:
            if task.num > 1:
                # link s nodes with t nodes and d nodes
                for count, s_p in enumerate(task.synchro_range):
                    # t -> d
                    self.matrix[task.task_range[count], s_p] = 1
                    # d -> t
                    self.matrix[s_p, task.task_range[count + 1]] = 1
                    # d -> s
                    self.matrix[task.dummy_range[count], s_p] = 1
                    # s -> d
                    self.matrix[s_p, task.dummy_range[count + 1]] = 1
                # S -> d
                self.matrix[start, task.dummy_range[0]] = 1
                # d -> E
                self.matrix[task.dummy_range[-1], end] = 1

    """ Permutation """
    def _permutation(self):
        """ Permutation """
        self._make_inner_matrix()
        for matrix in self._make_mutual_matrix():
            yield matrix

    def _make_inner_matrix(self):
        """ 处理同类task之间的联系 """
        start = 0
        end = self.task_nodes_num - 1
        for task in self.taskSet:
            # S -> 第一个任务
            self.matrix[start, task.begin] = 1
            # 同类任务的实例
            for count in range(task.begin, task.end):
                self.matrix[count, count + 1] = 1
            # 最后一个任务 -> S
            self.matrix[task.end, end] = 1

    def _make_mutual_matrix(self):
        """ 处理不同task之间的联系 """
        # 用字典存储每对(x,y)的可迭代对象
        self.iter_dict = dict()
        for key, x in enumerate(self.taskSet.taskList):
            for y in self.taskSet.taskList[key + 1:]:
                self.iter_dict.update({(x, y): Task.perm(x, y, self.taskSet.hp)})
        self.dict_keys = list(self.iter_dict.keys())

        # 遍历所有可能的矩阵
        for matrix in self._make_mutual_matrix_iter(len(self.iter_dict) - 1):
            yield matrix

    def _make_mutual_matrix_iter(self, n):
        key = self.dict_keys[n]
        x, y = key   # task x, task y
        iterator = self.iter_dict[key]

        # 遍历所有可能
        while True:
            try:  # 若还有组合，则遍历
                matrix_xy, matrix_yx = iterator.__next__()
                if x.t > y.t:
                    matrix_xy = matrix_xy.transpose()
                    matrix_yx = matrix_yx.transpose()
            except StopIteration:  # 若没有组合，则终止该迭代
                self.iter_dict[key] = Task.perm(x, y, self.taskSet.hp)
                break

            set_matrix(self.matrix, self.matrix, x.begin, x.end, y.begin, y.end, matrix_xy, matrix_yx)

            if n == 0:  # 如果已经在最里面一层
                if self._is_perm_available():  # 如果该排列可用
                    dag_reduced = deepcopy(self._DAG_aspect_reduce())
                    if not is_duplicated(dag_reduced, self.matrixSet):  # 如果结果不重复
                        self.matrixSet.append(dag_reduced)  # 则将matrix加入matrixSet
                        yield dag_reduced
            else:  # 进入下一层迭代
                for matrix in self._make_mutual_matrix_iter(n - 1):
                    yield matrix

            reset_matrix(self.matrix, self.matrix, x.begin, x.end, y.begin, y.end)  # 迭代结束后，重置该层

    """ Reduction """
    def _is_perm_available(self):
        """ 判断当前的排列在perm aspect上是否可用
            true if matrix is available, otherwise false
        """
        if self._is_cyclic() or self._is_exceeded():
            return False
        return True

    def _is_cyclic(self):
        """ 判断matrix是否成环
            true if matrix is acyclic, otherwise false
        """
        t = self.matrix
        n = len(self.instances)
        tn = matrixPow(t, n)
        x0 = np.ones([n, 1])
        return np.matmul(tn, x0).sum()

    def _is_exceeded(self):
        """ 判断matrix是否超过最长执行时间
            true if matrix is exceeded, otherwise false
        """
        wc = get_wc(self.instances)
        execution_time = max(maxProductPow(self.matrix, wc, len(self.instances)))
        return execution_time > self.taskSet.hp

    def _DAG_aspect_reduce(self):
        """ 对matrix进行化简 """
        return self._transitive_reduction()

    def _transitive_reduction(self):
        """ Transitive Reduction """
        t = self.matrix
        e = np.eye(self.matrix.shape[0], self.matrix.shape[1])
        tvi = un_boolean(matrixPow(t + e, len(self.taskSet)))
        d = un_boolean(tvi - e)
        td = un_boolean(np.matmul(t, d))
        tr = un_boolean((t - td) > 0)
        return tr

    # """ Draw """
    # def draw(self):
    #     for key, dag in enumerate(self.DAGs):
    #         dag.draw_with_synchro(str(key))
    #         dag.draw_without_synchro(str(key))


if __name__ == "__main__":
    """ Test Example 1: HP == SP & Harmonic"""
    # ts = TaskSet([
    #     Task('t0', 7, 5, 10, 10),
    #     Task('t1', 13, 10, 30, 30),
    #     Task('t2', 10, 8, 30, 30),
    # ])

    """ Test Example 2: HP != SP & Harmonic """
    # ts = TaskSet([
    #     Task('t0', 1, 1, 3, 1),
    #     Task('t1', 1, 1, 6, 1),
    #     Task('t2', 1, 1, 12, 1),
    # ])

    """ Test Example 3: HP == SP & Non-harmonic """
    # ts = TaskSet([
    #     Task('t0', 1, 1, 3, 1),
    #     Task('t1', 1, 1, 5, 1),
    # ])

    """ Test Example 4: HP != SP & Non-harmonic """
    # ts = TaskSet([
    #     Task('t0', 1, 1, 2, 1),
    #     Task('t1', 1, 1, 5, 1),
    #     Task('t2', 1, 1, 10, 1),
    # ])

    ts = TaskSet([
        Task('t3', 1, 1, 10, 10),
        Task('t1', 1, 1, 2, 10),
        Task('t2', 1, 1, 5, 10),
    ])

    g = Generator(ts)
    for key, dag in enumerate(g.generate()):
        dag.draw_with_synchro(str(key))
        dag.draw_without_synchro(str(key))
        print(key, dag.formal_dag.nodes, dag.formal_dag.edges)

    """ test drawer """

    # t = np.array(
    # [0, 1, 0, 0, 1, 1, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1, 0, 1, 1, 0, 0,
    #      0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0]).reshape([7, 7])
    # e = np.eye(7, 7)
    # tvi = boolean(matrixPow(t + e, 7))
    # d = boolean(tvi - e)
    # td = boolean(np.matmul(t, d))
    # tr = boolean((t - td) > 0)
