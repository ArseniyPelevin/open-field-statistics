#from PyQt6.QtWidgets import (QApplication, QMainWindow, QLabel, QLineEdit,
#     QVBoxLayout, QHBoxLayout, QGridLayout, QWidget, QPushButton, QFileDialog)
#from PyQt6.QtCore import QEvent
#from PyQt6.QtGui import QFontMetrics, QFont

from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from superqt import QRangeSlider

import pandas as pd

from datetime import datetime, timedelta

import math as m
import statistics as st

import sys

class Statistics():
    def __init__(self, df):
        df.columns.values[0] = "Time"      
        self.totalTime = self.calcTotalTime(df)
        self.totalDistance = self.calcTotalDistance(df)
        self.totalVelocity = self.calcVelocity(0, self.totalTime, self.totalDistance)
        self.totalRearings = self.calcRearings(df, 0, df.index[-1])
        
        #test
        #self.timePoint(df, 11)
        
#        print(df.to_string())
       # print(df)
       
    def timePoint(self, df, time):
        tp = self.timeStart + timedelta(seconds=time)
        
        # find closest existing time point
        for i, row in df.iterrows():
            curTime = datetime.strptime(df.at[i, 'Time'][:-1], '%H:%M:%S.%f')
            if curTime > tp:
                tp = i - 1
                break
            elif i == df.index[-1]:
                tp = i
                # Find row index prior to desired time
                
        # print(f'Timepoint of {time} = {tp}')
        return tp

    def calcTotalTime(self, df):
        self.timeStart = df.at[0, 'Time'][:-1]      
        # [:-1] because original time has 7 decimals instead of 6
        self.timeStart = datetime.strptime(self.timeStart, '%H:%M:%S.%f')
        timeEnd = df.at[df.index[-1], 'Time'][:-1]
        timeEnd = datetime.strptime(timeEnd, '%H:%M:%S.%f')
        totalTime = round(timedelta.total_seconds(timeEnd-self.timeStart), 1)
        print(f"Total time: {totalTime} s")
        return totalTime
        
    # distance in cell units yet
    def calcTotalDistance(self, df):
        df['X'] = 0
        df['Y'] = 0
        df['dist'] = 0
        totalDistance = 0
        for i, row in df.iterrows():
            
            # calculate central point of animal
            df.at[i, 'X'] = st.fmean([row['X1'], row['X2']])
            df.at[i, 'Y'] = st.fmean([row['Y1'], row['Y2']])
            
            if i == 0: continue
            p = [df.at[i-1, 'X'], df.at[i-1, 'Y']]   # previous point
            q = [df.at[i, 'X'], df.at[i, 'Y']]       # current point
            dist = m.dist(p, q) * (40 / 16)
            # 40 cm - edge of OpenField box, 16 - number of cells
            df.at[i, 'dist'] = dist                  # dist since last point
            totalDistance += dist
        totalDistance = round(totalDistance, 1)
                
        print(f'Total distance: {totalDistance} cm')
        return totalDistance
    
    def calcDistance(self, df, start, end):
        row1 = self.timePoint(df, start)
        row2 = self.timePoint(df, end)
        distance = 0
        for i, row in df.iloc[row1:row2+1, :].iterrows():
            distance += row['dist']
        distance = round(distance)
        print(f"Selected distance: {distance} cm")
        return distance
    
    def calcVelocity(self, start, end, dist):
        velocity = dist / (end - start)
        velocity = round(velocity, 1)
        print(f"Total velocity: {velocity} cm/s")
        return velocity
        
    def calcRearings(self, df, start, end):
        row1 = self.timePoint(df, start)
        row2 = self.timePoint(df, end)
        wasRearing = False
        rearings = 0
        for i, row in df.iloc[row1:row2+1, :].iterrows():
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
       
        #self.df = pd.DataFrame()
        
        self.fileName = QLabel()
        self.selectTime = QLabel("Select time interval:")
        
        self.totalTime = QLabel("Total time:")
        self.totalDistance = QLabel("Total distance:")
        self.totalVelocity = QLabel("Total velocity:")
        self.totalRearings = QLabel("Total rearings:")
        
        self.selectedTime = QLabel("Selected time:")
        self.selectedDistance = QLabel("Selected distance:")
        self.selectedVelocity = QLabel("Selected velocity:")
        self.selectedRearings = QLabel("Selected rearings:")
        
        self.startTime = QLineEdit()
        self.startTime.setDisabled(True)
        self.endTime = QLineEdit()
        self.endTime.setDisabled(True)
        self.timeRangeSlider = QRangeSlider(Qt.Horizontal)
        self.timeRangeSlider.setDisabled(True)
        
        self.getFileButton.clicked.connect(self.getFile)
        self.startTime.editingFinished.connect(self.textUpdateTimeRange)
        self.endTime.editingFinished.connect(self.textUpdateTimeRange)
        self.timeRangeSlider.sliderReleased.connect(self.sliderUpdateTimeRange)  
        
        generalLayout = QHBoxLayout()
        controlLayout = QVBoxLayout()
        timeRangeLayout = QGridLayout()
        dataLayout = QVBoxLayout()
        
        timeRangeLayout.addWidget(self.startTime, 0, 0, alignment = Qt.AlignLeft)
        timeRangeLayout.addWidget(self.endTime, 0, 1, alignment = Qt.AlignRight)
        timeRangeLayout.addWidget(self.timeRangeSlider, 1, 0, 1, 2)
        
        controlLayout.addWidget(self.getFileButton)
        controlLayout.addWidget(self.fileName, alignment = Qt.AlignTop)
        controlLayout.addWidget(self.selectTime, alignment = Qt.AlignBottom)
        
        controlLayout.addLayout(timeRangeLayout)
        
        dataLayout.addWidget(self.totalTime)
        dataLayout.addWidget(self.totalDistance)
        dataLayout.addWidget(self.totalVelocity)
        dataLayout.addWidget(self.totalRearings)
        dataLayout.addSpacing(QFontMetrics(QFont()).height())
        dataLayout.addWidget(self.selectedTime)
        dataLayout.addWidget(self.selectedDistance)
        dataLayout.addWidget(self.selectedVelocity)
        dataLayout.addWidget(self.selectedRearings)
        
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
        self.totalStat()
        self.setTimeRange()
        
    def totalStat(self):
        self.totalTime.setText(f"Total time: {self.stat.totalTime} s")
        self.totalDistance.setText(f"Total distance: {self.stat.totalDistance} cm")
        self.totalVelocity.setText(f"Total velocity: {self.stat.totalVelocity} cm/s")
        self.totalRearings.setText(f"Total rearings: {self.stat.totalRearings}")
        
    def selectedStat(self, start, end):
        self.selectedTime.setText(f"Selected time: {start}-{end} s")
        
        selectedDistance = self.stat.calcDistance(self.df, start, end)
        self.selectedDistance.setText(f"Selected distance: {selectedDistance} cm")
        
        selectedVelocity = self.stat.calcVelocity(start, end, selectedDistance)
        self.selectedVelocity.setText(f"Selected velocity: {selectedVelocity} cm/s")
        
        selectedRearings = self.stat.calcRearings(self.df, start, end)
        self.selectedRearings.setText(f"Selected rearings: {selectedRearings}")
        
    def setTimeRange(self):
        # slider is sensitive to 0.1 sec
        self.timeRangeSlider.setRange(0, self.stat.totalTime*10)
        self.timeRangeSlider.setValue([0, self.stat.totalTime*10])
        
        self.startTime.setEnabled(True)
        self.endTime.setEnabled(True)
        self.timeRangeSlider.setEnabled(True)
        
        self.startTime.setText(str(0))
        self.endTime.setText(str(self.stat.totalTime))
        
    def sliderUpdateTimeRange(self):
        start, end = [x/10 for x in self.timeRangeSlider.value()]
        
        self.startTime.setText(str(start))
        self.endTime.setText(str(end))

        self.selectedStat(start, end)
        
    def textUpdateTimeRange(self):
        start = float(self.startTime.text())
        end = float(self.endTime.text())
        if start >= end: 
            return
        
        self.timeRangeSlider.setValue([start*10, end*10])
        
        self.selectedStat(start, end)
        
    def released(self):
        print('released')
    def pressed(self):
        print('pressed')
    def changed(self):
        print('changed')
    def moved(self):
        print('moved')
        
        
        
    # def button_text(self):
    #     self.button.setText("Pushed")
    # def button_was_toggled(self):
    #     self.button.setText("Unpushed")
        

    
        

app = QApplication(sys.argv)
window = MainWindow()
window.show()
app.exec()