from src.Generator.dag import DAG
from typing import List


def merge(dag_set: List[DAG]):
    pass


if __name__ == "__main__":
    d = DAG(periodic=False)
    d.add_node('t1', execution_time=1, start_time=0, deadline=180)
    d.add_node('t2', execution_time=7, start_time=0, deadline=180)
    d.add_node('t3', execution_time=3, start_time=0, deadline=180)
    d.add_node('t4', execution_time=3, start_time=0, deadline=180)
    d.add_node('t5', execution_time=6, start_time=0, deadline=180)
    d.add_node('t6', execution_time=1, start_time=0, deadline=180)
    d.add_node('t7', execution_time=2, start_time=0, deadline=180)
    d.add_node('t8', execution_time=1, start_time=0, deadline=180)
