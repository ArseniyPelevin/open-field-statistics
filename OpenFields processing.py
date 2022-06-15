from PyQt6.QtWidgets import (QApplication, QMainWindow, QLabel, QLineEdit,
     QVBoxLayout, QWidget, QPushButton, QFileDialog)

import pandas as pd

import sys # Только для доступа к аргументам командной строки

class Statistics():
    def __init__(self, table):
        self.table = table
        self.table.columns.values[0] = "Time"      
        self.totalTime = self.calcTotalTime()
        self.totalDistance = self.calcDistance()
        self.totalVelocity = self.calcTotalVelocity()
        self.rearings = self.calcRearings()
        print(self.table)

    def calcTotalTime(self):
        timeStart = pd.Timestamp(self.table.iloc[0, 0])
        timeEnd = pd.Timestamp(self.table.iloc[-1, 0])
        totalTimeSec = pd.Interval(timeStart, timeEnd).length.seconds
        totalTimeMicrSec = pd.Interval(timeStart, timeEnd).length.microseconds
        totalTime = f"{totalTimeSec}.{totalTimeMicrSec}"
        print(totalTime)
        return totalTime
        
    def calcDistance(self):
        pass
        
    def calcTotalVelocity(self):
        pass
        
    def calcRearings(self):
        pass
        

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("OpenField processing")
        self.getFileButton = QPushButton("Select file")
        self.showStatButton = QPushButton("Show general statistics")
        self.table = pd.DataFrame()
        
        # self.line.textChanged.connect(self.label.setText)
        self.getFileButton.clicked.connect(self.getFile)
        self.showStatButton.clicked.connect(self.showStat)
        
        # self.line = QLineEdit()        
        
        layout = QVBoxLayout()
        # layout.addWidget(self.line)
        # layout.addWidget(self.label)
        layout.addWidget(self.getFileButton)
        layout.addWidget(self.showStatButton)
        
        container = QWidget()
        container.setLayout(layout)
        

        # self.button.released.connect(self.button_was_toggled)
        
        self.setCentralWidget(container)
        
    def getFile(self):
        self.file, _filter = QFileDialog.getOpenFileName(self, 
                             "Open .csv file", r"C:\OpenField\Data1.csv", "CSV files (*.csv)")
        self.table = pd.read_csv(self.file, delimiter=";")
        self.stat = Statistics(self.table) 
        
    def showStat(self):
        self.totalTime = QLabel(f"Total time: {self.stat.totalTime}")
        self.totalDistance = QLabel(f"Total distance: {self.stat.totalDistance}")
        self.totalVelocity = QLabel(f"Total velocity: {self.stat.totalVelocity}")
        self.rearings = QLabel(f"Rearings: {self.stat.rearings}")
        
    # def button_text(self):
    #     self.button.setText("Pushed")
    # def button_was_toggled(self):
    #     self.button.setText("Unpushed")
        

    
        

app = QApplication(sys.argv)
window = MainWindow()
window.show()
app.exec()