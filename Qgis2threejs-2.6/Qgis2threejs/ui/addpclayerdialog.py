# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'D:\Documents\minorua\QGIS\plugins\Qgis2threejs\ui\addpclayerdialog.ui'
#
# Created by: PyQt5 UI code generator 5.14.1
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_AddPointCloudLayerDialog(object):
    def setupUi(self, AddPointCloudLayerDialog):
        AddPointCloudLayerDialog.setObjectName("AddPointCloudLayerDialog")
        AddPointCloudLayerDialog.resize(497, 104)
        self.verticalLayout = QtWidgets.QVBoxLayout(AddPointCloudLayerDialog)
        self.verticalLayout.setObjectName("verticalLayout")
        self.groupBox = QtWidgets.QGroupBox(AddPointCloudLayerDialog)
        self.groupBox.setObjectName("groupBox")
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout(self.groupBox)
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.label = QtWidgets.QLabel(self.groupBox)
        self.label.setObjectName("label")
        self.horizontalLayout_2.addWidget(self.label)
        self.lineEdit_Source = QtWidgets.QLineEdit(self.groupBox)
        self.lineEdit_Source.setObjectName("lineEdit_Source")
        self.horizontalLayout_2.addWidget(self.lineEdit_Source)
        self.pushButton_Browse = QtWidgets.QPushButton(self.groupBox)
        self.pushButton_Browse.setObjectName("pushButton_Browse")
        self.horizontalLayout_2.addWidget(self.pushButton_Browse)
        self.verticalLayout.addWidget(self.groupBox)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.pushButton_Add = QtWidgets.QPushButton(AddPointCloudLayerDialog)
        self.pushButton_Add.setDefault(True)
        self.pushButton_Add.setObjectName("pushButton_Add")
        self.horizontalLayout.addWidget(self.pushButton_Add)
        self.pushButton_Cancel = QtWidgets.QPushButton(AddPointCloudLayerDialog)
        self.pushButton_Cancel.setObjectName("pushButton_Cancel")
        self.horizontalLayout.addWidget(self.pushButton_Cancel)
        self.verticalLayout.addLayout(self.horizontalLayout)

        self.retranslateUi(AddPointCloudLayerDialog)
        self.pushButton_Add.clicked.connect(AddPointCloudLayerDialog.accept)
        self.pushButton_Cancel.clicked.connect(AddPointCloudLayerDialog.close)
        QtCore.QMetaObject.connectSlotsByName(AddPointCloudLayerDialog)

    def retranslateUi(self, AddPointCloudLayerDialog):
        _translate = QtCore.QCoreApplication.translate
        AddPointCloudLayerDialog.setWindowTitle(_translate("AddPointCloudLayerDialog", "Add Point Cloud Layer"))
        self.groupBox.setTitle(_translate("AddPointCloudLayerDialog", "Source"))
        self.label.setText(_translate("AddPointCloudLayerDialog", "Potree supported file URL"))
        self.lineEdit_Source.setPlaceholderText(_translate("AddPointCloudLayerDialog", "http(s)://... or file://..."))
        self.pushButton_Browse.setText(_translate("AddPointCloudLayerDialog", "Browse..."))
        self.pushButton_Add.setText(_translate("AddPointCloudLayerDialog", "Add"))
        self.pushButton_Cancel.setText(_translate("AddPointCloudLayerDialog", "Cancel"))
