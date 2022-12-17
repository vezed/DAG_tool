import os
import shutil
import sys
import enum
from typing import Dict, List
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QMdiSubWindow,
    QTableWidgetItem,
    QAbstractItemView,
    QLabel,
    QMessageBox,
    QPushButton,
    QMenu,
    QAction,
    QFileDialog,
    QInputDialog,
    QTableWidget
)
from math import ceil, floor
from PyQt5.QtCore import Qt, QDir, QThread, pyqtSignal
from PyQt5 import QtCore
from PyQt5.QtGui import QPixmap, QCursor
from src.ui.Generator_main import Ui_Generator_main
from src.ui.aperiodic_generate import Ui_aperiodic_generate
from src.ui.periodic_generate import Ui_periodic_generate
from src.ui.run import Ui_run_window
from src.ui.property_selection import Ui_property_selection
from src.ui.property_distribution_controller import Ui_property_distribution_controller
from src.ui.process_bar import Ui_process
from src.Generator.dag import DAG
from src.Generator.generator import *
from src.Generator.random_weight import *
from src.Generator.multitask.generator import *
from src.Generator.distribute_controller import *
from src.Scheduler.scheduler import SchedulerSet
from src.client.utils import *
from src.Analyzer.analyzer import get_property


class ViewStatus(Enum):
    graph = 0
    table = 1
    tree = 2


