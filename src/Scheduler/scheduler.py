import simpy
from simpy.events import EventPriority
from collections import OrderedDict
from src.Scheduler.priority_assignment import *
from src.Scheduler.workload import *
import src.Scheduler.Monitor.dag as dag
import src.Scheduler.Monitor.processor_gantt as processor_gantt
import src.Scheduler.Monitor.vertex_gantt as vertex_gantt
from src.Scheduler.Monitor.processor_utilization import processor_utilization
from src.Scheduler.Monitor.system_model import get_system_status_iter
from src.Scheduler.processors import *


processor_type_dict = {
    'non-preemptive': PriorityProcessor,
    'preemptive': PreemptiveProcessor,
}

priority_assignment_dict = {
    'RMS': RMS,
    'DMS': DMS,
    'FPS': FPS,
    'SJF': SJF,
    'CPFE': CPFE,
    'EDF': EDF,
    'LLF': LLF,
}


class Scheduler(simpy.Environment):
    # def __init__(self, dags: Iterable[DAG], processor_num: int=1) -> None:
    def __init__(self,
                 dag: DAG,
                 processor_num: int = 1,
                 processor_type: str = 'non-preemptive',
                 priority_assignment: str = "SJF",
                 preempt_clock: int = 1,
                 processor_mode: str = '动态调度'
                 ) -> None:
        super().__init__()
        self.processor_type = processor_type
        self.priority_assignment = priority_assignment
        self.processor_mode = processor_mode
        priority_assignment = priority_assignment_dict[priority_assignment]
        self.processors = processor_type_dict[processor_type](self,
                                                              capacity=processor_num,
                                                              priority_assignment=priority_assignment,
                                                              preempt_clock=preempt_clock)
        self.dag = dag
        self.preempt_clock = int(preempt_clock)
        self.process_dict, self.runtime_info_dict = dag2task(dag=dag,
                                                             env=self,
                                                             processors=self.processors,
                                                             priority_assignment=priority_assignment
                                                             )
        self.processors_dict: OrderedDict[SimTime, Dict[int, Any]] = OrderedDict()
        self.put_queue_dict: OrderedDict[SimTime, List[PriorityRequest]] = OrderedDict()
        self.is_finish = False
        self.is_fail = False
        self.fail_time = float("inf")

    @property
    def queue(self) -> List[Tuple[SimTime, EventPriority, int, Event]]:
        return self._queue

    @property
    def make_span(self) -> int:
        if self.is_fail:
            return self.fail_time
        return self.now

    @property
    def processor_utilization(self) -> Dict[int, float]:
        return processor_utilization(self.processors_dict,
                                     self.processors.capacity,
                                     self.make_span,
                                     )

    @property
    def overall_utilization(self):
        return round(sum(self.processor_utilization.values()) / self.processors.capacity, 2)

    @property
    def system_status(self):
        return get_system_status_iter(self.put_queue_dict, self.processors_dict, self.make_span + 1)

    @property
    def processor_gantt_info(self) -> Dict[int, List[List]]:
        return processor_gantt.get_processor_gantt_info(self.processors_dict,
                                                        self.processors.capacity,
                                                        self.make_span
                                                        )

    @property
    def vertex_gantt_info(self) -> Dict[Any, List[NamedTuple]]:
        return vertex_gantt.get_vertex_gantt_info(self.runtime_info_dict, self.dag)

    def run(self, until=None):
        """ Get events happens on env. """
        while self.queue:
            try:
                self.step()
            except RuntimeError as e:
                self.is_fail = True
                print(e.args[0])
                print(e.args[0][0])
                print(e.args[0][1])
                fail_task = e.args[0][0]
                self.fail_time = int(e.args[0][1])
                print(f'任务{fail_task}在{self.fail_time}执行失败')
                return
            if self.queue == [] or self.peek() != self.now:
                # TODO: update priority
                self.processors.schedule(self.dag, self.now)
            # if preempt clock arrive at the interval of self.now and self.peek(), add a timeout event.
            if self.peek() != self.now:
                # print(self.now, list(self.processors.users.values()), self.processors.put_queue)
                self.processors_dict.update({
                    self.now: {key: value for key, value in self.processors.users.items()}
                })
                self.put_queue_dict.update({
                    self.now: [item for item in self.processors.put_queue]
                })

                if self.processor_type == 'preemptive':
                    try:
                        nxt = int(self.peek())
                        for cnt in range(self.now + 1, nxt):
                            if cnt % self.preempt_clock == 0:
                                self.timeout(cnt - self.now)
                    except OverflowError:
                        pass

        self.is_finish = True

    def vertex_tracing(self, vertex) -> None:
        """ Get the trace of vertex. """
        print(f'{vertex}:')
        for (time, status, message) in self.runtime_info_dict[vertex]:
            print(f'\t{status.name} at time {time}', end=' ')
            if status == VertexStatus.Interrupted:
                by = [key for key, value in self.process_dict.items() if value == message['by']][0]
                print(f"by {by}, usage = {message['usage']}.", end='')
            if status == VertexStatus.Running:
                print(f"on P{message['on']}", end='')
            print()

    def vertex_tracing_all(self) -> None:
        """ Get the trace of all the vertex """
        for node in self.dag.nodes:
            self.vertex_tracing(node)

    def draw_dag(self, animate: bool = False):
        dag.trigger_draw(runtime_info_dict=self.runtime_info_dict,
                         dag=self.dag,
                         until=min(self.now + 1, self.fail_time + 1),
                         init=True,
                         is_fail=self.is_fail,
                         fail_time=self.fail_time
                         )
        if animate:
            dag.animate(self.now)

    def draw_processor_monitor(self, animate: bool = False):
        processor_gantt.draw(self.dag, self.processors_dict, self.now, self.processors.capacity)
        if animate:
            pass

    def draw_vertex_monitor(self, animate: bool = False):
        vertex_gantt.draw(self.runtime_info_dict, self.dag, self.now)
        if animate:
            pass


