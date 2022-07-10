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

import os
import re
     

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("OpenField processing")
        self.setGeometry(100, 100, 800, 500)
        
        self.numLasers = 16
        self.mapSide = 320 # px
        
        generalLayout = QHBoxLayout()
        controlLayout = QGridLayout()
        timeRangeLayout = QGridLayout()
        dataLayout = QVBoxLayout()
        self.areaButtonLayout = QVBoxLayout()
        
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
        self.drawMap()
        self.areaButtons()
        
        self.areaBtn['Cell'].toggled.connect(self.cellMapButtons)
        self.areaBtn['Vertical_halves'].toggled.connect(self.vHalfArea)
        self.areaBtn['Horizontal_halves'].toggled.connect(self.hHalfArea)
        self.areaBtn['Wall'].toggled.connect(self.wallArea)        
        self.areaBtn['Column'].toggled.connect(self.columnMapButtons)
        self.areaBtn['Row'].toggled.connect(self.rowMapButtons)
        self.areaBtn['Square'].toggled.connect(self.squareMapButtons)
                
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
               
        timeRangeLayout.addWidget(self.startTime, 0, 0, Qt.AlignLeft)
        timeRangeLayout.addWidget(self.endTime, 0, 1, Qt.AlignRight)
        timeRangeLayout.addWidget(self.timeRangeSlider, 1, 0, 1, 2, Qt.AlignBottom)
        
        controlLayout.addWidget(self.getFileButton, 0, 0, 1, 2)
        controlLayout.addWidget(self.fileName, 1, 0, 1, 2, Qt.AlignTop)
        controlLayout.addLayout(self.areaButtonLayout, 2, 0, 1, 1, Qt.AlignLeft)
        controlLayout.addWidget(self.map, 2, 1, 1, 1, Qt.AlignHCenter)
        controlLayout.addLayout(timeRangeLayout, 3, 0, 1, 2, Qt.AlignBottom)
        
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
        
        self.setCentralWidget(container)
        
    def getFile(self):
        # self.file, _filter = QFileDialog.getOpenFileName(self, "Open .csv file", 
        #                      r"C:\OpenField\Data1.csv", "CSV files (*.csv)")
        file = r"C:\OpenField\Data1.csv"
        self.fileName.setText(file)
        self.df = pd.read_csv(file, delimiter=";")
        self.stat = OFStatistics(self.df) 
        self.totalStat()
        self.setTimeRange()
        self.drawPath(0, self.df.index[-1])
        
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
        
        self.drawPath(iStart, iEnd)
        
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
        self.drawPath(iStart, iEnd)
                
    def drawMap(self):
        canvas = QPixmap(self.mapSide + 1, self.mapSide + 1)
        canvas.fill()
        painter = QPainter(canvas)
        cell = int(self.mapSide / self.numLasers)
        
        # Draw grid
        for i in range(0, self.numLasers + 1):
            step = cell * i
            painter.drawLine(0, step, self.mapSide, step)
            painter.drawLine(step, 0, step, self.mapSide)
            
        painter.end()
        self.map.setPixmap(canvas) 
        return cell, canvas
            
    def drawPath(self, iStart, iEnd):
        cell, canvas = self.drawMap()
        painter = QPainter(canvas)
        painter.setPen(QPen(Qt.red, 2))
        lastX, lastY = 0, 0
        for i, row in self.df.iloc[iStart:iEnd, :].iterrows():
            if row['X'] != 0 and row['Y'] != 0:
                if not lastX:
                    lastX = int(row['X'] * cell - cell / 2)
                    lastY = int(row['Y'] * cell - cell / 2)
                    continue
                x = int(row['X'] * cell - cell / 2)
                y = int(row['Y'] * cell - cell / 2)
                painter.drawLine(lastX, lastY, x, y)
                lastX = x
                lastY = y
           
        painter.end()
        self.map.setPixmap(canvas)   
        
    def newAreaBtn(self, newBtn):
        for name in self.areaBtnNames:
            if name != newBtn:
                # if button is checked - disable others
                # if unchecked - enable others
                isOccupied = self.areaBtn[newBtn].isChecked()
                self.areaBtn[name].setEnabled(not isOccupied)
        
        # Delete old buttons
        if hasattr(self, 'mapLayout'):
            for i in reversed(range(self.mapLayout.count())):
                item = self.mapLayout.itemAt(i).widget()      
                item.deleteLater()
            # and old map buttons' layout
            self.mapLayout.deleteLater()
        self.mapButtons = []

        # Set Style Sheet for all map buttons
        with open('ButtonStyleSheet.css') as buttonStyleSheet:
            self.map.setStyleSheet(buttonStyleSheet.read())
            
    def cellMapButtons(self):        
        self.newAreaBtn('Cell')
        
        cell = int(self.mapSide / self.numLasers) # px
        
        self.mapLayout = QGridLayout(self.map)
        self.mapLayout.setSpacing(0)
        self.mapLayout.setContentsMargins(0, 0, 0, 0)
        
        for i in range(self.numLasers):
            self.mapButtons.append([])
            for j in range(self.numLasers):
                self.mapButtons[i].append(QPushButton('', self.map))
                self.mapButtons[i][j].setFixedSize(cell, cell)
                self.mapButtons[i][j].setCheckable(True)
                self.mapLayout.addWidget(self.mapButtons[i][j], i, j)
                
    def vHalfArea(self):
        self.newAreaBtn('Vertical_halves') 
        
        self.mapLayout = QHBoxLayout(self.map)
        self.mapLayout.setSpacing(0)
        self.mapLayout.setContentsMargins(0, 0, 0, 0)
        
        halves = [QPushButton(), QPushButton()]
        for half in halves:
            half.setFixedSize(int(self.mapSide / 2), self.mapSide)
            self.mapLayout.addWidget(half)
        halves[0].setStyleSheet("background-color: rgba(255, 0, 0, 0.3)")
        halves[1].setStyleSheet("background-color: rgba(0, 255, 0, 0.3)")
        
    
    def hHalfArea(self):
        self.newAreaBtn('Horizontal_halves')
        
        self.mapLayout = QVBoxLayout(self.map)
        self.mapLayout.setSpacing(0)
        self.mapLayout.setContentsMargins(0, 0, 0, 0)
        
        halves = [QPushButton(), QPushButton()]
        for half in halves:
            half.setFixedSize(self.mapSide, int(self.mapSide / 2))
            self.mapLayout.addWidget(half)
        halves[0].setStyleSheet("background-color: rgba(255, 0, 0, 0.3)")
        halves[1].setStyleSheet("background-color: rgba(0, 255, 0, 0.3)")
    
    def wallArea(self):
        self.newAreaBtn('Wall')
        
        self.mapLayout = QGridLayout(self.map)
        self.mapLayout.setSpacing(0)
        self.mapLayout.setContentsMargins(0, 0, 0, 0)
        
        pixmap = QPixmap(os.path.join('Area_pixmaps', 'wall.png'))
        outer = QPushButton()
        outer.setFixedSize(self.mapSide, self.mapSide)
        outer.setMask(pixmap.scaled(outer.size(), Qt.IgnoreAspectRatio).mask())
        outer.setStyleSheet("background-color: rgba(255, 0, 0, 0.3)")
        self.mapLayout.addWidget(outer, 0, 0)
        
        inner = outer = QPushButton()
        inner.setFixedSize(int(self.mapSide / 2), int(self.mapSide / 2))
        inner.setStyleSheet("background-color: rgba(0, 255, 0, 0.3)")
        self.mapLayout.addWidget(inner, 0, 0, alignment = Qt.AlignCenter)

    def columnMapButtons(self):      
        self.newAreaBtn('Column')
        
        self.mapLayout = QHBoxLayout(self.map)
        self.mapLayout.setSpacing(0)
        self.mapLayout.setContentsMargins(0, 0, 0, 0)
        
        cell = int(self.mapSide / self.numLasers) # px
        
        for i in range(self.numLasers):
            self.mapButtons.append(QPushButton('', self.map))
            self.mapButtons[i].setFixedSize(cell, self.mapSide)
            self.mapButtons[i].setCheckable(True)
            self.mapLayout.addWidget(self.mapButtons[i])
            
    def rowMapButtons(self):      
        self.newAreaBtn('Row')
        
        self.mapLayout = QVBoxLayout(self.map)
        self.mapLayout.setSpacing(0)
        self.mapLayout.setContentsMargins(0, 0, 0, 0)
        
        cell = int(self.mapSide / self.numLasers) # px
        
        for i in range(self.numLasers):
            self.mapButtons.append(QPushButton('', self.map))
            self.mapButtons[i].setFixedSize(self.mapSide, cell)
            self.mapButtons[i].setCheckable(True)
            self.mapLayout.addWidget(self.mapButtons[i])       
        
    def squareMapButtons(self):
        self.newAreaBtn('Square')
        
        self.mapLayout = QGridLayout(self.map)
        self.mapLayout.setSpacing(0)
        self.mapLayout.setContentsMargins(0, 0, 0, 0)
        
        for i in range(8):
            self.mapButtons.append(QPushButton('', self.map))
            self.mapButtons[i].setFixedSize(self.mapSide, self.mapSide)
            self.mapButtons[i].setCheckable(True)
            pixmap = QPixmap(os.path.join('Area_pixmaps', f'{i+1}.png')) 
            self.mapButtons[i].setMask(pixmap.scaled(self.mapButtons[i].size(), 
                                                    Qt.IgnoreAspectRatio).mask())
            self.mapLayout.addWidget(self.mapButtons[i], 0, 0) 
            
    def areaButtons(self):
        self.areaBtnNames = ['Cell', 'Vertical_halves', 'Horizontal_halves',
                             'Wall', 'Column', 'Row', 'Square']
        self.areaBtn = {}
        numAreaBtn = 7
        for i in range(numAreaBtn):
            name = self.areaBtnNames[i]
            self.areaBtn[name] = QPushButton()
            
            pixmap = QPixmap(os.path.join('Area_Buttons_pixmaps', 
                                  self.areaBtnNames[i] + '.png'))

            self.areaBtn[name].setIcon(QIcon(pixmap))
            self.areaBtn[name].setIconSize(QSize(30, 30))
            # Button is 2px larger than icon, otherwise some icon's pxls are outside
            self.areaBtn[name].setFixedSize(32, 32)
            self.areaButtonLayout.addWidget(self.areaBtn[name])
            self.areaBtn[name].setCheckable(True)

        self.areaButtonLayout.setSpacing(int((self.mapSide - (32 * numAreaBtn)) / \
                                         (numAreaBtn - 1)))
        self.areaButtonLayout.setContentsMargins(0, 0, 30, 0)
            
app = QApplication(os.sys.argv)
window = MainWindow()
window.show()
app.exec()