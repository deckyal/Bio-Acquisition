import sys
from PyQt4 import QtCore, QtGui


class Widget(QtGui.QWidget):
    def __init__(self):
        super(Widget, self).__init__()

        # Uncomment if you want to change the language
        # self.setLocale(QtCore.QLocale(QtCore.QLocale.Spanish, QtCore.QLocale.Peru))
        self.verticalLayout = QtGui.QVBoxLayout(self)
        self.dateEdit = QtGui.QDateEdit(self)
        self.dateEdit.setDisplayFormat("MMM dd yyyy")
        self.verticalLayout.addWidget(self.dateEdit)
        self.timeEdit = QtGui.QTimeEdit(self)
        self.timeEdit.setDisplayFormat("hh:mm:ss AP")
        self.verticalLayout.addWidget(self.timeEdit)
        self.updateTime()
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.updateTime)
        self.timer.start(1)

    def updateTime(self):
        current = QtCore.QDateTime.currentDateTime()
        self.dateEdit.setDate(current.date())
        self.timeEdit.setTime(current.time())


def main():
    app = QtGui.QApplication(sys.argv)
    w = Widget()
    w.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()