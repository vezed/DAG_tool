import networkx as nx
from src.Generator.dag import DAG
import matplotlib.pyplot as plt
from random import randrange


def random():
    return randrange(100) / 100


def gnp(n, p):
    if n <= 0:
        raise ValueError('节点数量为正整数')
    if p < 0 or p > 1:
        raise ValueError('概率为0-1的浮点数')

    dag = DAG(periodic=False)
    # dag.add_nodes_from([f't{i}' for i in range(n)])
    dag.add_nodes_from([f't{i}' for i in range(n)])
    # for node in dag.nodes:
    #     dag.nodes[node].update({'execution_time': 1})

    n_lst = list(dag)
    for i in range(n):
        for j in range(i):
            if random() < p:
                dag.add_edge(n_lst[j], n_lst[i])
    return dag


def gnm(n, m):
    if n <= 0:
        raise ValueError('节点数量为正整数')
    if type(m) is not int:
        raise TypeError('边数量为整数的')
    if m < 0:
        raise ValueError('边数量不得小于0')
    dag = DAG(periodic=False)
    # dag.add_nodes_from([f't{i}' for i in range(n)])
    dag.add_nodes_from([f't{i}' for i in range(n)])
    # for node in dag.nodes:
    #     dag.nodes[node].update({'execution_time': 2})

    if n == 1:
        return dag
    max_edges = n * (n - 1) / 2.0
    if m > max_edges:
        m = max_edges

    n_lst = list(dag)
    edge_count = 0
    while edge_count < m:
        # generate random edge
        u = randrange(1, n)
        v = randrange(u)
        if dag.has_edge(n_lst[v], n_lst[u]):
            continue
        else:
            dag.add_edge(n_lst[v], n_lst[u])
            edge_count = edge_count + 1
    return dag


def fan_in_fan_out():
    pass


def layer_by_layer():
    pass


def random_orders():
    pass


if __name__ == "__main__":
    d = gnm(5, 4)
    nx.draw_networkx(d)
    plt.show()
