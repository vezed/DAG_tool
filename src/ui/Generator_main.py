# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'Generator_main.ui'
#
# Created by: PyQt5 UI code generator 5.15.4
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_Generator_main(object):
    def setupUi(self, Generator_main):
        Generator_main.setObjectName("Generator_main")
        Generator_main.resize(1620, 771)
        self.centralwidget = QtWidgets.QWidget(Generator_main)
        self.centralwidget.setObjectName("centralwidget")
        self.scrollArea = QtWidgets.QScrollArea(self.centralwidget)
        self.scrollArea.setGeometry(QtCore.QRect(300, 10, 1311, 701))
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setObjectName("scrollArea")
        self.scrollAreaWidgetContents = QtWidgets.QWidget()
        self.scrollAreaWidgetContents.setGeometry(QtCore.QRect(0, 0, 1309, 699))
        self.scrollAreaWidgetContents.setObjectName("scrollAreaWidgetContents")
        self.scrollArea.setWidget(self.scrollAreaWidgetContents)
        self.groupBox = QtWidgets.QGroupBox(self.centralwidget)
        self.groupBox.setGeometry(QtCore.QRect(10, 10, 276, 701))
        self.groupBox.setObjectName("groupBox")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.groupBox)
        self.verticalLayout.setObjectName("verticalLayout")
        self.generate_result = QtWidgets.QListWidget(self.groupBox)
        self.generate_result.setObjectName("generate_result")
        self.verticalLayout.addWidget(self.generate_result)
        Generator_main.setCentralWidget(self.centralwidget)
        self.statusbar = QtWidgets.QStatusBar(Generator_main)
        self.statusbar.setObjectName("statusbar")
        Generator_main.setStatusBar(self.statusbar)
        self.menubar = QtWidgets.QMenuBar(Generator_main)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 1620, 26))
        self.menubar.setObjectName("menubar")
        self.generate_button = QtWidgets.QMenu(self.menubar)
        self.generate_button.setObjectName("generate_button")
        self.view_button = QtWidgets.QMenu(self.menubar)
        self.view_button.setObjectName("view_button")
        self.property_ana = QtWidgets.QMenu(self.menubar)
        self.property_ana.setObjectName("property_ana")
        Generator_main.setMenuBar(self.menubar)
        self.actiontable = QtWidgets.QAction(Generator_main)
        self.actiontable.setObjectName("actiontable")
        self.actionperiodic = QtWidgets.QAction(Generator_main)
        self.actionperiodic.setObjectName("actionperiodic")
        self.actionaperiodic = QtWidgets.QAction(Generator_main)
        self.actionaperiodic.setObjectName("actionaperiodic")
        self.actiongraphview = QtWidgets.QAction(Generator_main)
        self.actiongraphview.setObjectName("actiongraphview")
        self.actiontableview = QtWidgets.QAction(Generator_main)
        self.actiontableview.setObjectName("actiontableview")
        self.actiontreeview = QtWidgets.QAction(Generator_main)
        self.actiontreeview.setObjectName("actiontreeview")
        self.actionconfiguration = QtWidgets.QAction(Generator_main)
        self.actionconfiguration.setObjectName("actionconfiguration")
        self.generate_button.addAction(self.actionperiodic)
        self.generate_button.addAction(self.actionaperiodic)
        self.view_button.addAction(self.actiongraphview)
        self.view_button.addAction(self.actiontableview)
        self.property_ana.addAction(self.actionconfiguration)
        self.menubar.addAction(self.generate_button.menuAction())
        self.menubar.addAction(self.view_button.menuAction())
        self.menubar.addAction(self.property_ana.menuAction())

        self.retranslateUi(Generator_main)
        QtCore.QMetaObject.connectSlotsByName(Generator_main)

    def retranslateUi(self, Generator_main):
        _translate = QtCore.QCoreApplication.translate
        Generator_main.setWindowTitle(_translate("Generator_main", "?????????"))
        self.groupBox.setTitle(_translate("Generator_main", "????????????"))
        self.generate_button.setTitle(_translate("Generator_main", "??????"))
        self.view_button.setTitle(_translate("Generator_main", "??????"))
        self.property_ana.setTitle(_translate("Generator_main", "??????????????????"))
        self.actiontable.setText(_translate("Generator_main", "table"))
        self.actionperiodic.setText(_translate("Generator_main", "???????????????"))
        self.actionaperiodic.setText(_translate("Generator_main", "??????????????????"))
        self.actiongraphview.setText(_translate("Generator_main", "??????"))
        self.actiontableview.setText(_translate("Generator_main", "??????"))
        self.actiontreeview.setText(_translate("Generator_main", "???"))
        self.actionconfiguration.setText(_translate("Generator_main", "??????"))