class GeneratorMainWindow(QMainWindow, Ui_Generator_main):
    def __init__(self, main, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.main = main

        """ current generation """
        self.current_generation: List[DAG] = []

        """ generate window """
        self.aperiodic_generate_window = AperiodicGenerateWindow(self)
        self.periodic_generate_window = PeriodicGenerateWindow(self)
        self.actionperiodic.triggered.connect(self.periodic_generate)
        self.actionaperiodic.triggered.connect(self.aperiodic_generate)

        """ generate result """
        self.generation_set: Dict[str, List[DAG]] = {}  # key: generation name, value: generation
        self.generate_result.currentItemChanged.connect(self.transform)

        """ view """
        self.view = ViewStatus.graph
        self.actiongraphview.triggered.connect(self.update_graph_view)
        self.actiontableview.triggered.connect(self.update_table_view)
        # self.actiontreeview.triggered.connect(self.update_tree_view)

        """ Analyzer """
        self.configuration_window = ConfigurationWindow(self)
        self.actionconfiguration.triggered.connect(self.configuration_window_show)

        """ schedule simulation """
        self.generate_result.setContextMenuPolicy(Qt.CustomContextMenu)
        self.generate_result.customContextMenuRequested[QtCore.QPoint].connect(self.generation_operate_menu_show)
        self.run_window = RunWindow(self)

    def transform(self, e):
        if e is None:
            return
        current_generation_name = e.text()
        print(current_generation_name)
        self.current_generation = self.generation_set[current_generation_name]
        self._update()

    def _update(self):
        if self.current_generation is None:
            return
        if self.view == ViewStatus.graph:
            self.update_graph_view()
        elif self.view == ViewStatus.table:
            self.update_table_view()
        elif self.view == ViewStatus.tree:
            self.update_tree_view()

    def generation_operate_menu_show(self):
        def process_trigger(q):
            try:
                current_generation_name = self.generate_result.currentItem().text()
            except Exception as e:
                QMessageBox.warning(self, "错误", '选择一个生成结果进行操作')
                return
            current_generation: List[DAG] = self.generation_set[current_generation_name]

            if q.text() == "运行":
                print(f'运行{current_generation_name}')
                self.run_window.show()

            if q.text() == "删除":
                print(f'删除{current_generation_name}')
                self.generation_set.pop(current_generation_name)
                self.delete_result(self.generate_result.currentItem())

            if q.text() == "导出":
                print(f'导出{current_generation_name}')
                dlg = QFileDialog()
                dlg.setFileMode(QFileDialog.Directory)
                dlg.setFilter(QDir.Files)

                if dlg.exec_():
                    directory = dlg.selectedFiles()[0]

                    if not directory:
                        return

                directory += "/"

                formats = ["DOT",
                         "NetworkX (*.json)",
                         "JPG (*.jpg)",
                         "PNG (*.png)",
                         ]

                format, ok = QInputDialog.getItem(self, "选择导出类型", "类型列表", formats, 0, False)
                if not ok and format:
                    return

                print(directory, format)

                if format == "JPG (*.jpg)" or format == "PNG (*.png)":
                    if format == "JPG (*.jpg)":
                        format = 'jpg'
                    if format == "PNG (*.png)":
                        format = 'png'
                    for dag in current_generation:
                        dag.draw(directory, format)
                        os.remove(directory + dag.dag_name)

                elif format == "DOT":
                    for dag in current_generation:
                        dag.draw(directory, 'png')
                        os.remove(directory + dag.dag_name + '.png')

                elif format == "NetworkX (*.json)":
                    for dag in current_generation:
                        dag.networkx_export(directory)

        self.generation_menu = QMenu(self)
        self.generation_menu.addAction(QAction(u'运行', self))
        self.generation_menu.addAction(QAction(u'删除', self))
        self.generation_menu.addAction(QAction(u'导出', self))
        self.generation_menu.triggered[QAction].connect(process_trigger)
        self.generation_menu.exec_(QCursor.pos())

    def update_graph_view(self):
        self.view = ViewStatus.graph
        dir_path = 'Graph/'
        if os.path.exists(dir_path):
            shutil.rmtree(dir_path)
        for dag in self.current_generation:
            dag.draw()

        scroll_filler = QWidget()
        for cnt, dag in enumerate(self.current_generation):
            # graph label
            graph_label = QLabel(scroll_filler)
            graph_label.resize(240, 240)

            graph = QPixmap(f"Graph/{dag.dag_name}.png")
            new_graph = resize_graph(graph, graph_label)

            graph_label.setPixmap(new_graph)
            graph_label.move((cnt % 5) * 250 + int((240 - new_graph.width()) / 2), int(cnt / 5) * 270)  # column, row

            # name label
            name_label = QLabel(scroll_filler)
            name_label.setText(dag.dag_name)
            name_label.move((cnt % 5) * 250 + 100, (int(cnt / 5) + 1) * 270 - 20)

        scroll_filler.setMinimumSize(1260, (ceil(len(self.current_generation) / 5) * 270))
        self.scrollArea.setWidget(scroll_filler)

    def update_table_view(self):
        self.view = ViewStatus.table
        scroll_filler = QWidget()
        table = QTableWidget(scroll_filler)
        self.set_table(table)

        # Set contents of table
        table.setRowCount(len(self.current_generation))
        for cnt, dag in enumerate(self.current_generation):
            selected_property = self.configuration_window.selected_property
            table.setColumnCount(len(selected_property) + 1)
            labels = ['DAG名称']
            labels.extend(selected_property)
            table.setHorizontalHeaderLabels(labels)

            #  DAG name
            new_item = QTableWidgetItem(dag.dag_name)
            table.setItem(cnt, 0, new_item)
            # DAG properties
            for key, property_name in enumerate(selected_property):
                column = key + 1
                proper = get_property(dag, property_name)
                print(cnt, column, property_name, proper)
                new_item = QTableWidgetItem(str(proper))
                table.setItem(cnt, column, new_item)

        scroll_filler.setMinimumSize(1260, 650)
        self.scrollArea.setWidget(scroll_filler)
        print('table view')

    def set_table(self, table: QTableWidget):
        # basic
        table.setGeometry(0, 0, 1311, 701)
        table.verticalHeader().setVisible(False)
        table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        # context menu
        table.setContextMenuPolicy(Qt.CustomContextMenu)
        table.customContextMenuRequested[QtCore.QPoint].connect(self.property_table_edit_show)

    def set_table_property(self, row: int, dag: DAG, table: QTableWidget):
        selected_property = self.configuration_window.selected_property
        print(selected_property)
        table.setColumnCount(len(selected_property) + 1)
        labels = ['DAG名称']
        labels.extend(selected_property)
        print(row)
        table.setHorizontalHeaderLabels(labels)
        for key, property_name in enumerate(selected_property):
            column = key + 1
            proper = get_property(dag, property_name)
            print(row, column, property_name, proper)
            table.setItem(row, column, QTableWidgetItem(str(proper)))

    def property_table_edit_show(self):
        def process_trigger(q):
            if q.text() == "编辑":
                print('编辑')
            elif q.text() == "删除":
                print('删除')

        self.property_table_edit_menu = QMenu(self)
        self.property_table_edit_menu.addAction(QAction(u'编辑', self))
        self.property_table_edit_menu.addAction(QAction(u'删除', self))
        self.property_table_edit_menu.triggered[QAction].connect(process_trigger)
        self.property_table_edit_menu.exec_(QCursor.pos())

    def configuration_window_show(self):
        self.configuration_window.show()

    def update_tree_view(self):
        self.view = ViewStatus.tree
        print('tree view')

    def add_generation(self, generation_name):
        self.generate_result.addItem(generation_name)

    def delete_result(self, item):
        self.generate_result.clear()
        self.generate_result.addItems(self.generation_set.keys())

    def aperiodic_generate(self):
        self.aperiodic_generate_window.show()

    def periodic_generate(self):
        self.periodic_generate_window.show()


class AperiodicGenerateWindow(QWidget, Ui_aperiodic_generate):
    def __init__(self, parent_window: GeneratorMainWindow, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.parent_window: GeneratorMainWindow = parent_window

        """ init """
        self.arg_lst = []
        self._set_table()

        """ method combo """
        self.methods = {
            'GNP': {
                'func': gnp,
                'args': ['n', 'p'],
                'type': ['int', 'float']
            },
            'GNM': {
                'func': gnm,
                'args': ['n', 'm'],
                'type': ['int', 'int']
            },
            'Layer-by-Layer': {
                'func': layer_by_layer,
                'args': ['n', 'k', 'p'],
                'type': ['int', 'int', 'float']
            },
            'Fan-in/Fan-out': {
                'func': fan_in_fan_out,
                'args': ['n', 'id', 'od'],
                'type': ['int', 'int', 'int']
            },
            'Random Orders': {
                'func': random_orders,
                'args': ['n', 'k'],
                'type': ['int', 'int']
            }
        }
        self.method_combo.addItems(list(self.methods.keys()))
        self.method_combo.currentIndexChanged.connect(self.method_change)
        # dummy
        self.method_combo.setCurrentIndex(1)
        self.method_combo.setCurrentIndex(0)

        """ Conform """
        self.conform.clicked.connect(self.generate)

        """ random weight generation """
        self.deadline_percent_checkbox.toggled.connect(self._deadline_percent_checkbox_toggled)
        self.deadline_percent_checkbox.setChecked(True)
        self.deadline_percent_checkbox.setChecked(False)
        self.execution_time_random_checkbox.toggled.connect(self._execution_time_random_checkbox_toggled)
        self.execution_time_random_checkbox.setChecked(True)
        self.execution_time_random_checkbox.setChecked(False)
        self.deadline_random_checkbox.toggled.connect(self._deadline_random_checkbox_toggled)
        self.deadline_random_checkbox.setChecked(True)
        self.deadline_random_checkbox.setChecked(False)
        self.start_time_random_checkbox.toggled.connect(self._start_time_random_checkbox_toggled)
        self.start_time_random_checkbox.setChecked(True)
        self.start_time_random_checkbox.setChecked(False)

        """ Distribution Controller """
        self.distribution_controller_window = PropertyDistributionControllerWindow(self)
        self.conditions: List[Condition] = []
        self.property_distribute_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.property_distribute_list.customContextMenuRequested[QtCore.QPoint].connect(self.distribution_control)

        """ process bar """
        self.process_bar = ProcessWindow(self)

        """ test """
        self.deadline_left_edit.setText('100')
        self.execution_time_left_edit.setText('1')
        self.start_time_left_edit.setText('0')
        self.name_edit.setText('Generation_1')
        self.num_edit.setText('10')
        self.method_combo.setCurrentIndex(0)

    def generate(self):
        """ Generate a DAG from input to the interactive interface. """
        """ basic information validation """
        if not self.name_edit.text():
            QMessageBox.warning(self, "错误", "名称不能为空")
            return
        if self.name_edit.text() in self.parent_window.generation_set.keys():
            QMessageBox.warning(self, "错误", "生成结果重名")
            return
        if not self.num_edit.text():
            QMessageBox.warning(self, "错误", "生成数量不能为空")
            return
        try:
            num = int(self.num_edit.text())
        except ValueError:
            QMessageBox.warning(self, "错误", "生成数量只能为整数")
            return

        """ fetch information """
        generation_name = self.name_edit.text()
        method_selected_name = self.method_combo.currentText()
        method_selected = self.methods[method_selected_name]['func']
        args = self.methods[method_selected_name]['args']
        arg_type = self.methods[method_selected_name]['type']

        """ args validation """
        arg_input = []
        for cnt, arg in enumerate(args):
            if self.property_table.item(cnt, 0) is None:
                QMessageBox.warning(self, "错误", f"请输入参数{args[cnt]}")
                return
            try:
                arg_input.append(eval(arg_type[cnt])(self.property_table.item(cnt, 0).text()))
            except Exception as e:
                QMessageBox.warning(self, "错误", f"参数{args[cnt]}格式错误")
                return

        """ random weight validation """
        # execution_time
        try:
            execution_time_random = self.execution_time_random_checkbox.isChecked()
            execution_time_left = int(self.execution_time_left_edit.text())
            if execution_time_random:
                execution_time_right = int(self.execution_time_right_edit.text())
            else:
                execution_time_right = None
        except ValueError:
            QMessageBox.warning(self, '错误', f"执行时间非法")
            return

        # deadline
        try:
            deadline_random = self.deadline_random_checkbox.isChecked()
            deadline_percent = self.deadline_percent_checkbox.isChecked()
            deadline_left = int(self.deadline_left_edit.text())
            if deadline_random:
                deadline_right = int(self.deadline_right_edit.text())
            else:
                deadline_right = None
        except ValueError:
            QMessageBox.warning(self, '错误', f"截止时间非法")
            return

        # start_time
        try:
            start_time_random = self.start_time_random_checkbox.isChecked()
            start_time_left = int(self.start_time_left_edit.text())
            if start_time_random:
                start_time_right = int(self.start_time_right_edit.text())
            else:
                start_time_right = None
        except ValueError:
            QMessageBox.warning(self, '错误', f"开始时间非法")
            return

        """ Generation """
        generation = []
        cnt = 0
        self.process_bar.progressBar.setValue(floor(cnt / num))
        self.process_bar.show()
        filtered_num = 0
        while cnt < num:
            try:
                """ generation """
                dag = method_selected(*arg_input)

                """ random weight """
                execution_time_generate(dag, execution_time_left, execution_time_right, execution_time_random)
                start_time_generate(dag, start_time_left, start_time_right, start_time_random)
                deadline_generate(dag, deadline_left, deadline_right, deadline_random, deadline_percent)
                dag.transform_add_source()
                dag.transform_add_sink()
                for node in dag.nodes:
                    print(dag.nodes[node])

                # Filter
                if not is_eligible(dag, self.conditions):
                    filtered_num += 1
                    continue

                # DAG name
                dag.dag_name = f'dag_{cnt}'

                generation.append(dag)
                cnt += 1
                self.process_bar.progressBar.setValue(floor(cnt / num) * 100)
                QApplication.processEvents()
            except Exception as e:
                QMessageBox.warning(self, "错误", str(e))
                return
        self.process_bar.setVisible(False)
        QMessageBox.information(self, '成功', f'生成成功，过滤了{filtered_num}条DAG')
        self.parent_window.generation_set.update({generation_name: generation})
        self.parent_window.add_generation(generation_name)
        self.setVisible(False)

    def distribution_control(self):
        def process_trigger(q):
            if q.text() == "添加":
                self.distribution_controller_window.show()

            elif q.text() == "删除":
                print('删除')

        self.distribution_controller_edit_menu = QMenu(self)
        self.distribution_controller_edit_menu.addAction(QAction(u'添加', self))
        self.distribution_controller_edit_menu.addAction(QAction(u'删除', self))
        self.distribution_controller_edit_menu.triggered[QAction].connect(process_trigger)
        self.distribution_controller_edit_menu.exec_(QCursor.pos())

    def add_condition(self, condition: Condition):
        self.conditions.append(condition)
        self.update_distribution_controller_list()

    def delete_condition(self, condition: Condition):
        self.conditions.remove(condition)
        self.update_distribution_controller_list()

    def update_distribution_controller_list(self):
        self.property_distribute_list.clear()
        self.property_distribute_list.addItems([str(condition) for condition in self.conditions])

    def method_change(self):
        method_selected_name = self.method_combo.currentText()
        method_selected = self.methods[method_selected_name]['func']
        args = self.methods[method_selected_name]['args']
        self.arg_lst = args
        self.property_table.setRowCount(len(self.arg_lst))
        self.property_table.setVerticalHeaderLabels(self.arg_lst)

    def _set_table(self):
        self.property_table.horizontalHeader().setVisible(False)
        self.property_table.setColumnCount(1)
        self.property_table.setColumnWidth(0, 500)

    def _deadline_percent_checkbox_toggled(self):
        if self.deadline_percent_checkbox.isChecked():
            self.percent_left.setVisible(True)
            if self.deadline_random_checkbox.isChecked():
                self.percent_right.setVisible(True)
        else:
            self.percent_left.setVisible(False)
            self.percent_right.setVisible(False)

    def _execution_time_random_checkbox_toggled(self):
        if self.execution_time_random_checkbox.isChecked():
            self.execution_time_right_edit.setVisible(True)
            self.execution_time_middle_line.setVisible(True)
        else:
            self.execution_time_right_edit.setVisible(False)
            self.execution_time_middle_line.setVisible(False)

    def _deadline_random_checkbox_toggled(self):
        if self.deadline_random_checkbox.isChecked():
            self.deadline_right_edit.setVisible(True)
            self.deadline_middle_line.setVisible(True)
            if self.deadline_percent_checkbox.isChecked():
                self.percent_right.setVisible(True)
        else:
            self.deadline_right_edit.setVisible(False)
            self.deadline_middle_line.setVisible(False)
            if self.deadline_percent_checkbox.isChecked():
                self.percent_right.setVisible(False)

    def _start_time_random_checkbox_toggled(self):
        if self.start_time_random_checkbox.isChecked():
            self.start_time_right_edit.setVisible(True)
            self.start_time_middle_line.setVisible(True)
        else:
            self.start_time_right_edit.setVisible(False)
            self.start_time_middle_line.setVisible(False)


class PeriodicGenerateWindow(QWidget, Ui_periodic_generate):
    def __init__(self, parent_window, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.parent_window = parent_window
        self.method_combo.currentIndexChanged.connect(self.method_change)

        self.cnt = 0

        """ TaskSet """
        # init
        self.task_table.verticalHeader().setVisible(False)
        self.task_table.setContextMenuPolicy(Qt.CustomContextMenu)
        # context menu
        self.task_table.customContextMenuRequested[QtCore.QPoint].connect(self.task_table_edit_show)
        # change validation
        self.current_item_text = None
        self.task_table.cellChanged.connect(self.cell_changed)
        self.task_table.currentItemChanged.connect(self.record_current_item)

        """ Conform """
        self.confirm.clicked.connect(self.generate)

        """ Distribution Controller """
        self.distribution_controller_window = PropertyDistributionControllerWindow(self)
        self.conditions: List[Condition] = []
        self.property_distribute_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.property_distribute_list.customContextMenuRequested[QtCore.QPoint].connect(self.distribution_control)

        """ process bar """
        self.process_bar = ProcessWindow(self)

        """ test """
        self.name_edit.setText('Generation_1')
        self.num_edit.setText('10')

    def task_table_edit_show(self):
        def process_trigger(q):
            if q.text() == "添加":
                row = self.task_table.rowCount()
                self.task_table.setRowCount(row + 1)
                # name
                new_item = QTableWidgetItem(f't{self.cnt}')
                self.task_table.setItem(row, 0, new_item)
                self.cnt += 1
                # priority
                new_item = QTableWidgetItem(f'0')
                self.task_table.setItem(row, 1, new_item)
                # execution time
                new_item = QTableWidgetItem(f'0')
                self.task_table.setItem(row, 2, new_item)
                # deadline
                new_item = QTableWidgetItem(f'inf')
                self.task_table.setItem(row, 3, new_item)
                # period
                new_item = QTableWidgetItem(f'1')
                self.task_table.setItem(row, 4, new_item)

            if q.text() == "删除":
                current_task = self.task_table.currentItem()
                current_task_row = current_task.row()
                current_task_name = self.task_table.item(current_task_row, 0).text()
                self.task_table.removeRow(current_task_row)

        self.task_table_edit_menu = QMenu(self)
        self.task_table_edit_menu.addAction(QAction(u'添加', self))
        if self.task_table.currentItem() is not None:
            self.task_table_edit_menu.addAction(QAction(u'删除', self))
        self.task_table_edit_menu.triggered[QAction].connect(process_trigger)
        self.task_table_edit_menu.exec_(QCursor.pos())

    def record_current_item(self, current, previous):
        if current is None:
            return
        self.current_item_text = current.text()

    def cell_changed(self, row, column):
        print(row, column, self.current_item_text, self.task_table.item(row, column).text())

        # name validation (column 0)
        if column == 0:
            name = self.task_table.item(row, column).text()
            if name in [self.task_table.item(i, 0).text() for i in range(self.task_table.rowCount()) if i != row]:
                QMessageBox.warning(self, '错误', '任务名称重复')
                self.roll_back(row, column)
                return

        # priority (column 1)
        elif column == 1:
            priority = self.task_table.item(row, column).text()
            if not priority.isdigit():
                QMessageBox.warning(self, '错误', '优先级不合法')
                self.roll_back(row, column)
                return
            priority = int(priority)
            if priority < 0:
                QMessageBox.warning(self, '错误', '优先级为负数')
                self.roll_back(row, column)
                return

        # execution time validation (column 2)
        elif column == 2:
            execution_time = self.task_table.item(row, column).text()
            if not execution_time.isdigit():
                QMessageBox.warning(self, '错误', '执行时间不合法')
                self.roll_back(row, column)
                return
            execution_time = int(execution_time)
            if execution_time < 0:
                QMessageBox.warning(self, '错误', '执行时间为负数')
                self.roll_back(row, column)
                return

        # deadline validation (column 3)
        elif column == 3:
            deadline = self.task_table.item(row, column).text()
            if not deadline.isdigit() and deadline != 'inf':
                QMessageBox.warning(self, '错误', '截止时间不合法')
                self.roll_back(row, column)
                return
            if deadline != 'inf':
                deadline = int(deadline)
                if deadline < 0:
                    QMessageBox.warning(self, '错误', '截止时间为负数')
                    self.roll_back(row, column)
                    return

        # period validation (column 4)
        elif column == 4:
            period = self.task_table.item(row, column).text()
            if not period.isdigit():
                QMessageBox.warning(self, '错误', '周期不合法')
                self.roll_back(row, column)
                return
            period = int(period)
            if period < 0:
                QMessageBox.warning(self, '错误', '周期为非正整数')
                self.roll_back(row, column)
                return

        self.update_current_text(row, column)

    def method_change(self):
        print(self.method_combo.currentText())

    def update_current_text(self, row, column):
        self.current_item_text = self.task_table.item(row, column).text()

    def roll_back(self, row, column):
        item = QTableWidgetItem(self.current_item_text)
        self.task_table.setItem(row, column, item)

    def generate(self):
        """ press confirm button to generate """
        """ basic information validation """
        if not self.name_edit.text():
            QMessageBox.warning(self, '错误', '名称不能为空')
            return
        if self.name_edit.text() in self.parent_window.generation_set.keys():
            QMessageBox.warning(self, '错误', '生成结果重名')
            return
        if not self.num_edit.text().isdigit():
            QMessageBox.warning(self, '错误', '生成数量非法')
            return

        """ fetch information """
        generation_name = self.name_edit.text()
        num = int(self.num_edit.text())
        method_selected_name = self.method_combo.currentText()

        """ task validation and generation """
        ts = []
        for row in range(self.task_table.rowCount()):
            """ fetch args """
            name = self.task_table.item(row, 0).text()
            priority = int(self.task_table.item(row, 1).text())
            execution_time = int(self.task_table.item(row, 2).text())
            if self.task_table.item(row, 3).text() == 'inf':
                deadline = float('inf')
            else:
                deadline = int(self.task_table.item(row, 3).text())
            period = int(self.task_table.item(row, 4).text())

            """ task validation """
            if execution_time > deadline:
                QMessageBox.warning(self, '配置错误', f"{name}的执行时间大于相对截止时间")
                return
            """ task generation """
            ts.append(Task(name, execution_time, execution_time, period, deadline))
        """ taskset generation """
        ts = TaskSet(ts)

        """ DAG Generation """
        g = Generator(ts)
        generation = []
        cnt = 0
        filtered_num = 0
        self.process_bar.progressBar.setValue(0)
        self.process_bar.show()
        self.process_bar.filtered_num_edit.setText(str(filtered_num))
        while cnt < num:
            self.process_bar.progressBar.setValue(floor(cnt / num * 100))
            self.process_bar.filtered_num_edit.setText(str(filtered_num))
            self.process_bar.show()
            if self.process_bar.end_flag:
                break
            QApplication.processEvents()
            try:
                dag = g.generate().__next__().formal_dag
                # DAG name
                dag.dag_name = f'dag_{cnt}'

                # Filter
                if not is_eligible(dag, self.conditions):
                    filtered_num += 1
                    continue

                generation.append(dag)
                cnt += 1
                self.process_bar.progressBar.setValue(floor(cnt / num))
            except StopIteration:
                QMessageBox.information(self, '提示', f'根据配置仅能生成{cnt}个DAG')
                break
        self.process_bar.setVisible(False)
        if self.process_bar.end_flag:
            QMessageBox.information(self, '结束', f'提前结束，生成了{cnt}个DAG，过滤了{filtered_num}个DAG')
            self.process_bar.end_flag = False
        else:
            QMessageBox.information(self, '成功', f'生成成功，生成了{cnt}个DAG，过滤了{filtered_num}个DAG')
        self.parent_window.generation_set.update({generation_name: generation})
        self.parent_window.add_generation(generation_name)
        self.setVisible(False)

    def distribution_control(self):
        def process_trigger(q):
            if q.text() == "添加":
                self.distribution_controller_window.show()

            elif q.text() == "删除":
                print('删除')

        self.distribution_controller_edit_menu = QMenu(self)
        self.distribution_controller_edit_menu.addAction(QAction(u'添加', self))
        self.distribution_controller_edit_menu.addAction(QAction(u'删除', self))
        self.distribution_controller_edit_menu.triggered[QAction].connect(process_trigger)
        self.distribution_controller_edit_menu.exec_(QCursor.pos())

    def add_condition(self, condition: Condition):
        self.conditions.append(condition)
        self.update_distribution_controller_list()

    def delete_condition(self, condition: Condition):
        self.conditions.remove(condition)
        self.update_distribution_controller_list()

    def update_distribution_controller_list(self):
        self.property_distribute_list.clear()
        self.property_distribute_list.addItems([str(condition) for condition in self.conditions])


class PropertyDistributionControllerWindow(QWidget, Ui_property_distribution_controller):
    def __init__(self, parent_window: AperiodicGenerateWindow, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.parent_window = parent_window
        self.add_btn.clicked.connect(self.add)
        self.cancel_btn.clicked.connect(self.cancel)
        self.init_property_list()
        self.property_list.currentItemChanged.connect(self.current_item_changed)

    def init_property_list(self):
        self.property_list.addItems([
            '长度',
            '宽度',
            '最大入度',
            '最小入度',
            '平均入度',
            '最大出度',
            '最小出度',
            '平均出度',
        ])

    def current_item_changed(self):
        current_item = self.property_list.currentItem()
        self.property_edit.setText(current_item.text())

    def add(self):
        # Validation
        if not self.value_edit:
            QMessageBox.warning(self, '错误', '值不能为空')
            return
        if not self.value_edit.text().isdigit():
            QMessageBox.warning(self, '错误', '值为非数字')
            return

        # fetch args
        property_name = self.property_edit.text()
        operator = self.operator_combo.currentText()
        value = float(self.value_edit.text())

        # add control
        condition = Condition(property_name, operator, value)
        if condition in self.parent_window.conditions:
            QMessageBox(self, '条件重复', '已有此条件')
        for exist_condition in self.parent_window.conditions:
            if exist_condition.property == condition.property:
                self.parent_window.delete_condition(exist_condition)
                break
        self.parent_window.add_condition(condition)

    def cancel(self):
        self.setVisible(False)


class RunWindow(QWidget, Ui_run_window):
    def __init__(self, parent_window: GeneratorMainWindow, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.parent_window = parent_window
        self.confirm.clicked.connect(self.run)
        self.new_scheduler_button.toggled.connect(lambda: self.bnt_toggled(self.new_scheduler_button))
        self.existing_scheduler_button.toggled.connect(lambda: self.bnt_toggled(self.existing_scheduler_button))
        self.new_scheduler_button.setChecked(True)

        """ test """
        self.priority_assignment_combo.setCurrentIndex(3)

    def bnt_toggled(self, btn):
        if btn == self.new_scheduler_button:
            self.existing_scheduler_combo.setEnabled(False)
            self.new_scheduler_edit.setEnabled(True)
            self.processor_num_edit.setEnabled(True)
            self.processor_mode_combo.setEnabled(True)
            self.preempt_mode_combo.setEnabled(True)
            self.preempt_rate.setEnabled(True)
            self.priority_assignment_combo.setEnabled(True)
        elif btn == self.existing_scheduler_button:
            self.existing_scheduler_combo.setEnabled(True)
            self.new_scheduler_edit.setEnabled(False)
            self.processor_num_edit.setEnabled(False)
            self.processor_mode_combo.setEnabled(False)
            self.preempt_mode_combo.setEnabled(False)
            self.preempt_rate.setEnabled(False)
            self.priority_assignment_combo.setEnabled(False)
            # TODO: Existing Scheduler

    def run(self):
        if self.existing_scheduler_button.isChecked():
            print('现有调度集')
        elif self.new_scheduler_button.isChecked():
            # validation
            try:
                processor_num = int(self.processor_num_edit.text())
            except ValueError:
                QMessageBox.warning(self, '错误', '处理器数量为整数')
                return
            if processor_num <= 0:
                QMessageBox.warning(self, '错误', '处理器数量<1')
                return
            try:
                preempt_rate = int(self.preempt_rate.text())
            except ValueError:
                QMessageBox.warning(self, '错误', '抢占周期为整数')
                return
            if preempt_rate <= 0:
                QMessageBox.warning(self, '错误', '抢占周期<1')
                return
            if self.new_scheduler_edit.text() in [scheduler_set.name for scheduler_set in
                                                  self.parent_window.main.scheduler.scheduler_sets]:
                QMessageBox.warning(self, '错误', '调度集重名')
                return
            try:
                preempt_clock = int(self.preempt_rate.text())
            except ValueError:
                QMessageBox.warning(self, '错误', '抢占周期为正整数')
                return
            if preempt_clock <= 0:
                QMessageBox.warning(self, '错误', '抢占周期为正整数')
                return

            print(f'调度集名称:{self.new_scheduler_edit.text()}\n'
                  f'处理器数量:{processor_num}\n'
                  f'处理器模式:{self.processor_mode_combo.currentText()}\n'
                  f'抢占模式:{self.preempt_mode_combo.currentText()}\n'
                  f'抢占周期:{preempt_rate}\n'
                  f'优先级分配算法:{self.priority_assignment_combo.currentText()}\n')

            # 生成调度集
            ss = SchedulerSet(dags=self.parent_window.current_generation,
                              processor_num=processor_num,
                              processor_type=self.preempt_mode_combo.currentText(),
                              name=self.new_scheduler_edit.text(),
                              priority_assignment=self.priority_assignment_combo.currentText(),
                              preempt_clock=self.preempt_rate.text(),
                              processor_mode=self.processor_mode_combo.currentText()
                              )

            self.parent_window.main.scheduler.add_scheduler_set(ss)
            self.parent_window.main.scheduler.show()
            self.setVisible(False)


class ConfigurationWindow(QWidget, Ui_property_selection):
    def __init__(self, parent_window: GeneratorMainWindow, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.parent_window = parent_window
        self.add_btn.clicked.connect(self.add)
        self.remove_btn.clicked.connect(self.remove)
        self.confirm_btn.clicked.connect(self.confirm)
        self.set_property_list()
        self.selected_property = []

    def add(self):
        item = self.property_list.currentItem()
        if item is None:
            QMessageBox.warning(self, '错误', '请选择一个静态属性')
            return
        if item.text() in self.selected_property:
            QMessageBox.information(self, '重复添加', '该静态属性已添加')
            return
        self.selected_property.append(item.text())
        self.selected_property_list.addItem(item.text())

    def remove(self):
        item = self.selected_property_list.currentItem()
        if item is None:
            QMessageBox.warning(self, '错误', '请选择需要移出的静态属性')
            return

        self.selected_property.remove(item.text())
        self.selected_property_list.clear()
        self.selected_property_list.addItems(self.selected_property)

    def confirm(self):
        # 更新表格或树
        print('确定')
        self.parent_window._update()
        self.setVisible(False)

    def set_property_list(self):
        self.property_list.addItems([
            '长度',
            '路径',
            '最长路径',
            '宽度',
            '反链',
            '最长反链',
            '最大入度',
            '最小入度',
            '平均入度',
            '最大出度',
            '最小出度',
            '平均出度',
        ])

    def set_selected_property_list(self):
        pass


class ProcessWindow(QWidget, Ui_process):
    def __init__(self, parent_window: GeneratorMainWindow, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.parent_window = parent_window
        self.end_flag = False
        self.end_btn.clicked.connect(self.end)

    def end(self):
        self.end_flag = True
