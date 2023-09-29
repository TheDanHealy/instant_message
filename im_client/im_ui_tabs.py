# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'im_client_tabs.ui'
#
# Created by: PyQt5 UI code generator 5.15.0
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(721, 585)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.gridLayout = QtWidgets.QGridLayout(self.centralwidget)
        self.gridLayout.setObjectName("gridLayout")
        self.chatTabWidget = QtWidgets.QTabWidget(self.centralwidget)
        self.chatTabWidget.setObjectName("chatTabWidget")
        self.gridLayout.addWidget(self.chatTabWidget, 6, 0, 1, 1)
        self.connectedUserListWidget = QtWidgets.QListWidget(self.centralwidget)
        self.connectedUserListWidget.setMaximumSize(QtCore.QSize(140, 16777215))
        self.connectedUserListWidget.setObjectName("connectedUserListWidget")
        self.gridLayout.addWidget(self.connectedUserListWidget, 6, 1, 1, 1, QtCore.Qt.AlignRight)
        self.gridLayout_current = QtWidgets.QGridLayout()
        self.gridLayout_current.setObjectName("gridLayout_current")
        self.label_user = QtWidgets.QLabel(self.centralwidget)
        self.label_user.setObjectName("label_user")
        self.gridLayout_current.addWidget(self.label_user, 1, 0, 1, 1, QtCore.Qt.AlignLeft)
        self.label_curr = QtWidgets.QLabel(self.centralwidget)
        self.label_curr.setMaximumSize(QtCore.QSize(100, 16777215))
        self.label_curr.setObjectName("label_curr")
        self.gridLayout_current.addWidget(self.label_curr, 2, 0, 1, 1)
        self.me_label = QtWidgets.QLabel(self.centralwidget)
        self.me_label.setObjectName("me_label")
        self.gridLayout_current.addWidget(self.me_label, 1, 1, 1, 1)
        self.status_label = QtWidgets.QLabel(self.centralwidget)
        self.status_label.setObjectName("status_label")
        self.gridLayout_current.addWidget(self.status_label, 2, 1, 1, 1)
        self.gridLayout.addLayout(self.gridLayout_current, 5, 0, 1, 1)
        self.gridLayout_server = QtWidgets.QGridLayout()
        self.gridLayout_server.setObjectName("gridLayout_server")
        self.server_status_label = QtWidgets.QLabel(self.centralwidget)
        self.server_status_label.setObjectName("server_status_label")
        self.gridLayout_server.addWidget(self.server_status_label, 1, 0, 1, 1)
        self.label = QtWidgets.QLabel(self.centralwidget)
        self.label.setObjectName("label")
        self.gridLayout_server.addWidget(self.label, 2, 0, 1, 1)
        self.gridLayout.addLayout(self.gridLayout_server, 5, 1, 1, 1)
        MainWindow.setCentralWidget(self.centralwidget)

        self.retranslateUi(MainWindow)
        self.chatTabWidget.setCurrentIndex(-1)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "Chat"))
        self.label_user.setText(_translate("MainWindow", "Current User:"))
        self.label_curr.setText(_translate("MainWindow", "Current Chat:"))
        self.me_label.setText(_translate("MainWindow", "me"))
        self.status_label.setText(_translate("MainWindow", "none, find someone to talk to"))
        self.server_status_label.setText(_translate("MainWindow", "TextLabel"))
        self.label.setText(_translate("MainWindow", "Connected Users"))


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    MainWindow.show()
    sys.exit(app.exec_())
