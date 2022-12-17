# dag -> judge -> valid / invalid (True / False)
from src.Generator.dag import DAG
from src.Analyzer.analyzer import get_property
from typing import List


class Condition:
    def __init__(self, property, operator, value):
        self.property = property
        self.operator = operator
        self.value = value

    def judge(self, dag: DAG) -> bool:
        if self.operator == '>':
            return get_property(dag, self.property) > self.value
        elif self.operator == '≥':
            return get_property(dag, self.property) >= self.value
        elif self.operator == '＝':
            return get_property(dag, self.property) == self.value
        elif self.operator == '≤':
            return get_property(dag, self.property) <= self.value
        elif self.operator == '＜':
            return get_property(dag, self.property) < self.value

    def __str__(self):
        return f"{self.property} {self.operator} {self.value}"


def is_eligible(dag: DAG, conditions: List[Condition]):
    for condition in conditions:
        if not condition.judge(dag):
            return False
    return True