class SchedulerSet(list):
    """ Stores the results of each scheduling set. """
    count = 0

    def __init__(self,
                 dags: List[DAG],
                 processor_num: int = 1,
                 processor_type: str = 'non-preemptive',
                 priority_assignment: str = "SJF",
                 preempt_clock: int = 1,
                 processor_mode: str = '动态调度',
                 name: str = None) -> None:
        super().__init__()
        self.processor_num = processor_num
        self.processor_type = processor_type
        self.priority_assignment = priority_assignment
        self.preempt_clock = preempt_clock
        self.processor_mode = processor_mode
        for dag in dags:
            scheduler = Scheduler(dag=dag,
                                  processor_num=processor_num,
                                  processor_type=processor_type,
                                  priority_assignment=priority_assignment,
                                  preempt_clock=preempt_clock
                                  )
            self.append(scheduler)
            scheduler.run()
        SchedulerSet.count += 1
        if name is None:
            self.name = f'SchedulerSet{SchedulerSet.count}'
        else:
            self.name = name

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name


if __name__ == "__main__":
    # non-preemptive
    # d = DAG()
    # d.add_node(3)
    # d.add_edges_from([(1, 4), (1, 5), (4, 6), (4, 7)])
    # s = Scheduler(d, processor_num=2, processor_type='non-preemptive', priority_assignment=SJF)
    # s.run()
    # for node in s.dag.nodes:
    #     s.vertex_tracing(node)
    # s.draw_dag()
    # s.draw_processor_monitor()

    # preemptive
    # d = DAG()
    # d.add_node('t1', execution_time=1, start_time=1, deadline=3)
    # d.add_node('t4', execution_time=4, start_time=0, deadline=5)
    # d.add_node('t5', execution_time=5, start_time=0, deadline=7)
    # d.add_node('t6', execution_time=6, start_time=0, deadline=10)
    # d.add_node('t7', execution_time=7, start_time=0, deadline=15)
    # d.add_edges_from([('t1', 't4'), ('t1', 't5'), ('t4', 't6'), ('t4', 't7')])
    # s = Scheduler(d, processor_num=2, processor_type='preemptive', priority_assignment=LLF)
    # s.run()
    # for node in s.dag.nodes:
    #     s.vertex_tracing(node)
    # s.draw_dag()
    # s.draw_processor_monitor()
    # s.draw_vertex_monitor()
    # for node in s.dag.nodes:
    #     print(node, vertex_gantt.get_vertex_running_status(s.runtime_info_dict, node))
    # print(processor_gantt.get_processor_gantt_info(s.processors_dict, s.processors.capacity, s.now))
    # SchedulerSet
    # dags = [generate() for _ in range(5)]
    # ss = SchedulerSet(dags, 2)

    # test LLF
    # d = DAG(periodic=True)
    # d.add_node('t1,0', execution_time=2, start_time=0, deadline=3)
    # d.add_node('t1,1', execution_time=2, start_time=3, deadline=3)
    # d.add_node('t1,2', execution_time=2, start_time=6, deadline=3)
    # d.add_node('t1,3', execution_time=2, start_time=9, deadline=3)
    # d.add_node('t1,4', execution_time=2, start_time=12, deadline=3)
    # d.add_node('t2,0', execution_time=5, start_time=0, deadline=15)
    # # d.add_edges_from([('t1,0', 't1,1'), ('t1,1', 't1,2'), ('t2,0', 't2,1')])
    # s = Scheduler(d, processor_num=1, processor_type='non-preemptive', priority_assignment='LLF', preempt_clock=2)
    # s.run()
    # for node in s.dag.nodes:
    #     s.vertex_tracing(node)
    # s.draw_vertex_monitor()
    # s.draw_processor_monitor()
    # print(s.vertex_gantt_info)
    # print(s.processor_gantt_info)

    # test Gantt
    d = DAG(periodic=False)
    d.add_node('t0', execution_time=1, start_time=0, deadline=1)
    d.add_node('t1', execution_time=1, start_time=0, deadline=1)
    d.add_node('t2', execution_time=1, start_time=0, deadline=1)
    d.add_node('t3', execution_time=1, start_time=0, deadline=1)
    d.add_node('t4', execution_time=1, start_time=0, deadline=1)
    d.add_edges_from([('t0', 't2'), ('t1', 't2'), ('t2', 't3'), ('t3', 't4')])
    s = Scheduler(d, processor_num=1, processor_type='preemptive', priority_assignment='LLF', preempt_clock=1)
    s.run()
