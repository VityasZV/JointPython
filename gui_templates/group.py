import sys
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

class ExampleWidget(QGroupBox):
    def __init__(self, numAddWidget,x):
        QGroupBox.__init__(self)
        self.name = x
        self.numAddWidget = numAddWidget
        self.numAddItem   = 1
        self.initSubject()
        self.organize()

    def initSubject(self):
        self.lblName = QPushButton(self.name, self)


    def organize(self):
        grid = QGridLayout(self)
        self.setLayout(grid)
        grid.addWidget(self.lblName,        0, 0, 0, 0)



class MyApp(QWidget):
    def __init__(self):
        super().__init__()
        self.numAddWidget = 1
        self.initUi()

    def initUi(self):
        self.layoutV = QVBoxLayout(self)

        self.area = QScrollArea(self)
        self.area.setWidgetResizable(True)
        self.scrollAreaWidgetContents = QWidget()
        self.scrollAreaWidgetContents.setGeometry(0, 0, 200, 100)

        self.layoutH = QHBoxLayout(self.scrollAreaWidgetContents)
        self.gridLayout = QGridLayout()
        self.layoutH.addLayout(self.gridLayout)

        self.area.setWidget(self.scrollAreaWidgetContents)
        self.layoutV.addWidget(self.area)
        self.setGeometry(700, 200, 350, 300)

    def addWidget(self,x):
        self.numAddWidget += 1
        self.widget = ExampleWidget(self.numAddWidget,x)
        self.gridLayout.addWidget(self.widget)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = MyApp()
    w.show()
    sys.exit(app.exec_())
