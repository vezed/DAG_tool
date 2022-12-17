import sys
from PyQt5.QtGui import QPainter, QBrush, QColor, QPen
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt, QEvent

PROCESSOR_NAME_WIDTH = 80
PROCESSOR_NAME_LENGTH = 30
PROCESSOR_ITEM_WIDTH = 120
PROCESSOR_ITEM_LENGTH = 100
PROCESSOR_CONTAINER_WIDTH = 100
PROCESSOR_CONTAINER_LENGTH = 80

QUEUE_ITEM_WIDTH = 120
QUEUE_ITEM_LENGTH = 100
QUEUE_CONTAINER_WIDTH = 100
QUEUE_CONTAINER_LENGTH = 80

RdYlGr = ['#d73027', '#f46d43', '#fdae61', '#fee08b', '#ffffbf', '#d9ef8b', '#66bd63', '#1a9850', '#90EE90', '#FFFFE0',
          '#48D1CC', '#DA70D6']
CLR_WAITING = '#0066FF'


class SystemDrawing(QWidget):
    def __init__(self, dag, capacity, users, put_queue, fail, parent=None):
        super().__init__(parent)
        self.dag = dag
        self.capacity = capacity
        self.users = users
        self.put_queue = put_queue
        self.fail = fail

        self.init()
        self.draw()

    def init(self):
        # length is fixed.
        length = 250
        # width = max(processor_width, queue_width)
        processor_width = self.capacity * PROCESSOR_ITEM_WIDTH
        queue_width = QUEUE_ITEM_WIDTH * len(self.put_queue) + 15
        width = max(processor_width, queue_width)
        self.setMinimumSize(width, length)

    def draw(self):
        for cnt in range(self.capacity):
            self.add_processor_item(cnt)
        put_queue_label = QLabel(self)
        put_queue_label.setText(f'就绪队列')
        put_queue_label.move(20, 130)
        if self.fail:
            return
        for cnt, request in enumerate(self.put_queue):
            self.add_put_queue_item(cnt, request)

    def add_processor_item(self, cnt):
        processor = cnt
        request = self.users.get(processor)

        # Draw the cnt th processor
        processor_name_lbl = QLabel(self)
        processor_name_lbl.setText(f'P{processor}')
        processor_name_lbl.move(cnt * PROCESSOR_ITEM_WIDTH + 20, 20)

        processor_container_lbl = QLabel(self)
        processor_container_lbl.move(cnt * PROCESSOR_ITEM_WIDTH + 20, 40)
        if request is None or self.fail:
            processor_container_lbl.setText('IDLE')
        else:
            vertex_name = request.vertex_name
            vertex = self.dag.nodes[vertex_name]
            processor_container_lbl.setText(f"{vertex_name}\n"
                                            f"Prior:{vertex['priority']}")

    def add_put_queue_item(self, cnt, request):
        # draw cnt th queue item
        item_lbl = QLabel(self)
        vertex_name = request.vertex_name
        vertex = self.dag.nodes[vertex_name]
        item_lbl.setText(f"{vertex_name}\n"
                         f"Prior:{vertex['priority']}")
        item_lbl.move(cnt * QUEUE_ITEM_WIDTH + 20, 150)

    def paintEvent(self, e):
        qp = QPainter()
        qp.begin(self)
        pen = QPen(Qt.black, 2, Qt.SolidLine)
        qp.setPen(pen)
        self.drawSystem(qp)
        qp.end()

    def drawSystem(self, qp):
        # draw processors
        for cnt in range(self.capacity):
            processor = cnt
            request = self.users.get(processor)
            # if request is None or self.fail:
            #     color = '#ffffff'
            # else:
                # vertex_name = request.vertex_name
                # index = list(self.dag).index(str(vertex_name))
                # color = RdYlGr[index % len(RdYlGr)]
            color = RdYlGr[cnt % len(RdYlGr)]

            color = QColor(color)
            brush = QBrush(color)
            qp.setBrush(brush)
            qp.drawRect(cnt * PROCESSOR_ITEM_WIDTH + 20,
                        40,
                        PROCESSOR_CONTAINER_WIDTH,
                        PROCESSOR_CONTAINER_LENGTH
                        )

        if self.fail:
            return
        # draw vertexes
        cnt = 0
        for vertex in self.put_queue:
            index = list(self.dag).index(str(vertex))
            color = CLR_WAITING
            color = QColor(color)
            brush = QBrush(color)
            qp.setBrush(brush)
            qp.drawRect(cnt * PROCESSOR_ITEM_WIDTH + 20,
                        150,
                        QUEUE_CONTAINER_WIDTH,
                        QUEUE_CONTAINER_LENGTH
                        )
            cnt += 1


class ELabel(QLabel):
    def __init__(self, parent=None):
        super(ELabel, self).__init__(parent)

    def event(self, a0: QEvent) -> bool:
        if a0.type() == QEvent.ToolTip:
            self.setToolTip(self.text())
        return QLabel.event(self, a0)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    demo = SystemDrawing(3, {1: 't1', 2: 't2'}, ['t3', 't4', 't5', 't6', 't7', 't8', 't9'])
    demo.show()
    sys.exit(app.exec_())
