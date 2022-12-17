# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'process_bar.ui'
#
# Created by: PyQt5 UI code generator 5.15.4
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_process(object):
    def setupUi(self, process):
        process.setObjectName("process")
        process.setWindowModality(QtCore.Qt.ApplicationModal)
        process.resize(248, 87)
        self.verticalLayout = QtWidgets.QVBoxLayout(process)
        self.verticalLayout.setObjectName("verticalLayout")
        self.progressBar = QtWidgets.QProgressBar(process)
        self.progressBar.setProperty("value", 24)
        self.progressBar.setObjectName("progressBar")
        self.verticalLayout.addWidget(self.progressBar)
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.label = QtWidgets.QLabel(process)
        self.label.setObjectName("label")
        self.horizontalLayout_2.addWidget(self.label)
        self.filtered_num_edit = QtWidgets.QLineEdit(process)
        self.filtered_num_edit.setEnabled(False)
        self.filtered_num_edit.setObjectName("filtered_num_edit")
        self.horizontalLayout_2.addWidget(self.filtered_num_edit)
        self.verticalLayout.addLayout(self.horizontalLayout_2)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.end_btn = QtWidgets.QPushButton(process)
        self.end_btn.setObjectName("end_btn")
        self.horizontalLayout.addWidget(self.end_btn)
        spacerItem1 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem1)
        self.verticalLayout.addLayout(self.horizontalLayout)

        self.retranslateUi(process)
        QtCore.QMetaObject.connectSlotsByName(process)

    def retranslateUi(self, process):
        _translate = QtCore.QCoreApplication.translate
        process.setWindowTitle(_translate("process", "进度条"))
        self.label.setText(_translate("process", "过滤数量"))
        self.end_btn.setText(_translate("process", "结束"))
