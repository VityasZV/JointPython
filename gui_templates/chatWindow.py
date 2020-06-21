import gettext

from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        self.el = gettext.translation('base', localedir='locales', languages=['ua'])
        self.el.install()
        _ = self.el.gettext
        self.lngs = ['en', 'ua']
        self.it = 0
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(549, 563)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.verticalLayout_3 = QtWidgets.QVBoxLayout(self.centralwidget)
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout()
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.textBrowser = QtWidgets.QTextBrowser(self.centralwidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.textBrowser.sizePolicy().hasHeightForWidth())
        self.textBrowser.setSizePolicy(sizePolicy)
        self.textBrowser.setMinimumSize(QtCore.QSize(256, 0))
        self.textBrowser.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.textBrowser.setObjectName("textBrowser")
        self.horizontalLayout.addWidget(self.textBrowser)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        self.verticalLayout_2.addLayout(self.horizontalLayout)
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.plainTextEdit = QtWidgets.QPlainTextEdit(self.centralwidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.plainTextEdit.sizePolicy().hasHeightForWidth())
        self.plainTextEdit.setSizePolicy(sizePolicy)
        self.plainTextEdit.setMinimumSize(QtCore.QSize(0, 71))
        self.plainTextEdit.setMaximumSize(QtCore.QSize(16777215, 71))
        self.plainTextEdit.setAcceptDrops(False)
        self.plainTextEdit.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.plainTextEdit.setObjectName("plainTextEdit")
        self.horizontalLayout_2.addWidget(self.plainTextEdit)
        self.verticalLayout_2.addLayout(self.horizontalLayout_2)
        self.verticalLayout_3.addLayout(self.verticalLayout_2)
        self.horizontalLayout_3 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_3.setSizeConstraint(QtWidgets.QLayout.SetFixedSize)
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.pushButton_2 = QtWidgets.QPushButton(self.centralwidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.pushButton_2.sizePolicy().hasHeightForWidth())
        self.pushButton_2.setSizePolicy(sizePolicy)
        self.pushButton_2.setMinimumSize(QtCore.QSize(200, 0))
        self.pushButton_2.setMaximumSize(QtCore.QSize(200, 16777215))
        self.pushButton_2.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.pushButton_2.setObjectName("pushButton_2")
        self.horizontalLayout_3.addWidget(self.pushButton_2)
        self.horizontalLayout_4 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_4.setSizeConstraint(QtWidgets.QLayout.SetFixedSize)
        self.horizontalLayout_4.setObjectName("horizontalLayout_4")
        self.pushButton_4 = QtWidgets.QPushButton(self.centralwidget)
        self.horizontalLayout_4.addWidget(self.pushButton_4)
        self.pushButton_4.setText(_("EN|UA"))
        self.pushButton_4.clicked.connect(lambda: self.trsl(MainWindow))
        self.pushButton = QtWidgets.QPushButton(self.centralwidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.pushButton.sizePolicy().hasHeightForWidth())
        self.pushButton.setSizePolicy(sizePolicy)
        self.pushButton.setMinimumSize(QtCore.QSize(200, 0))
        self.pushButton.setMaximumSize(QtCore.QSize(200, 16777215))
        self.pushButton.setCursor(QtGui.QCursor(QtCore.Qt.ArrowCursor))
        self.pushButton.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.pushButton.setObjectName("pushButton")
        self.horizontalLayout_3.addWidget(self.pushButton)
        self.verticalLayout_3.addLayout(self.horizontalLayout_3)
        self.pushButton_3 = QtWidgets.QPushButton(self.centralwidget)
        self.pushButton_3.setObjectName("pushbutton_3")
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.pushButton_3.sizePolicy().hasHeightForWidth())
        self.pushButton_3.setSizePolicy(sizePolicy)
        self.pushButton_3.setMinimumSize(QtCore.QSize(200, 0))
        self.pushButton_3.setMaximumSize(QtCore.QSize(200, 16777215))
        self.pushButton_3.setCursor(QtGui.QCursor(QtCore.Qt.ArrowCursor))
        self.pushButton_3.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.horizontalLayout_3.addWidget(self.pushButton_3)
        MainWindow.setCentralWidget(self.centralwidget)

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
        MainWindow.setWindowTitle(_translate("MainWindow", _("Chat")))
        self.pushButton_2.setText(_translate("MainWindow", _("Log Out")))
        self.pushButton.setText(_translate("MainWindow", _("Send")))
        self.pushButton_3.setText(_translate("MainWindow", _("Choose room")))
