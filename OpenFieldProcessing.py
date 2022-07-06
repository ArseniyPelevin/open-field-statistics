#!/usr/bin/env python3

#from PyQt6.QtWidgets import (QApplication, QMainWindow, QLabel, QLineEdit,
#     QVBoxLayout, QHBoxLayout, QGridLayout, QWidget, QPushButton, QFileDialog)
#from PyQt6.QtCore import QEvent
#from PyQt6.QtGui import QFontMetrics, QFont

from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from superqt import QRangeSlider

import pandas as pd

from OpenFieldStatistics import OFStatistics

import sys
import re
     

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("OpenField processing")
        self.setGeometry(100, 100, 1000, 600)
        
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
        
        self.map = QLabel()
                
        self.getFileButton.clicked.connect(self.getFile)
        # Check if input is correct
        self.startTime.textEdited.connect(lambda: self.checkCorrect(self.startTime))
        self.endTime.textEdited.connect(lambda: self.checkCorrect(self.endTime))
        
        # Now update time range from text
        self.startTime.editingFinished.connect(self.textUpdateTimeRange)
        self.endTime.editingFinished.connect(self.textUpdateTimeRange)
        # Update time range from slider
        self.timeRangeSlider.sliderMoved.connect(self.updateMap)
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
        # controlLayout.addWidget(self.selectTime, alignment = Qt.AlignBottom)
        controlLayout.addWidget(self.map, alignment = Qt.AlignCenter)
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
        self.stat = OFStatistics(self.df) 
        self.totalStat()
        self.setTimeRange()
        self.drawMap(0, self.df.index[-1])
        
    def totalStat(self):
        self.totalTime.setText(f"Total time: {self.stat.totalTime} s")
        self.totalDistance.setText(f"Total distance: {self.stat.totalDistance} cm")
        self.totalVelocity.setText(f"Total velocity: {self.stat.totalVelocity} cm/s")
        self.totalRearings.setText(f"Total rearings: {self.stat.totalRearings}")
        
    def selectedStat(self, start, end):
        iStart = self.stat.timePoint(self.df, start)
        iEnd = self.stat.timePoint(self.df, end)
        
        self.selectedTime.setText(f"Selected time: {start}-{end} s")
        
        selectedDistance = self.stat.calcDistance(self.df, iStart, iEnd)
        self.selectedDistance.setText(f"Selected distance: {selectedDistance} cm")
        
        selectedVelocity = self.stat.calcVelocity(start, end, selectedDistance)
        self.selectedVelocity.setText(f"Selected velocity: {selectedVelocity} cm/s")
        
        selectedRearings = self.stat.calcRearings(self.df, iStart, iEnd)
        self.selectedRearings.setText(f"Selected rearings: {selectedRearings}")
        
        self.drawMap(iStart, iEnd)
        
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
        
        self.timeRangeSlider.setValue([start*10, end*10])
        
        self.selectedStat(start, end)   
        
    # Check if time range input is correct, delete last char otherwise
    def checkCorrect(self, lineEdit):
        # Correct decimal 
        if not re.match(r'^\d+\.?\d*$', lineEdit.text()):
            lineEdit.backspace()
            return 
        
        # In total time range
        # No need to check for start < 0, we can't enter negative number
        num = float(lineEdit.text())
        if not num <= self.stat.totalTime:
            lineEdit.backspace()
            return
        
        # start < end
        if not float(self.startTime.text()) < float(self.endTime.text()):
            lineEdit.backspace()
            return
        
    def updateMap(self):
        start, end = [x/10 for x in self.timeRangeSlider.value()]
        iStart = self.stat.timePoint(self.df, start)
        iEnd = self.stat.timePoint(self.df, end)
        self.drawMap(iStart, iEnd)
                
    def drawMap(self, iStart, iEnd):
        numLasers = 16
        mapSide = 320
        canvas = QPixmap(mapSide + 1, mapSide + 1)
        canvas.fill()
        painter = QPainter(canvas)
        cell = int(mapSide / numLasers)
        
        # Draw grid
        for i in range(0, numLasers + 1):
            step = cell * i
            painter.drawLine(0, step, mapSide, step)
            painter.drawLine(step, 0, step, mapSide)
            
        # Draw path
        painter.setPen(QPen(Qt.red, 2))
        lastX, lastY = 0, 0
        for i, row in self.df.iloc[iStart:iEnd, :].iterrows():
            if row['X'] != 0 and row['Y'] != 0:
                if not lastX:
                    lastX = row['X'] * cell - cell / 2
                    lastY = row['Y'] * cell - cell / 2
                    continue
                x = row['X'] * cell - cell / 2
                y = row['Y'] * cell - cell / 2
                #print(f'lastx {lastX}, lastY {lastY}, x {x}, y {y}')
                painter.drawLine(lastX, lastY, x, y)
                lastX = x
                lastY = y
           
        painter.end()
        self.map.setPixmap(canvas)
        

        
            


app = QApplication(sys.argv)
window = MainWindow()
window.show()
app.exec()