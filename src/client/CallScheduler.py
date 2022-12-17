import sys
from time import sleep
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QTableWidget,
    QTableWidgetItem,
    QAbstractItemView,
    QLabel,
    QMessageBox,
    QLayout,
)
from PyQt5.QtGui import QPixmap
from src.ui.Scheduler import Ui_Scheduler
from src.ui.Scheduler_main import Ui_Scheduler_main
from src.ui.tool_select import Ui_Tool_select
from src.ui.draw_sytem import SystemDrawing
from src.ui.draw_gantt import GanttDrawing
from src.Scheduler.scheduler import *
from src.Generator.generator import *
from src.ui.run import Ui_run_window
from src.client.utils import *
from src.Generator.multitask.dag import Task, TaskSet, Instance
from src.Generator.multitask.generator import Generator


class SchedulerMainWindow(QMainWindow, Ui_Scheduler_main):
    def __init__(self, main, parent=None):
        super().__init__(parent)
        self.main = main
        self.current_scheduler_set = None
        self.setupUi(self)
        self.scheduler_window = SchedulerWindow()
        self._set_table()
        self.scheduler_sets = []
        self.SchedulerSetList.currentItemChanged.connect(self.list_item_changed)

    def add_scheduler_set(self, scheduler_set: SchedulerSet):
        self.scheduler_sets.append(scheduler_set)
        self.update_scheduler_sets()

    # TODO
    def append_scheduler_set(self, name, dags):
        pass

    def update_scheduler_sets(self):
        self.SchedulerSetList.clear()
        self.SchedulerSetList.addItems([scheduler_set.name for scheduler_set in self.scheduler_sets])

    def list_item_changed(self, item):
        if item is None:
            return
        scheduler_set_name = item.text()
        self.current_scheduler_set: SchedulerSet = self._find_scheduler_set(scheduler_set_name)

        """ Set Scheduler args """
        self.processor_num_edit.setText(f'{self.current_scheduler_set.processor_num}')
        self.processor_mode_combo.setCurrentText(f'{self.current_scheduler_set.processor_mode}')
        self.preempt_mode_combo.setCurrentText(f'{self.current_scheduler_set.processor_type}')
        self.preempt_clock.setText(f'{self.current_scheduler_set.preempt_clock}')
        self.priority_assignment_combo.setCurrentText(f'{self.current_scheduler_set.priority_assignment}')

        """ Set DAG result """
        total_make_span = 0
        total_utilization = 0
        total_fail = 0

        self.dag_result.setRowCount(len(self.current_scheduler_set))
        for key, scheduler in enumerate(self.current_scheduler_set):
            """ dag_name """
            table_item = QTableWidgetItem(scheduler.dag.dag_name)
            self.dag_result.setItem(key, 0, table_item)
            """ dag runtime property """
            # make span
            if scheduler.is_fail:
                table_item = QTableWidgetItem('N/A')
            else:
                table_item = QTableWidgetItem(str(scheduler.make_span))
                total_make_span += scheduler.make_span
            self.dag_result.setItem(key, 1, table_item)
            # utilization
            table_item = QTableWidgetItem(f'{scheduler.overall_utilization}%')
            self.dag_result.setItem(key, 2, table_item)
            if not scheduler.is_fail:
                total_utilization += scheduler.overall_utilization
            # has_error
            if scheduler.is_fail:
                table_item = QTableWidgetItem(f'是')
                total_fail += 1
            else:
                table_item = QTableWidgetItem(f'否')
            self.dag_result.setItem(key, 3, table_item)
            # fail time
            if scheduler.is_fail:
                table_item = QTableWidgetItem(f'{scheduler.fail_time}')
            else:
                table_item = QTableWidgetItem(f'N/A')
            self.dag_result.setItem(key, 4, table_item)

        """ Set Scheduler result """
        """ Scheduler set name """
        table_item = QTableWidgetItem(scheduler_set_name)
        self.scheduler_result.setVerticalHeaderItem(0, table_item)
        """ Scheduler property """
        # make span
        if len(self.current_scheduler_set) == total_fail:
            table_item = QTableWidgetItem(f'N/A')
        else:
            table_item = QTableWidgetItem(f'{round(total_make_span / (len(self.current_scheduler_set) - total_fail), 2)}')
        self.scheduler_result.setItem(0, 0, table_item)
        # utilization
        if len(self.current_scheduler_set) == total_fail:
            table_item = QTableWidgetItem(f'N/A')
        else:
            table_item = QTableWidgetItem(f'{round(total_utilization / (len(self.current_scheduler_set) - total_fail), 2)}%')
        self.scheduler_result.setItem(0, 1, table_item)
        # has_error
        table_item = QTableWidgetItem(f'{total_fail}')
        self.scheduler_result.setItem(0, 2, table_item)

    def _find_scheduler_set(self, name):
        for scheduler_set in self.scheduler_sets:
            if scheduler_set.name == name:
                return scheduler_set
        raise ValueError(f'Can not find scheduler set named {name}')

    def _set_table(self):
        self.scheduler_result.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.dag_result.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.dag_result.doubleClicked.connect(self.show_scheduler_window)
        self.dag_result.verticalHeader().setVisible(False)

    def show_scheduler_window(self, index):
        index = index.row()
        scheduler = self.current_scheduler_set[index]
        scheduler.vertex_tracing_all()
        self.scheduler_window.transform(scheduler=scheduler)


