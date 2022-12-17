import sys
from collections import namedtuple
from typing import Dict, List, Any, NamedTuple
from PyQt5.QtGui import QPainter, QBrush, QColor, QPen
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt, QRect
from src.Generator.dag import DAG

NAME_WIDTH = 50
NAME_MID = 15
UNIT_WIDTH = 60
UNIT_LENGTH = 40
ROW_INTERVAL = 60
SCALE_LENGTH = 40
SCALE_VERTICAL_ROW = 25
SCALE_HEIGHT = 10


RdYlGr = ['#d73027', '#f46d43', '#fdae61', '#fee08b', '#ffffbf', '#d9ef8b', '#a6d96a', '#66bd63', '#1a9850', '#90EE90',
          '#FFFFE0', '#48D1CC', '#DA70D6']

running_time = namedtuple('running_time', ['start', 'end', 'on'])


class GanttDrawing(QWidget):
    def __init__(self,
                 capacity: int,
                 dag: DAG,
                 vertex_gantt: Dict[Any, List[NamedTuple]],
                 processor_gantt: Dict[int, List[List]],
                 make_span: int,
                 parent=None):
        super().__init__(parent)
        self.capacity = capacity
        self.dag = dag
        self.vertex_gantt = vertex_gantt
        self.processor_gantt = processor_gantt
        self.make_span = make_span
        self.init_widget()

    def init_widget(self):
        self.vertex_gantt = self.vertex_gantt
        self.processor_gantt = self.processor_gantt
        # length depends on num of processors and vertexes.
        if self.dag.periodic:
            self.length = ROW_INTERVAL * (self.capacity + len(self.dag.tasks)) + 40
        else:
            self.length = ROW_INTERVAL * (self.capacity + len(self.dag.nodes) - 2) + 40
        # width depends on make span.
        self.width = NAME_WIDTH + UNIT_WIDTH * self.make_span + 40
        self.setMinimumSize(self.width, self.length)

        cnt = 0
        # processors label
        for cnt in range(self.capacity):
            processor_name_label = QLabel(self)
            processor_name_label.setText(f'P{cnt}')
            processor_name_label.move(5, cnt * ROW_INTERVAL + SCALE_LENGTH + NAME_MID)
            cnt += 1

        # vertexes label
        if self.dag.periodic:
            self.periodic_dict = {}
            for task in self.dag.tasks:
                task_label = QLabel(self)
                task_label.setText(f'{task.name}')
                task_label.move(5, cnt * ROW_INTERVAL + SCALE_LENGTH + NAME_MID)
                self.periodic_dict.update({task.name: cnt})
                cnt += 1
        else:
            for vertex in self.dag.nodes:
                if vertex == 'S' or vertex == 'E':
                    continue
                vertex_label = QLabel(self)
                vertex_label.setText(f'{vertex}')
                vertex_label.move(5, cnt * ROW_INTERVAL + SCALE_LENGTH + NAME_MID)
                cnt += 1

    def paintEvent(self, event):
        qp = QPainter()
        qp.begin(self)
        pen = QPen(Qt.black, 2, Qt.SolidLine)
        qp.setPen(pen)
        self.draw_scale_mark(qp, event)
        if self.dag.periodic:
            self.drawGanttsPeriodic(qp)
        else:
            self.drawGanttsAperiodic(qp)
        qp.end()

    def draw_scale_mark(self, qp, event):
        # Vertical
        qp.drawLine(NAME_WIDTH,  # column start
                    SCALE_VERTICAL_ROW,  # row start
                    NAME_WIDTH + self.make_span * UNIT_WIDTH,  # column end
                    SCALE_VERTICAL_ROW  # row end
                    )
        # Mark
        for t in range(self.make_span + 1):
            # Set pen
            if t == self.make_span:
                pen = QPen(Qt.blue, 2, Qt.SolidLine)
                qp.setPen(pen)
            # Line
            qp.drawLine(NAME_WIDTH + t * UNIT_WIDTH,  # column start
                        SCALE_VERTICAL_ROW,  # row start
                        NAME_WIDTH + t * UNIT_WIDTH,  # column end
                        SCALE_VERTICAL_ROW + SCALE_HEIGHT  # row end
                        )
            # Number
            rect = QRect(0.667 * (NAME_WIDTH + t * UNIT_WIDTH),  # column start
                         SCALE_VERTICAL_ROW - 20,  # row start
                         0.667 * (NAME_WIDTH + t * UNIT_WIDTH),  # column end
                         SCALE_VERTICAL_ROW - 10  # row end
                         )
            qp.drawText(rect, Qt.AlignCenter, str(t))
            # Reset Pen
            if t == self.make_span:
                qp.drawLine(NAME_WIDTH + t * UNIT_WIDTH,  # column start
                            SCALE_VERTICAL_ROW,  # row start
                            NAME_WIDTH + t * UNIT_WIDTH,  # column end
                            self.length  # row end
                            )
                qp.drawText(rect, Qt.AlignCenter, str(t))
                pen = QPen(Qt.black, 2, Qt.SolidLine)
                qp.setPen(pen)

    def drawGanttsAperiodic(self, qp):
        self.draw_processors(qp)
        self.drawAperiodicVertexes(qp)

    def drawGanttsPeriodic(self, qp):
        self.draw_processors(qp)
        self.drawPeriodicVertexes(qp)

    def drawAperiodicVertexes(self, qp):
        cnt = self.capacity
        # draw vertexes
        for vertex_name, info in self.vertex_gantt.items():
            if str(vertex_name) == 'S' or str(vertex_name) == 'E':
                continue

            # vertex gantt
            for key, (start, end, on) in enumerate(info):
                # Validation
                if start >= self.make_span:
                    break
                if end > self.make_span:
                    end = self.make_span
                    finish = False
                else:
                    finish = True

                # draw
                self.draw_aperiod_arrive_arrow_trigger(qp)
                self.draw_finish_arrow(qp, key, start, end, cnt, info, finish)
                self.draw_bar(qp, on, start, end, cnt)

            cnt += 1

    def drawPeriodicVertexes(self, qp):
        # # draw vertexes
        for vertex_name, info in self.vertex_gantt.items():
            if vertex_name == 'S' or vertex_name == 'E':
                continue

            # vertex gantt
            for key, (start, end, on) in enumerate(info):
                # validation
                if start >= self.make_span:
                    break
                if end > self.make_span:
                    end = self.make_span
                    finish = False
                else:
                    finish = True

                # Get cnt
                for task in self.periodic_dict.keys():
                    if vertex_name.startswith(task):
                        cnt = self.periodic_dict[task]
                        break

                # draw
                self.draw_period_arrive_arrow_trigger(qp)
                self.draw_finish_arrow(qp, key, start, end, cnt, info, finish)
                self.draw_bar(qp, on, start, end, cnt)

    def draw_aperiod_arrive_arrow_trigger(self, qp):
        for vertex in self.dag.nodes:
            if vertex == 'S' or vertex == 'E':
                continue
            cnt = self.capacity + list(self.vertex_gantt.keys()).index(vertex)
            start_time = self.dag.nodes[vertex]['start_time']
            if start_time <= self.make_span:
                self.draw_arrive_arrow(qp, start_time, cnt)

    def draw_period_arrive_arrow_trigger(self, qp):
        for vertex in self.dag.nodes:
            if vertex == 'S' or vertex == 'E':
                continue

            for task in self.periodic_dict.keys():
                print(vertex, type(vertex))
                if vertex.startswith(task):
                    cnt = self.periodic_dict[task]
                    break
            start_time = self.dag.nodes[vertex]['start_time']
            if start_time <= self.make_span:
                self.draw_arrive_arrow(qp, start_time, cnt)

    def draw_arrive_arrow(self, qp, start_time, cnt):
        # draw arrive arrow
        # Vertical
        qp.drawLine(NAME_WIDTH + start_time * UNIT_WIDTH,  # column start
                    SCALE_LENGTH + cnt * ROW_INTERVAL + UNIT_LENGTH,  # row start
                    NAME_WIDTH + start_time * UNIT_WIDTH,  # column end
                    SCALE_LENGTH + cnt * ROW_INTERVAL - 14  # row end
                    )
        # left -> right
        qp.drawLine(NAME_WIDTH + start_time * UNIT_WIDTH - 3,  # column start
                    SCALE_LENGTH + cnt * ROW_INTERVAL - 10,  # row start
                    NAME_WIDTH + start_time * UNIT_WIDTH,  # column end
                    SCALE_LENGTH + cnt * ROW_INTERVAL - 14  # row end
                    )
        # right -> left
        qp.drawLine(NAME_WIDTH + start_time * UNIT_WIDTH + 3,  # column start
                    SCALE_LENGTH + cnt * ROW_INTERVAL - 10,  # row start
                    NAME_WIDTH + start_time * UNIT_WIDTH,  # column end
                    SCALE_LENGTH + cnt * ROW_INTERVAL - 14  # row end
                    )

    def draw_finish_arrow(self, qp, key, start, end, cnt, info, finish):
        # draw finish arrow
        if key == len(info) - 1 and finish:
            # Vertical
            qp.drawLine(NAME_WIDTH + start * UNIT_WIDTH + UNIT_WIDTH * (end - start),  # column start
                        SCALE_LENGTH + cnt * ROW_INTERVAL - 14,  # row start
                        NAME_WIDTH + start * UNIT_WIDTH + UNIT_WIDTH * (end - start),  # column end
                        SCALE_LENGTH + cnt * ROW_INTERVAL + UNIT_LENGTH  # row end
                        )
            # left -> right
            qp.drawLine(NAME_WIDTH + start * UNIT_WIDTH + UNIT_WIDTH * (end - start) - 3,  # column start
                        SCALE_LENGTH + cnt * ROW_INTERVAL - 4,  # row start
                        NAME_WIDTH + start * UNIT_WIDTH + UNIT_WIDTH * (end - start),  # column end
                        SCALE_LENGTH + cnt * ROW_INTERVAL  # row end
                        )
            # right -> left
            qp.drawLine(NAME_WIDTH + start * UNIT_WIDTH + UNIT_WIDTH * (end - start) + 3,  # column start
                        SCALE_LENGTH + cnt * ROW_INTERVAL - 4,  # row start
                        NAME_WIDTH + start * UNIT_WIDTH + UNIT_WIDTH * (end - start),  # column end
                        SCALE_LENGTH + cnt * ROW_INTERVAL  # row end
                        )

    def draw_bar(self, qp, on, start, end, cnt):
        # Set Brush
        color = RdYlGr[on % len(RdYlGr)]
        color = QColor(color)
        brush = QBrush(color)
        qp.setBrush(brush)
        # draw
        qp.drawRect(NAME_WIDTH + start * UNIT_WIDTH,  # column
                    SCALE_LENGTH + cnt * ROW_INTERVAL,  # row
                    UNIT_WIDTH * (end - start),  # width
                    UNIT_LENGTH  # length
                    )

    def draw_processors(self, qp):
        cnt = 0
        # draw processors
        for processor, info in self.processor_gantt.items():
            # print(processor)
            # processor gantt
            for start, end, vertex_name in info:
                if start >= self.make_span:
                    break
                if end > self.make_span:
                    end = self.make_span
                if vertex_name is None:
                    # color = '#ffffff'
                    color = '#808080'
                    # color = RdYlGr[processor % len(RdYlGr)]
                    color = QColor(color)
                    brush = QBrush(color)
                    qp.setBrush(brush)
                    qp.drawRect(NAME_WIDTH + start * UNIT_WIDTH,
                                SCALE_LENGTH + cnt * ROW_INTERVAL,
                                UNIT_WIDTH * (end - start),
                                UNIT_LENGTH
                                )
            cnt += 1


