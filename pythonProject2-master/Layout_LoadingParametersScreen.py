# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'C:\Users\TomatoTech\Downloads\Layout_LoadingParametersScreen.ui'
#
# Created by: PyQt5 UI code generator 5.9.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt

class ProgressWindow(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setWindowTitle("Parameters in progress")
        self.progress = QtWidgets.QProgressBar(self)
        self.progress.setAlignment(Qt.AlignCenter)
        self.progress.setFixedSize(340, 30)
        
        self.label = QtWidgets.QLabel(self)
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setFixedSize(330, 30)
        self.label.setText("Please wait. This process can take a few moments...")
        
        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(self.label)
        layout.addWidget(self.progress)
        
    def setValue(self, value):
        self.progress.setValue(value)
        QtWidgets.QApplication.processEvents()
        
    def setText(self, text):
        self.label.setText(text)