class SchedulerWindow(QWidget, Ui_Scheduler):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_scheduler: Scheduler = None
        self.setupUi(self)
        self.t = -1  # SimTime
        self.simtime.setText(str(self.t))
        self.make_span = 0  # Make span
        self.backward_btn.clicked.connect(self.backward)
        self.forward_btn.clicked.connect(self.forward)
        self.start_btn.clicked.connect(self.start)
        self.pause_btn.clicked.connect(self.pause)
        self._init()

    def transform(self, scheduler: Scheduler):
        self.current_scheduler = scheduler
        print(self.current_scheduler.runtime_info_dict)
        self.make_span = self.current_scheduler.make_span
        self.t = -1
        self.simtime.setText(str(self.t))
        self._update(init=True)
        self.setVisible(True)

    def _init(self):
        self._init_tab()

    def _update(self, init=False, fail=False):
        self._update_dag(init)
        self._update_system(init, fail)
        self._update_gantt(init)
        self._update_tab(init)

    def _update_dag(self, init):
        print('update dag')
        if init:
            print('draw')
            self.current_scheduler.draw_dag()
            print('draw success')
        graph = QPixmap(f"Monitor/img/dag/{self.t + 1}.png")
        new_graph = resize_graph(graph, self.DAG_label)
        self.DAG_label.setPixmap(new_graph)
        print('update success')

    def _update_system(self, init, fail):
        if self.t == -1:
            scroll_filler = QWidget(self)
            self.system_scrollarea.setWidget(scroll_filler)
            return
        status = self.current_scheduler.system_status.get(self.t)
        scroll_filler = SystemDrawing(dag=self.current_scheduler.dag,
                                      capacity=self.current_scheduler.processors.capacity,
                                      users=status.users,
                                      put_queue=status.put_queue,
                                      fail=fail
                                      )
        self.system_scrollarea.setWidget(scroll_filler)

    def _update_gantt(self, init):
        if self.t == -1:
            scroll_filler = QWidget(self)
            self.gantt_scrollarea.setWidget(scroll_filler)
            return
        try:
            scroll_filler = GanttDrawing(capacity=self.current_scheduler.processors.capacity,
                                         dag=self.current_scheduler.dag,
                                         vertex_gantt=self.current_scheduler.vertex_gantt_info,
                                         processor_gantt=self.current_scheduler.processor_gantt_info,
                                         make_span=self.t,
                                         )
        except Exception as e:
            print(e)
        self.gantt_scrollarea.setWidget(scroll_filler)

    def _init_tab(self):
        self.scheduler_args_table.horizontalHeader().setVisible(False)
        self.scheduler_args_table.setRowCount(5)
        self.scheduler_args_table.setColumnCount(1)
        self.scheduler_args_table.setVerticalHeaderLabels(['处理器数量',
                                                           '处理器模式',
                                                           '抢占模式',
                                                           '抢占周期',
                                                           '优先级分配算法'
                                                           ])
        self.scheduler_args_table.setColumnWidth(0, 400)
        # self.scheduler_args_table.setEditTriggers(QAbstractItemView.NoEditTriggers)

        self.schedule_result_table.horizontalHeader().setVisible(False)
        self.schedule_result_table.setRowCount(5)
        self.schedule_result_table.setColumnCount(1)
        self.schedule_result_table.setVerticalHeaderLabels(['DAG名称',
                                                            '完工时间',
                                                            '长度',
                                                            '宽度',
                                                            '节点数量',
                                                            '边数量'
                                                            ])
        self.schedule_result_table.setColumnWidth(0, 400)
        self.schedule_result_table.setEditTriggers(QAbstractItemView.NoEditTriggers)

    def _update_tab(self, init):
        # scheduler_args_tab
        new_item = QTableWidgetItem(f'{self.current_scheduler.processors.capacity}')
        self.scheduler_args_table.setItem(0, 0, new_item)
        new_item = QTableWidgetItem(f'{self.current_scheduler.processor_mode}')
        self.scheduler_args_table.setItem(0, 1, new_item)
        new_item = QTableWidgetItem(f'{self.current_scheduler.processor_type}')
        self.scheduler_args_table.setItem(0, 2, new_item)
        new_item = QTableWidgetItem(f'{self.current_scheduler.preempt_clock}')
        self.scheduler_args_table.setItem(0, 3, new_item)
        new_item = QTableWidgetItem(f'{self.current_scheduler.priority_assignment}')
        self.scheduler_args_table.setItem(0, 4, new_item)

        # schedule_result_tab
        new_item = QTableWidgetItem(f'{self.current_scheduler.dag.dag_name}')
        self.schedule_result_table.setItem(0, 0, new_item)
        new_item = QTableWidgetItem(f'{self.current_scheduler.make_span}')
        self.schedule_result_table.setItem(0, 1, new_item)
        # new_item = QTableWidgetItem(f'{self.current_scheduler.dag.longest_path_length}')
        new_item = QTableWidgetItem(f'test')
        self.schedule_result_table.setItem(0, 2, new_item)
        # new_item = QTableWidgetItem(f'{self.current_scheduler.dag.longest_anti_chain_length}')
        new_item = QTableWidgetItem(f'test')
        self.schedule_result_table.setItem(0, 3, new_item)
        new_item = QTableWidgetItem(f'{len(self.current_scheduler.dag.nodes)}')
        self.schedule_result_table.setItem(0, 4, new_item)
        new_item = QTableWidgetItem(f'{len(self.current_scheduler.dag.edges)}')
        self.schedule_result_table.setItem(0, 5, new_item)

    def forward(self):
        # Validation
        if self.t == self.make_span:
            return False
        self.t += 1
        print('forward')
        print(self.t)
        self.simtime.setText(str(self.t))
        if self.current_scheduler.is_fail and self.t == self.current_scheduler.make_span:
            fail = True
        else:
            fail = False
        self._update(fail=fail)
        return True

    def backward(self):
        # Validation
        if self.t == -1:
            return False
        self.t -= 1
        print(self.t)
        print('backward')
        self.simtime.setText(str(self.t))
        self._update()
        return True

    def start(self):
        pass
        # while self.forward():
        #     sleep(1)

    def pause(self):
        pass


