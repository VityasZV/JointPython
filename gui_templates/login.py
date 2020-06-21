import gettext
from PyQt5 import QtCore, QtGui, QtWidgets
import sys

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(513, 397)
        self.el = gettext.translation('base', localedir='locales', languages=['ua'])
        self.el.install()
        _ = self.el.gettext
        self.lngs = ['en', 'ua']
        self.it = 0
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.verticalLayout_3 = QtWidgets.QVBoxLayout(self.centralwidget)
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.verticalLayout.setObjectName("verttransfericalLayout")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout()
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.label = QtWidgets.QLabel(self.centralwidget)
        self.label.setObjectName("label")
        self.verticalLayout_2.addWidget(self.label)
        self.lineEdit = QtWidgets.QLineEdit(self.centralwidget)
        self.lineEdit.setMouseTracking(False)
        self.lineEdit.setObjectName("lineEdit")
        self.verticalLayout_2.addWidget(self.lineEdit)
        self.label_2 = QtWidgets.QLabel(self.centralwidget)
        self.label_2.setObjectName("label_2")
        self.verticalLayout_2.addWidget(self.label_2)
        self.lineEdit_2 = QtWidgets.QLineEdit(self.centralwidget)
        self.lineEdit_2.setObjectName("lineEdit_2")
        self.verticalLayout_2.addWidget(self.lineEdit_2)
        self.pushButton = QtWidgets.QPushButton(self.centralwidget)
        self.pushButton.setObjectName("pushButton")
        self.verticalLayout_2.addWidget(self.pushButton)
        self.label_3 = QtWidgets.QLabel(self.centralwidget)
        self.label_3.setObjectName("label_3")
        self.verticalLayout_2.addWidget(self.label_3)
        self.pushButton_2 = QtWidgets.QPushButton(self.centralwidget)
        self.pushButton_2.setObjectName("pushButton_2")
        self.verticalLayout_2.addWidget(self.pushButton_2)
        self.verticalLayout.addLayout(self.verticalLayout_2)
        self.verticalLayout_3.addLayout(self.verticalLayout)
        self.pushButton_3 = QtWidgets.QPushButton(self.centralwidget)
        self.verticalLayout_2.addWidget(self.pushButton_3)
        self.pushButton_3.setObjectName("pushButton_3")
        MainWindow.setCentralWidget(self.centralwidget)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)
        self.pushButton_4 = QtWidgets.QPushButton(self.centralwidget)
        self.verticalLayout_2.addWidget(self.pushButton_4)
        self.pushButton_4.setText(_("EN|UA"))
        self.pushButton_4.clicked.connect(lambda: self.trsl(MainWindow))
        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def trsl(self, MainWindow):
        self.it = (self.it + 1) % 2
        self.el = gettext.translation('base', localedir='locales', languages=[self.lngs[self.it]])
        self.el.install()
        self.retranslateUi(MainWindow)

    def retranslateUi(self, MainWindow):
        _ = self.el.gettext
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", _("Login"), None))
        self.label.setText(_translate("MainWindow", _("Login")))
        self.label_2.setText(_translate("MainWindow", _("Password")))
        self.pushButton.setText(_translate("MainWindow", _("Sign In")))
        self.label_3.setText(_translate("MainWindow", _("Do not have an account yet?")))
        self.pushButton_2.setText(_translate("MainWindow", _("Sign Up")))
        self.pushButton_3.setText(_translate("MainWindow", _("Exit")))

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    ex = Ui_MainWindow()
    sys.exit(app.exec_())
