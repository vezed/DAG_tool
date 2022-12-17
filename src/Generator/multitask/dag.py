from graphviz import Digraph
from src.Generator.multitask.utils import *
import numpy as np
from copy import deepcopy
from src.Generator.multitask.model import *
import src.Generator.dag as formal


class DAG:
    def __init__(self, tasks, instances, matrix, task_nodes_num, synchro_nodes_num, nodes_num):
        self.taskSet: TaskSet = tasks
        self.instances = instances
        self.matrix = matrix
        self.task_nodes_num = task_nodes_num
        self.synchro_nodes_num = synchro_nodes_num
        self.nodes_num = nodes_num
        self.EST = np.zeros(self.task_nodes_num)  # All equal to zero
        self.LFT = np.ones(self.task_nodes_num) * self.taskSet.hp  # All equal to HP
        self.EFT = np.zeros(self.task_nodes_num)
        self.LST = np.zeros(self.task_nodes_num)
        self.bc = get_bc(self.instances)
        self.wc = get_wc(self.instances)
        self.get_timing_attributes()

    @property
    def formal_dag(self):
        formal_dag = formal.DAG(periodic=True)

        # node
        for instance in self.instances[:self.task_nodes_num]:
            formal_dag.add_node(str(instance),
                                execution_time=instance.task.wc,
                                start_time=instance.task.t * instance.no,
                                deadline=instance.task.deadline)

        # inner edge
        for task in self.taskSet:
            task_instances = [instance for instance in self.instances if instance.task == task]
            for item in range(len(task_instances) - 1):
                formal_dag.add_edge(str(task_instances[item]), str(task_instances[item + 1]))

        # mutual edge
        matrix = self.matrix[:self.task_nodes_num, :self.task_nodes_num]
        for row in range(self.task_nodes_num):
            for column in range(self.task_nodes_num):
                if matrix[row, column] == 1:
                    formal_dag.add_edge(str(self.instances[row]), str(self.instances[column]))

        formal_dag.task_set = self.taskSet
        formal_dag.instances = self.instances

        return formal_dag

    # Draw with synchro nodes
    def draw_with_synchro(self, filename):
        """ draw DAG into ../img/filename.png and ../img/filename.txt with synchro nodes"""
        # init Digraph
        g = Digraph('DAG')

        """ nodes """
        for instance in self.instances:
            if instance.task.name == 'S':
                g.node(name='S', color='green')
            elif instance.task.name == 'E':
                g.node(name='E', color='red')
            else:
                g.node(name=str(instance))

        """ edges """
        for x in range(self.nodes_num):
            for y in range(self.nodes_num):
                if self.matrix[x, y]:
                    g.edge(str(self.instances[x]), str(self.instances[y]))

        """ render """
        g.render('Graph/img_with_synchro/' + filename, view=False, format='png')

    # Draw without synchro nodes
    def draw_without_synchro(self, filename):
        """ draw DAG into ../img/filename.png and ../img/filename.txt without synchro nodes"""
        # init Digraph
        g = Digraph('DAG')

        """ nodes """
        for instance in self.instances:
            if instance.task.name == 'S':
                g.node(name='S', color='green')
            elif instance.task.name == 'E':
                g.node(name='E', color='red')
            elif instance.task.type == Type.task:
                g.node(name=str(instance))

        """ edges """
        task_matrix = deepcopy(self.matrix[0: self.task_nodes_num, 0: self.task_nodes_num])

        # # in-degree == 0
        # for count in range(1, self.task_nodes_num - 1):
        #     if sum(self.matrix[0: self.task_nodes_num, count]) == 0:
        #         # First instance of the task
        #         if self.instances[count - 1].task != self.instances[count].task:
        #             task_matrix[0, count] = 1
        #         # Another instance of the task
        #         else:
        #             task_matrix[count - 1, count] = 1
        #
        # # out-degree == 0
        # for count in range(1, self.task_nodes_num - 1):
        #     if sum(task_matrix[count, 0: self.task_nodes_num]) == 0:
        #         # Last instance of the task
        #         if self.instances[count].task != self.instances[count + 1].task:
        #             task_matrix[count, self.task_nodes_num] = 1
        #         # Another instance of the task
        #         else:
        #             task_matrix[count, count + 1] = 1

        # in-degree == 0
        for count in range(1, self.task_nodes_num - 1):

            # First instance of the task
            if self.instances[count - 1].task != self.instances[count].task:
                if sum(self.matrix[0: self.task_nodes_num, count]) == 0:
                    task_matrix[0, count] = 1
            # Another instance of the task
            else:
                task_matrix[count - 1, count] = 1

        # out-degree == 0
        for count in range(1, self.task_nodes_num - 1):

            # Last instance of the task
            if self.instances[count].task != self.instances[count + 1].task:
                if sum(task_matrix[count, 0: self.task_nodes_num]) == 0:
                    task_matrix[count, self.task_nodes_num] = 1
            # Another instance of the task
            else:
                task_matrix[count, count + 1] = 1

        # Add edge
        for x in range(self.task_nodes_num):
            for y in range(self.task_nodes_num):
                if task_matrix[x, y]:
                    g.edge(str(self.instances[x]), str(self.instances[y]))

        """ render """
        g.render('Graph/img_without_synchro/' + filename, view=False, format='png')

    def get_timing_attributes(self):
        """ Get EST, LFT, EFT, LST """

        # EFT(Earliest Finishing Time) and LFT (Latest Finishing Time)
        # 初始化，EST为period到来的时间，LFT为period结束的时间
        for i in range(self.task_nodes_num):
            self.EST[i] = self.instances[i].no * self.instances[i].task.t
            self.LFT[i] = (self.instances[i].no + 1) * self.instances[i].task.t
        # 迭代生成EFT和LFT
        for _ in range(self.task_nodes_num):
            for i in range(self.task_nodes_num):
                for j in range(self.task_nodes_num):
                    # EFT (Earliest Finishing Time)
                    self.EST[i] = max(self.EST[i], (self.EST[j] + self.bc[j]) * self.matrix[j, i])
                    # LFT (Latest Finishing Time)
                    if self.matrix[i, j]:
                        self.LFT[i] = min(self.LFT[i], (self.LFT[j] - self.wc[j]) * self.matrix[i, j])

        # EST(Earliest Starting Time)
        self.EFT = self.EST + self.bc[:self.task_nodes_num]

        # LST(Latest Starting Time)
        self.LST = self.LFT - self.wc[:self.task_nodes_num]

    def find_reactions(self):
        """ Get first reaction and last reaction """
        pass

    def get_data_age(self):
        """ Get data edge of this DAG """
        pass

    def get_reaction_time(self):
        """ Get Reaction time of this DAG """
        pass

    def schedule(self):
        """ Schedule by Heterogeneous Earliest Finishing Time (HEFT) algorithm """
        pass


if __name__ == "__main__":
    pass
