from PyQt6.QtWidgets import (QApplication, QMainWindow, QLabel, QLineEdit,
     QVBoxLayout, QWidget, QPushButton, QFileDialog)

import pandas as pd

import sys # Только для доступа к аргументам командной строки

class Statistics():
    def __init__(self, table):
        print(table)
        table.rename(columns={"":"Time"})
        self.totalDistance = self.calcDistance()
        self.totalVelocity = self.calcTotalVelocity()
        self.rearings = self.calcRearings()
        self.totalTime = self.calcTotalTime()
        

        
    def calcDistance(self):
        pass
        
    def calcTotalVelocity(self):
        pass
        
    def calcRearings(self):
        pass
        
    def calcTotalTime(self):
        pass
        

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("OpenField processing")
        self.button = QPushButton("Select file")
        self.table = pd.DataFrame()
        
        # self.line.textChanged.connect(self.label.setText)
        self.button.clicked.connect(self.getFile)
        
        self.totalDistance = QLabel(f"Total distance: {self.stat.totalDistance}")
        self.rearings = QLabel()
        self.totalVelocity = QLabel()
        # self.line = QLineEdit()        
        
        layout = QVBoxLayout()
        # layout.addWidget(self.line)
        # layout.addWidget(self.label)
        layout.addWidget(self.button)
        
        container = QWidget()
        container.setLayout(layout)
        

        # self.button.released.connect(self.button_was_toggled)
        
        self.setCentralWidget(container)
        
    def getFile(self):
        self.file, _filter = QFileDialog.getOpenFileName(self, 
                             "Open .csv file", r"C:\OpenField", "CSV files (*.csv)")
        self.table = pd.read_csv(self.file)
        self.stat = Statistics(self.table) 
        print(type(self.table))
        
    # def button_text(self):
    #     self.button.setText("Pushed")
    # def button_was_toggled(self):
    #     self.button.setText("Unpushed")
        

    
        

app = QApplication(sys.argv)
window = MainWindow()
window.show()
app.exec()