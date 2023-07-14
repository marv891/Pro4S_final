
from PyQt5 import QtCore, QtGui, QtWidgets


class confirmLaserOffUi(object):
    def setupErrorUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(350, 250)
        Dialog.setMinimumSize(QtCore.QSize(350, 150))
        Dialog.setMaximumSize(QtCore.QSize(350, 150))
        self.verticalLayoutWidget = QtWidgets.QWidget(Dialog)
        self.verticalLayoutWidget.setGeometry(QtCore.QRect(10, 10, 331, 120))
        self.verticalLayoutWidget.setObjectName("verticalLayoutWidget")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.verticalLayoutWidget)
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout.setObjectName("verticalLayout")
        self.label_3 = QtWidgets.QLabel(self.verticalLayoutWidget)
        font = QtGui.QFont()
        font.setPointSize(18)
        font.setBold(True)
        font.setUnderline(True)
        font.setWeight(75)
        self.label_2 = QtWidgets.QLabel(self.verticalLayoutWidget)
        font = QtGui.QFont()
        font.setPointSize(16)
        self.label_2.setFont(font)
        self.label_2.setAlignment(QtCore.Qt.AlignCenter)
        self.label_2.setObjectName("label_2")
        self.verticalLayout.addWidget(self.label_2)
        self.Hint1 = QtWidgets.QLabel(self.verticalLayoutWidget)
        self.Hint1.setMinimumSize(QtCore.QSize(0, 0))
        self.Hint1.setMaximumSize(QtCore.QSize(16777215, 200))
        font = QtGui.QFont()
        font.setBold(False)
        font.setWeight(50)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setSpacing(5)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.Retrybutton = QtWidgets.QPushButton(self.verticalLayoutWidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.Retrybutton.sizePolicy().hasHeightForWidth())
        self.Retrybutton.setSizePolicy(sizePolicy)
        self.Retrybutton.setMinimumSize(QtCore.QSize(93, 28))
        self.Retrybutton.setMaximumSize(QtCore.QSize(150, 50))
        self.Retrybutton.setAutoDefault(False)
        self.Retrybutton.setObjectName("Retrybutton")
        self.horizontalLayout.addWidget(self.Retrybutton)
        self.verticalLayout.addLayout(self.horizontalLayout)

        self.retranslateUi(Dialog)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "Receive image laser cross"))
        self.label_2.setText(_translate("Dialog", "Deactivate red laser!"))
        self.Retrybutton.setText(_translate("Dialog", "Laser deactivated"))


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    Dialog = QtWidgets.QDialog()
    ui = confirmLaserOffUi()
    ui.setupErrorUi(Dialog)
    Dialog.show()
    sys.exit(app.exec_())