if __name__ == "__main__":
    d = DAG(periodic=True)
    d.add_node('t1,0', execution_time=2, start_time=0, deadline=3)
    d.add_node('t1,1', execution_time=2, start_time=3, deadline=3)
    d.add_node('t1,2', execution_time=2, start_time=6, deadline=3)
    d.add_node('t1,3', execution_time=2, start_time=9, deadline=3)
    d.add_node('t1,4', execution_time=2, start_time=12, deadline=3)
    d.add_node('t2,0', execution_time=5, start_time=0, deadline=15)
    app = QApplication(sys.argv)
    demo = GanttDrawing(capacity=1,
                        dag=d,
                        vertex_gantt={'t1,0': [running_time(start=0, end=2, on=0)], 't1,1': [running_time(start=4, end=6, on=0)], 't1,2': [running_time(start=6, end=8, on=0)], 't1,3': [running_time(start=10, end=12, on=0)], 't1,4': [running_time(start=12, end=14, on=0)], 't2,0': [running_time(start=2, end=4, on=0), running_time(start=8, end=10, on=0), running_time(start=14, end=15, on=0)]},
                        processor_gantt={0: [[0, 2, 't1,0'], [2, 4, 't2,0'], [4, 6, 't1,1'], [6, 8, 't1,2'], [8, 10, 't2,0'], [10, 12, 't1,3'], [12, 14, 't1,4'], [14, 15, 't2,0']]},
                        make_span=15
                        )
    demo.show()
    sys.exit(app.exec_())
