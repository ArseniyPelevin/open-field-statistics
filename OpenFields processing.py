from PyQt6.QtWidgets import (QApplication, QMainWindow, QLabel, QLineEdit,
     QVBoxLayout, QHBoxLayout, QWidget, QPushButton, QFileDialog)
from PyQt6.QtCore import QEvent
from PyQt6.QtGui import QFontMetrics, QFont

import pandas as pd

import math as m
import statistics as st

import sys

class Statistics():
    def __init__(self, df):
        df.columns.values[0] = "Time"      
        self.totalTime = self.calcTotalTime(df)
        self.totalDistance = self.calcDistance(df)
        self.totalVelocity = self.calcVelocity()
        self.rearings = self.calcRearings(df)
        
        #test
        #self.timePoint(df, 11)
        
#        print(df.to_string())
       # print(df)
       
    def timePoint(self, df, time):
        tp = self.timeStart + pd.Timestamp(time, unit='s')
        
        # find closest existing time point
        for i, row in df.iterrows():
            if df.at[i, 'Time'] > tp:
                tp = df.at[i-1, 'Time']
                
        print(f'timepoint = {tp}')
        return tp

    def calcTotalTime(self, df):
        self.timeStart = pd.Timestamp(df.at[0, 'Time'])
        timeEnd = pd.Timestamp(df.at[df.index[-1], 'Time'])
        totalTimeSec = pd.Interval(self.timeStart, timeEnd).length.seconds
        totalTimeMicrSec = pd.Interval(self.timeStart, timeEnd).length.microseconds
        totalTime = float(f"{totalTimeSec}.{totalTimeMicrSec}")
        totalTime = round(totalTime, 1)
        print(f"Total time: {totalTime} s")
        return totalTime
        
    # distance in cell units yet
    def calcDistance(self, df):
        df['X'] = 0
        df['Y'] = 0
        df['dist'] = 0
        distance = 0
        for i, row in df.iterrows():
            
            # calculate central point of animal
            df.at[i, 'X'] = st.fmean([row['X1'], row['X2']])
            df.at[i, 'Y'] = st.fmean([row['Y1'], row['Y2']])
            
            if i == 0: continue
            p = [df.at[i-1, 'X'], df.at[i-1, 'Y']]   # previous point
            q = [df.at[i, 'X'], df.at[i, 'Y']]       # current point
            dist = m.dist(p, q)
            df.at[i, 'dist'] = dist                  # dist since last point
            distance += dist
        distance = distance * (40 / 16)
        # 40 cm - edge of OpenField box, 16 - number of cells
        distance = round(distance, 1)
                
        print(f'Total distance: {distance} cm')
        return distance
    
    def calcVelocity(self):
        velocity = self.totalDistance / self.totalTime
        velocity = round(velocity, 1)
        print(f"Total velocity: {velocity} cm/s")
        return velocity
        
    def calcRearings(self, df):
        wasRearing = False
        rearings = 0
        for i, row in df.iterrows():
            if row['Z'] and not wasRearing:
                rearings += 1
                wasRearing = True
            elif not row['Z'] and wasRearing:
                wasRearing = False
        print(f'Rearings: {rearings}')
        return rearings
        

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("OpenField processing")
        
        self.getFileButton = QPushButton("Select file")
        self.showStatButton = QPushButton("Show general statistics")
       
        self.df = pd.DataFrame()
        
        self.fileName = QLabel()
        self.selectTime = QLabel("Select time interval:")
        
        self.totalTime = QLabel("Total time:")
        self.totalDistance = QLabel("Total distance:")
        self.totalVelocity = QLabel("Total velocity:")
        self.totalRearings = QLabel("Total rearings:")
        
        self.selectedTime = QLabel("Selected time:")
        self.selectedDistance = QLabel("Selected distance:")
        self.selectedVelocity = QLabel("Selected velocity:")
        self.selectedRrearings = QLabel("Selected rearings:")
        self.startTime = QLineEdit()
        self.endTime = QLineEdit()
        
        # self.line.textChanged.connect(self.label.setText)
        self.getFileButton.clicked.connect(self.getFile)
       # self.showStatButton.clicked.connect(self.showStat)
        
        # self.line = QLineEdit()        
        
        generalLayout = QHBoxLayout()
        controlLayout = QVBoxLayout()
        dataLayout = QVBoxLayout()

        controlLayout.addWidget(self.getFileButton)
        controlLayout.addWidget(self.fileName)
        controlLayout.addWidget(self.selectTime)
        # QFileOpenEvent.connect(self.updateStat)
        # controlLayout.addWidget(self.showStatButton)
        
        dataLayout.addWidget(self.totalTime)
        dataLayout.addWidget(self.totalDistance)
        dataLayout.addWidget(self.totalVelocity)
        dataLayout.addWidget(self.totalRearings)
        dataLayout.addSpacing(QFontMetrics(QFont()).height())
        dataLayout.addWidget(self.selectedTime)
        dataLayout.addWidget(self.selectedDistance)
        dataLayout.addWidget(self.selectedVelocity)
        dataLayout.addWidget(self.selectedRrearings)
        
        generalLayout.addLayout(controlLayout)
        generalLayout.addLayout(dataLayout)
        
        container = QWidget()
        container.setLayout(generalLayout)
        
        # self.button.released.connect(self.button_was_toggled)
        
        self.setCentralWidget(container)
        
    def getFile(self):
        self.file, _filter = QFileDialog.getOpenFileName(self, "Open .csv file", 
                             r"C:\OpenField\Data1.csv", "CSV files (*.csv)")
        self.fileName.setText(self.file)
        self.df = pd.read_csv(self.file, delimiter=";")
        self.stat = Statistics(self.df) 
        self.updateStat()
        
    def updateStat(self):
        self.totalTime.setText(f"Total time: {self.stat.totalTime} s")
        self.totalDistance.setText(f"Total distance: {self.stat.totalDistance} cm")
        self.totalVelocity.setText(f"Total velocity: {self.stat.totalVelocity} cm/s")
        self.totalRearings.setText(f"Rearings: {self.stat.rearings}")
        
    # def button_text(self):
    #     self.button.setText("Pushed")
    # def button_was_toggled(self):
    #     self.button.setText("Unpushed")
        

    
        

app = QApplication(sys.argv)
window = MainWindow()
window.show()
app.exec()