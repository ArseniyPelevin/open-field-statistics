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

import ctypes
import sip
     

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("OpenField processing")
        self.setGeometry(100, 100, 800, 500)
        
        self.numLasers = 16
        self.mapSide = 320 # px
        
        print(os.sys.version)
        
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
        
        # self.checkedAreaBtn = 'Cell'
        # self.cellMapButtons()
        self.areaBtn['Cell'].toggled.connect(self.cellMapButton)
        self.areaBtn['Vertical_halves'].toggled.connect(self.vHalfMapArea)
        self.areaBtn['Horizontal_halves'].toggled.connect(self.hHalfMapArea)
        self.areaBtn['Wall'].toggled.connect(self.wallMapArea)        
        self.areaBtn['Column'].toggled.connect(self.columnMapButtons)
        self.areaBtn['Row'].toggled.connect(self.verticalMapButtons)
        self.areaBtn['Square'].toggled.connect(self.horizontalMapButtons)


                
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
        
        # self.button.released.connect(self.button_was_toggled)
        
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
        
    def newAreaBtn(self, name, times):
        print('a')
        if hasattr(self, 'mapLayout'):
            print(self.mapLayout)
       # self.areaBtn[name].setChecked(True)
        #self.areaBtn[self.checkedAreaBtn].setChecked(False)
        self.checkedAreaBtn = name
        if hasattr(self, 'mapLayout'):
            print('b')
            if hasattr(self, 'mapLayout'):
                print(self.mapLayout)
            for i in reversed(range(self.mapLayout.count())):
                item = self.mapLayout.itemAt(i).widget()
                #item.setParent(None)         # We want all previous buttons deleted
                item.deleteLater()
                # sip.delete(item)
             

          #  print(self.mapLayout, self.mapLayout.count())
        # if hasattr(self, 'mapButtons'):
        #     print('was here!!')
        #     for item in self.mapButtons:
        #         del item
            # self.mapLayout.deleteLater()
            # self.map.itemAt(0).removeItem(self.mapLayout)
            #sip.delete(self.mapLayout)
            # sip.delete(self.mapLayout)

            self.mapLayout.deleteLater()
            # QCoreApplication.processEvents()
            
            
           # print(self.mapLayout, self.mapLayout.count())
        # self.mapButtons = []
        # cell = int(self.mapSide / self.numLasers) # px
        with open('ButtonStyleSheet.css') as buttonStyleSheet:
            self.map.setStyleSheet(buttonStyleSheet.read())
        # return cell
        
        # if times == 0:
        #     if name == 'Cell': self.cellMapButtons(times)
        #     if name == 'Column': self.verticalMapButtons(times)
        #     if name == 'Row': self.horizontalMapButtons(times)
            
    def cellMapButtons(self, times):
        # print('CELL 1')
        # if hasattr(self, 'mapLayout'):
        #     print(self.mapLayout)
            
        # if times == 1: self.newAreaBtn('Cell', times)   
        
        # print('CELL 2')
        # if hasattr(self, 'mapLayout'):
        #     print(self.mapLayout)
           
        cell = int(self.mapSide / self.numLasers) # px
        mapCButtons = []
        
        self.mapLayout = QGridLayout(self.map)
        self.mapLayout.setSpacing(0)
        self.mapLayout.setContentsMargins(0, 0, 0, 0)
        
        for i in range(self.numLasers):
            mapCButtons.append([])
            for j in range(self.numLasers):
                mapCButtons[i].append(QPushButton('', self.map))
                mapCButtons[i][j].setFixedSize(cell, cell)
                mapCButtons[i][j].setCheckable(True)
                self.mapLayout.addWidget(mapCButtons[i][j], i, j)

        

            #self.cellMapButtons()
        
        # with open('ButtonStyleSheet.css') as buttonStyleSheet:
        #     self.map.setStyleSheet(buttonStyleSheet.read())

    def verticalMapButtons(self, times):
        # print('COLUMN 1')
        # if hasattr(self, 'mapLayout'):
        #     print(self.mapLayout)
            
        # cell = self.newAreaBtn('Column')  
        
        # print('COLUMN 2')
        # if hasattr(self, 'mapLayout'):
        #     print(self.mapLayout)
        
        self.mapLayout = QHBoxLayout(self.map)
        self.mapLayout.setSpacing(0)
        self.mapLayout.setContentsMargins(1, 1, 1, 1)
        
        cell = int(self.mapSide / self.numLasers) # px
        mapVButtons = []
        
        for i in range(self.numLasers):
            mapVButtons.append(QPushButton('', self.map))
            mapVButtons[i].setFixedSize(cell, self.mapSide)
            mapVButtons[i].setCheckable(True)
            self.mapLayout.addWidget(mapVButtons[i])
            
        print('Column', self.mapLayout, self.mapLayout.count())
        
        # if self.timesNewButton == 0:
        #     self.timesNewButton = 1
        #     self.newAreaBtn('Column')
        #     self.verticalMapButtons()
                
        # with open('ButtonStyleSheet.css') as buttonStyleSheet:
        #     self.map.setStyleSheet(buttonStyleSheet.read())
        
        # times += 1
        # if times < 2:
        #     self.newAreaBtn('Column', times)
            #self.cellMapButtons()
            
    def horizontalMapButtons(self):      
        # cell = self.newAreaBtn('Row')
        
        self.mapLayout = QVBoxLayout(self.map)
        self.mapLayout.setSpacing(0)
        self.mapLayout.setContentsMargins(1, 1, 1, 1)
        
        cell = int(self.mapSide / self.numLasers) # px
        mapHButtons = []
        
        for i in range(self.numLasers):
            mapHButtons.append(QPushButton('', self.map))
            mapHButtons[i].setFixedSize(self.mapSide, cell)
            mapHButtons[i].setCheckable(True)
            self.mapLayout.addWidget(mapHButtons[i])
            
        print('Row', self.mapLayout, self.mapLayout.count())
        
        # with open('ButtonStyleSheet.css') as buttonStyleSheet:
        #     self.map.setStyleSheet(buttonStyleSheet.read())
            
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
            # palette = QPalette()
            # palette.setBrush(self.areaBtn[name].backgroundRole(), QBrush(pixmap))

            # self.areaBtn[name].setPalette(palette)
            # self.areaBtn[name].setStyleSheet(f'''
            #         background-image: 
            #     url({os.path.join('Area_Buttons_pixmaps', self.areaBtnNames[i] + '.png')});
                   
            #         ''')
            # self.areaBtn[name].setIcon(QIcon(os.path.join('Area_Buttons_pixmaps', 
            #                                          self.areaBtnNames[i] + '.png')))
            self.areaBtn[name].setIcon(QIcon(pixmap))
          ##  self.areaBtn[name].setFlat(True)
           # self.areaBtn[name].setAutoFillBackground(True)
        #    self.areaBtn[name].setAttribute(Qt.WA_TranslucentBackground)
            self.areaBtn[name].setIconSize(QSize(30, 30))
            self.areaBtn[name].setFixedSize(30, 30)
            self.areaButtonLayout.addWidget(self.areaBtn[name])
            self.areaBtn[name].setCheckable(True)
            # print(name)
        self.areaButtonLayout.setSpacing(int((self.mapSide - (30 * numAreaBtn)) / \
                                         (numAreaBtn - 1)))
        self.areaButtonLayout.setContentsMargins(0, 0, 30, 0)
            
app = QApplication(os.sys.argv)
window = MainWindow()
window.show()
app.exec()