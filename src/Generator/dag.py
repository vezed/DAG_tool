import json
from copy import deepcopy

import networkx as nx
from typing import Optional
from graphviz import Digraph


class DAG(nx.DiGraph):
    def __init__(self, periodic: bool, incoming_graph_data=None, **attr):
        super().__init__(incoming_graph_data, **attr)
        self.periodic = periodic
        self.dag_name = None

    @property
    def tasks(self):
        if self.periodic:
            return self.task_set
        else:
            return None

    @property
    def paths(self, start='S'):
        self.transform_add_source()
        self.transform_add_sink()
        path = []
        return list(self.get_path_iter(start, path))

    def get_path_iter(self, vertex, path):
        path.append(vertex)
        if vertex == 'E':
            yield deepcopy(path)
            path.remove('E')
            return
        for nxt in nx.neighbors(self, vertex):
            for result in self.get_path_iter(nxt, path):
                yield result
        path.remove(vertex)

    def path_length(self, path):
        length = 0
        for vertex in path:
            length += self.nodes[vertex]['execution_time']
        return length

    @property
    def longest_paths(self):
        self.transform_add_source()
        self.transform_add_sink()

        longest_length = 0
        paths = []
        path = []
        # depth-first search
        for length, curr_path in self.get_longest_path_iter('S', path, 0):
            if length > longest_length:
                paths = [curr_path]
                longest_length = length
            elif length == longest_length:
                paths.append(curr_path)
        return paths

    def get_longest_path_iter(self, vertex, path, length):
        path.append(vertex)
        length += self.nodes[vertex]['execution_time']
        if vertex == 'E':
            yield length, deepcopy(path)
            path.remove('E')
            return
        for nxt in nx.neighbors(self, vertex):
            for result in self.get_longest_path_iter(nxt, path, length):
                yield result

        path.remove(vertex)
        length -= self.nodes[vertex]['execution_time']

    @property
    def longest_path_length(self):
        return len(self.longest_paths[0])

    @property
    def anti_chains(self):
        d = nx.DiGraph(self)
        return list(nx.antichains(d))

    @property
    def longest_anti_chain(self):
        anti_chains = self.anti_chains
        return [anti_chain for anti_chain in anti_chains if len(anti_chain) == self.longest_anti_chain_length]

    @property
    def longest_anti_chain_length(self):
        return max(len(anti_chain) for anti_chain in self.anti_chains)

    @property
    def sources(self):
        sources = []
        for node, in_degree in self.in_degree:
            if in_degree == 0:
                sources.append(node)
        return sources

    @property
    def sinks(self):
        sinks = []
        for node, in_degree in self.out_degree:
            if in_degree == 0:
                sinks.append(node)
        return sinks

    @property
    def max_in_degree(self):
        max_in_degree = 0
        for vertex, in_degree in self.in_degree:
            if in_degree > max_in_degree:
                max_in_degree = in_degree
        return max_in_degree

    @property
    def min_in_degree(self):
        min_in_degree = float('inf')
        for vertex, in_degree in self.in_degree:
            if in_degree < min_in_degree:
                min_in_degree = in_degree
        return min_in_degree

    @property
    def ave_in_degree(self):
        total = 0
        for vertex, in_degree in self.in_degree:
            total += in_degree
        return total / len(self)

    @property
    def max_out_degree(self):
        max_out_degree = 0
        for vertex, out_degree in self.out_degree:
            if out_degree > max_out_degree:
                max_out_degree = out_degree
        return max_out_degree

    @property
    def min_out_degree(self):
        min_out_degree = float('inf')
        for vertex, out_degree in self.out_degree:
            if out_degree < min_out_degree:
                min_out_degree = out_degree
        return min_out_degree

    @property
    def ave_out_degree(self):
        total = 0
        for vertex, out_degree in self.out_degree:
            total += out_degree
        return total / len(self)

    def get_in_degree(self, vertex):
        for v, in_degree in self.in_degree:
            if vertex ==  v:
                return in_degree

    def get_out_degree(self, vertex):
        for v, out_degree in self.out_degree:
            if vertex == v:
                return out_degree

    def transform_add_source(self):
        if 'S' in list(self.nodes):
            return
        self.add_node('S', execution_time=0, deadline=float("inf"), start_time=0, priority=0)
        for node in self.sources:
            if node != 'S' and node != 'E':
                self.add_edge('S', node)

    def transform_delete_source(self):
        for node in self.sources:
            self.remove_node(node)

    def transform_add_sink(self):
        if 'E' in list(self.nodes):
            return
        self.add_node('E', execution_time=0, deadline=float("inf"), start_time=0, priority=0)
        for node in self.sinks:
            if node != 'S' and node != 'E':
                self.add_edge(node, 'E')

    def transform_delete_sink(self):
        for node in self.sinks:
            self.remove_node(node)

    def draw(self, dir_path: Optional[str] = 'Graph/', format: Optional[str] = 'png'):
        g_graph = Digraph()

        # add vertex
        for vertex in self.nodes:
            if vertex == 'S':
                color = 'green'
            elif vertex == 'E':
                color = 'red'
            else:
                color = 'black'
            g_graph.node(name=str(vertex), color=color)

        # add edge
        for (start, end), _ in self.edges.items():
            g_graph.edge(str(start), str(end))

        g_graph.render(dir_path + self.dag_name, view=False, format=format)

    def networkx_export(self, dir_path: Optional[str] = 'Graph/'):
        data = nx.node_link_data(self)
        with open(dir_path + self.dag_name + '.json', 'w') as obj:
            json.dump(data, obj)

    def get_instances(self, task):
        if not self.periodic:
            raise AssertionError('非周期任务不能调用此方法')

        return [instance for instance in self.instances if instance.task == task]


if __name__ == "__main__":
    d = DAG(periodic=False)
    d.dag_name = '0'
    d.add_node('t0', execution_time=2, start_time=0, deadline=1)
    d.add_node('t1', execution_time=1, start_time=0, deadline=1)
    d.add_node('t2', execution_time=3, start_time=0, deadline=1)
    d.add_node('t3', execution_time=1, start_time=0, deadline=1)
    d.add_node('t4', execution_time=1, start_time=0, deadline=1)
    d.add_edges_from([('t0', 't2'), ('t1', 't2'), ('t2', 't3'), ('t3', 't4')])
    d.transform_add_sink()
    d.transform_add_source()
    d.draw()
    print(d.anti_chains)
    print(d.longest_anti_chain)
    print(d.longest_anti_chain_length)
