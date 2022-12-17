# dag -> weighted dag

from src.Generator.dag import DAG
from random import randint
# test import
from src.Generator.generator import *


def rand(left: int, right: int, random: bool):
    if random:
        return randint(left, right)
    else:
        return left


def execution_time_generate(dag: DAG,
                            left: int,
                            right: int = None,
                            random: bool = False,
                            ):
    for vertex in dag.nodes:
        dag.nodes[vertex].update({'execution_time': rand(left, right, random)})


def deadline_generate(dag: DAG,
                      left: int,
                      right: int = None,
                      random: bool = False,
                      percent: bool = False):
    # Validation
    if percent:
        for vertex in dag.nodes:
            if dag.nodes[vertex].get('execution_time') is None:
                raise ValueError('未设置运行时间')
    for vertex in dag.nodes:
        if percent:
            execution_time = dag.nodes[vertex].get('execution_time')
            deadline_percent = int(rand(left, right, random) * execution_time / 100)
            dag.nodes[vertex].update({'deadline': deadline_percent})
        else:
            dag.nodes[vertex].update({'deadline': rand(left, right, random)})


def start_time_generate(dag: DAG,
                        left: int,
                        right: int = None,
                        random: bool = False
                        ):
    for vertex in dag.nodes:
        dag.nodes[vertex].update({'start_time': rand(left, right, random)})


if __name__ == '__main__':
    dag = gnp(5, 0.5)
    execution_time_generate(dag, 4, 10, True)
    start_time_generate(dag, 1, None, False)
    # deadline_generate(dag, 50, 80, True, True)
    deadline_generate(dag, 50, None, False, True)
    # deadline_generate(dag, 1, 3, True, False)
    # deadline_generate(dag, 2, None, False, False)

    for node in dag.nodes:
        print(dag.nodes[node])