if __name__ == "__main__":
    app = QApplication(sys.argv)
    scheduler_main = SchedulerMainWindow(None)
    d = DAG(periodic=True)
    d.dag_name = 'DAG_0'
    d.add_node('t0,0', execution_time=3, start_time=0, deadline=4, priority=1)
    d.add_node('t0,1', execution_time=3, start_time=4, deadline=4, priority=1)
    d.add_node('t0,2', execution_time=3, start_time=8, deadline=4, priority=1)
    d.add_node('t1,0', execution_time=2, start_time=0, deadline=6, priority=2)
    d.add_node('t1,1', execution_time=2, start_time=6, deadline=6, priority=2)
    d.add_node('t2,0', execution_time=7, start_time=0, deadline=12, priority=3)
    ts = TaskSet([
        Task('t0', 3, 3, 4, 4),
        Task('t1', 2, 2, 6, 6),
        Task('t2', 7, 7, 12, 12),
    ])
    g = Generator(ts)
    g.generate().__next__()
    d.task_set = ts
    d.instances = g.instances

    # d.add_node('t0,0', execution_time=2, start_time=0, deadline=4, priority=0)
    # d.add_node('t0,1', execution_time=2, start_time=4, deadline=4, priority=0)
    # d.add_node('t0,2', execution_time=2, start_time=8, deadline=4, priority=0)
    # d.add_node('t1,0', execution_time=3, start_time=0, deadline=6, priority=1)
    # d.add_node('t1,1', execution_time=3, start_time=6, deadline=6, priority=1)
    # d.add_node('t2,0', execution_time=8, start_time=0, deadline=12, priority=2)
    d.add_edges_from([('t0,0', 't1,0'), ('t0,0', 't2,0'), ('t0,0', 't0,1'), ('t0,1', 't0,2'), ('t1,0', 't1,1')])
    d.transform_add_source()
    d.transform_add_sink()
    scheduler_main.add_scheduler_set(SchedulerSet(dags=[d],
                                                  processor_num=2,
                                                  # processor_type='non-preemptive',
                                                  processor_type='preemptive',
                                                  name='Scheduler_1',
                                                  # priority_assignment="EDF",
                                                  priority_assignment="FPS",
                                                  preempt_clock=1,
                                                  processor_mode="动态调度"
                                                  ))
    scheduler_main.show()
    sys.exit(app.exec_())
