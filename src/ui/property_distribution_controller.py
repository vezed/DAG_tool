# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'property_distribution_controller.ui'
#
# Created by: PyQt5 UI code generator 5.15.4
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_property_distribution_controller(object):
    def setupUi(self, property_distribution_controller):
        property_distribution_controller.setObjectName("property_distribution_controller")
        property_distribution_controller.setWindowModality(QtCore.Qt.ApplicationModal)
        property_distribution_controller.resize(522, 300)
        self.horizontalLayout_3 = QtWidgets.QHBoxLayout(property_distribution_controller)
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.verticalLayout_5 = QtWidgets.QVBoxLayout()
        self.verticalLayout_5.setObjectName("verticalLayout_5")
        self.label = QtWidgets.QLabel(property_distribution_controller)
        self.label.setObjectName("label")
        self.verticalLayout_5.addWidget(self.label)
        self.property_list = QtWidgets.QListWidget(property_distribution_controller)
        self.property_list.setObjectName("property_list")
        self.verticalLayout_5.addWidget(self.property_list)
        self.horizontalLayout_3.addLayout(self.verticalLayout_5)
        self.verticalLayout_4 = QtWidgets.QVBoxLayout()
        self.verticalLayout_4.setObjectName("verticalLayout_4")
        spacerItem = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout_4.addItem(spacerItem)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.verticalLayout.setObjectName("verticalLayout")
        self.label_2 = QtWidgets.QLabel(property_distribution_controller)
        self.label_2.setObjectName("label_2")
        self.verticalLayout.addWidget(self.label_2)
        self.property_edit = QtWidgets.QLineEdit(property_distribution_controller)
        self.property_edit.setEnabled(False)
        self.property_edit.setObjectName("property_edit")
        self.verticalLayout.addWidget(self.property_edit)
        self.horizontalLayout.addLayout(self.verticalLayout)
        self.verticalLayout_2 = QtWidgets.QVBoxLayout()
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.label_3 = QtWidgets.QLabel(property_distribution_controller)
        self.label_3.setObjectName("label_3")
        self.verticalLayout_2.addWidget(self.label_3)
        self.operator_combo = QtWidgets.QComboBox(property_distribution_controller)
        self.operator_combo.setObjectName("operator_combo")
        self.operator_combo.addItem("")
        self.operator_combo.addItem("")
        self.operator_combo.addItem("")
        self.operator_combo.addItem("")
        self.operator_combo.addItem("")
        self.verticalLayout_2.addWidget(self.operator_combo)
        self.horizontalLayout.addLayout(self.verticalLayout_2)
        self.verticalLayout_3 = QtWidgets.QVBoxLayout()
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.label_4 = QtWidgets.QLabel(property_distribution_controller)
        self.label_4.setObjectName("label_4")
        self.verticalLayout_3.addWidget(self.label_4)
        self.value_edit = QtWidgets.QLineEdit(property_distribution_controller)
        self.value_edit.setObjectName("value_edit")
        self.verticalLayout_3.addWidget(self.value_edit)
        self.horizontalLayout.addLayout(self.verticalLayout_3)
        self.verticalLayout_4.addLayout(self.horizontalLayout)
        spacerItem1 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout_4.addItem(spacerItem1)
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        spacerItem2 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem2)
        self.add_btn = QtWidgets.QPushButton(property_distribution_controller)
        self.add_btn.setObjectName("add_btn")
        self.horizontalLayout_2.addWidget(self.add_btn)
        spacerItem3 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem3)
        self.cancel_btn = QtWidgets.QPushButton(property_distribution_controller)
        self.cancel_btn.setObjectName("cancel_btn")
        self.horizontalLayout_2.addWidget(self.cancel_btn)
        spacerItem4 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem4)
        self.verticalLayout_4.addLayout(self.horizontalLayout_2)
        spacerItem5 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout_4.addItem(spacerItem5)
        self.horizontalLayout_3.addLayout(self.verticalLayout_4)

        self.retranslateUi(property_distribution_controller)
        QtCore.QMetaObject.connectSlotsByName(property_distribution_controller)

    def retranslateUi(self, property_distribution_controller):
        _translate = QtCore.QCoreApplication.translate
        property_distribution_controller.setWindowTitle(_translate("property_distribution_controller", "属性分布限制"))
        self.label.setText(_translate("property_distribution_controller", "属性列表"))
        self.label_2.setText(_translate("property_distribution_controller", "属性"))
        self.label_3.setText(_translate("property_distribution_controller", "关系"))
        self.operator_combo.setItemText(0, _translate("property_distribution_controller", "＞"))
        self.operator_combo.setItemText(1, _translate("property_distribution_controller", "≥"))
        self.operator_combo.setItemText(2, _translate("property_distribution_controller", "＝"))
        self.operator_combo.setItemText(3, _translate("property_distribution_controller", "≤"))
        self.operator_combo.setItemText(4, _translate("property_distribution_controller", "＜"))
        self.label_4.setText(_translate("property_distribution_controller", "值"))
        self.add_btn.setText(_translate("property_distribution_controller", "添加"))
        self.cancel_btn.setText(_translate("property_distribution_controller", "退出"))