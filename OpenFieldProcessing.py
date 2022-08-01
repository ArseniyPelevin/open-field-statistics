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
import numpy as np
import math as m
import csv

from OpenFieldStatistics import OFStatistics
# from NewStatistics import OFStatistics
from MapButtonStyleSheet import styleSheet, zoneColors, color

import os
import re
     

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("OpenField processing")
        self.setWindowIcon(QIcon('logo.png'))
        self.setGeometry(100, 100, 100, 100)
        
        self.setVariables()
        self.setWidgets()
        self.setSignals()
        self.setLayouts()
        
    def setVariables(self):
        self.param = {'numLasers': 16, 'mapSide': 320, 
                      'boxSide': 40, 'numStatParam': 4}
        self.numLasers = 16
        self.mapSide = 320 # px
        self.numStatParam = 4  # Time, distance, velocity, rearings
        self.statParam = ['time', 'dist', 'vel', 'rear']

        # OFStatistics.table(zones) default values
        self.zoneCoord = np.ones((self.numLasers, self.numLasers))     
        self.numZones = 0
        
        self.hasSelectedStat = False
    
    def setWidgets(self):
        self.getFileButton = QPushButton("Select file")
        self.getFileButton.setFixedWidth(80)
        self.fileName = QLabel()
        
        self.startTime = QLineEdit(alignment = Qt.AlignLeft)
        self.startTime.setFixedWidth(60)
        self.startTime.setDisabled(True)
        self.endTime = QLineEdit(alignment = Qt.AlignRight)
        self.endTime.setFixedWidth(60)
        self.endTime.setDisabled(True)
        self.timeRangeSlider = QRangeSlider(Qt.Horizontal)
        self.timeRangeSlider.setDisabled(True)
        
        self.timePeriod = QLabel("Time period every ")
        self.periodLine = QLineEdit(alignment = Qt.AlignRight)
        self.periodLine.setFixedWidth(60)
        self.periodLine.setDisabled(True)
        self.mins = QLabel(" min")
        
        self.addZoneBtn = QPushButton('Add zone')
        self.addZoneBtn.setFixedWidth(80)
        self.addZoneBtn.setDisabled(True)
        
        self.saveButton = QPushButton('Save data')
        self.saveButton.setFixedWidth(80)
        self.saveButton.setDisabled(True)
        
        self.areaButtons()
        self.map = QLabel()
        self.drawMap()
        self.setTable()
        
    def setTable(self):
        self.table = QTableWidget(self.numStatParam, 1)
        
        # Forbid user touch anything in the table
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setFocusPolicy(Qt.NoFocus)
        self.table.setSelectionMode(QAbstractItemView.NoSelection)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Fixed)
        self.table.verticalHeader().setSectionResizeMode(QHeaderView.Fixed)
        
        self.table.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)


        self.table.setItemDelegate(Delegate(self.table))

        self.table.setVerticalHeaderLabels(['Total time, s', 'Total distance, cm', 
                                            'Total velocity, cm/s', 'Total rearings'])
        self.table.setHorizontalHeaderLabels(['Whole field'])
        self.table.setStyleSheet('''
                                QTableView {
                                    gridline-color: black;
                                }
                                
                                QHeaderView::section {
                                    padding: 4px;
                                    border-style: none;
                                    border-bottom: 1px solid black;
                                    border-right: 1px solid black;
                                }
                                
                                QHeaderView::section:horizontal {
                                    border-top: 1px solid black;
                                }
                                
                                QHeaderView::section:vertical { 
                                    border-left: 1px solid black; 
                                }
                                
                                QHeaderView::background-color:grey {
                                    background-color: 200, 200, 200, 0,5;
                                }
                                
                                QTableWidget QTableCornerButton::section {
                                    border: 1px solid black;
                                }''')
                                
        # header = QTableWidgetItem()
        # self.table.verticalHeaderItem(3).setBackground(QColor(200, 200, 200, 100))
        # self.table.setVerticalHeaderItem(3, header)
        
        self.table.show()
        self.table.setFixedWidth(self.tableWidth())
        self.adjustSize()
    
    def setSignals(self):
        self.getFileButton.clicked.connect(self.getFile)
        self.addZoneBtn.clicked.connect(self.addNewZone)
        self.saveButton.clicked.connect(self.saveData)
        
        self.areaBtn['Cell'].toggled.connect(self.cellMapButtons)
        self.areaBtn['Vertical_halves'].toggled.connect(self.vHalfArea)
        self.areaBtn['Horizontal_halves'].toggled.connect(self.hHalfArea)
        self.areaBtn['Wall'].toggled.connect(self.wallArea)        
        self.areaBtn['Column'].toggled.connect(self.columnMapButtons)
        self.areaBtn['Row'].toggled.connect(self.rowMapButtons)
        self.areaBtn['Square'].toggled.connect(self.squareMapButtons)
        
        # Check if input is correct
        self.periodLine.textEdited.connect(lambda: self.checkCorrect(self.periodLine, 
                                                                 period=True))
        self.startTime.textEdited.connect(lambda: self.checkCorrect(self.startTime))
        self.endTime.textEdited.connect(lambda: self.checkCorrect(self.endTime))
        
        # Update time range from text
        self.periodLine.editingFinished.connect(self.updatePeriod)
        self.startTime.editingFinished.connect(self.textUpdateTimeRange)
        self.endTime.editingFinished.connect(self.textUpdateTimeRange)
        # Update time range from slider
        self.timeRangeSlider.sliderMoved.connect(self.updateMap)
        self.timeRangeSlider.sliderReleased.connect(self.sliderUpdateTimeRange)  
    
    def setLayouts(self):
        timeRangeLayout = QGridLayout()
        timeRangeLayout.addWidget(self.startTime, 0, 0, Qt.AlignLeft)
        timeRangeLayout.addWidget(self.endTime, 0, 1, Qt.AlignRight)
        timeRangeLayout.addWidget(self.timeRangeSlider, 1, 0, 1, 2, Qt.AlignBottom)
        
        periodLayout = QHBoxLayout()
        periodLayout.addWidget(self.timePeriod, alignment = Qt.AlignRight)
        periodLayout.addWidget(self.periodLine, alignment = Qt.AlignRight)
        periodLayout.addWidget(self.mins, alignment = Qt.AlignRight)
        
        controlLayout = QGridLayout()
        controlLayout.addWidget(self.getFileButton, 0, 0, 1, 1, Qt.AlignLeft)
        controlLayout.addWidget(self.fileName, 1, 0, 1, 2, Qt.AlignTop)
        controlLayout.addWidget(self.addZoneBtn, 2, 0, 1, 2, Qt.AlignRight)
        controlLayout.addLayout(self.areaButtonLayout, 3, 0, 1, 1, Qt.AlignLeft)
        controlLayout.addWidget(self.map, 3, 1, 1, 1, Qt.AlignHCenter)
        controlLayout.addLayout(periodLayout, 4, 0, 1, 2, Qt.AlignRight)
        controlLayout.addLayout(timeRangeLayout, 5, 0, 1, 2, Qt.AlignBottom)
        
        dataLayout = QVBoxLayout()
        dataLayout.addWidget(self.table)
        dataLayout.addWidget(self.saveButton)
        
        generalLayout = QHBoxLayout()
        generalLayout.addLayout(controlLayout)
        generalLayout.addLayout(dataLayout)
        # generalLayout.addWidget(self.table, Qt.AlignCenter)
        # generalLayout.setSizeConstraint(QLayout.SetMinimumSize)
                
        container = QWidget()
        container.setLayout(generalLayout)
        
        self.setCentralWidget(container)
        
    def getFile(self):
        # self.inputFile, _filter = QFileDialog.getOpenFileName(self, 
        #                      'Open .csv file', 
        #                      os.path.join('C:', 'OpenField', 'Data1.csv'), 
        #                      'CSV files (*.csv)')
        file = r"C:\OpenField\Data1.csv"
        self.inputFile = file
        self.fileName.setText(file)           
        self.df = pd.read_csv(file, delimiter=";")
        self.stat = OFStatistics(self.df, self.param) 
        # self.stat = OFStatistics(file)
        self.totalStat()
        self.setTimeRange()
        self.drawPath(0, self.df.index[-1])
        
        # OFStatistics.table() default values
        self.startSelected = 0
        self.endSelected = self.stat.totalTime
        self.period = self.stat.totalTime
        self.numPeriods = 1
        
        self.fillTable()
        self.saveButton.setEnabled(True)
        
    def totalStat(self):
        pass
        # item = QTableWidgetItem(str(self.stat.totalTime))
        # self.table.setItem(0, 0, item)
        # item = QTableWidgetItem(str(self.stat.totalDistance))
        # self.table.setItem(1, 0, item)
        # item = QTableWidgetItem(str(self.stat.totalVelocity))
        # self.table.setItem(2, 0, item)
        # item = QTableWidgetItem(str(self.stat.totalRearings))
        # self.table.setItem(3, 0, item)
        
    def selectedStat(self, start, end):
        n = self.numStatParam
        
        iStart = self.stat.timePoint(self.df, start)
        iEnd = self.stat.timePoint(self.df, end)
        
        if not self.hasSelectedStat:
            headers = ['Selected time, s', 'Selected distance, cm', 
                       'Selected velocity, cm/s', 'Selected rearings']
            headers = list(map(QTableWidgetItem, headers))
            for i in range(n):
                self.table.insertRow(i+n)
                self.table.setVerticalHeaderItem(i+n, headers[i])
        self.hasSelectedStat = True
        
        # item = QTableWidgetItem(f'{start}-{end}')
        # self.table.setItem(n, 0, item)
        
        # selectedDistance = self.stat.calcDistance(self.df, iStart, iEnd)
        # item = QTableWidgetItem(str(selectedDistance))
        # self.table.setItem(n+1, 0, item)   
        
        # selectedVelocity = self.stat.calcVelocity(start, end, selectedDistance)
        # item = QTableWidgetItem(str(selectedVelocity))
        # self.table.setItem(n+2, 0, item)        
        
        # selectedRearings = self.stat.calcRearings(self.df, iStart, iEnd)
        # item = QTableWidgetItem(str(selectedRearings))
        # self.table.setItem(n+3, 0, item)
        
        self.startSelected = start
        self.endSelected = end
        self.fillTable()
        
        self.drawPath(iStart, iEnd)
        
    def setTimeRange(self):
        # slider is sensitive to 0.1 sec
        self.timeRangeSlider.setRange(0, self.stat.totalTime*10)
        self.timeRangeSlider.setValue([0, self.stat.totalTime*10])
        
        self.startTime.setEnabled(True)
        self.endTime.setEnabled(True)
        self.timeRangeSlider.setEnabled(True)
        self.periodLine.setEnabled(True)
        
        self.startTime.setText(str(0))
        self.endTime.setText(str(self.stat.totalTime))
        
    def updatePeriod(self):
        n = self.numStatParam
        self.table.setRowCount(n + n * self.hasSelectedStat)
        
        try:
            self.period = float(self.periodLine.text())
            self.period = round(self.period * 60, 1)  # User enters minutes
        except ValueError:  # Empty line
            self.period = 0
        selectedInterval = round(self.endSelected-self.startSelected, 1)
        if self.period == 0 or self.period == selectedInterval:
            self.period = selectedInterval  # default value
            self.fillTable()
            return
        
        self.numPeriods = m.ceil(selectedInterval / self.period)
        for i in range(self.numPeriods):
            timeStart = round(i * self.period, 1)
            timeEnd = round((i+1) * self.period, 1)
            if timeEnd > self.stat.totalTime:
                timeEnd = self.stat.totalTime
            numRows = self.table.rowCount()
            self.table.setRowCount(numRows+n)
            self.table.setVerticalHeaderItem(numRows, 
                            QTableWidgetItem(f'{timeStart}-{timeEnd} s'))
            self.table.setVerticalHeaderItem(numRows+1, 
                            QTableWidgetItem('Distance, cm'))
            self.table.setVerticalHeaderItem(numRows+2, 
                            QTableWidgetItem('Velocity, cm/s'))
            self.table.setVerticalHeaderItem(numRows+3, 
                            QTableWidgetItem('Rearings'))
            # if (numRows // n) % 2 == 0:
            #     for h in range(n):
            #         self.table.verticalHeaderItem(numRows + h).setBackground(Qt.black)
            
        self.fillTable()
        
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
    def checkCorrect(self, lineEdit, period=False):
        # Not a decimal 
        if not re.match(r'^\d+\.?\d*$', lineEdit.text()):
            lineEdit.backspace()
            return 
        
        # period is in minutes, not seconds
        num = 60*float(lineEdit.text()) if period else float(lineEdit.text())
        
        # Out of total time range
        # No need to check for start < 0, we can't enter negative number
        if num > self.stat.totalTime:
            lineEdit.backspace()
            return
        
        # period > selected time interval
        if period and num > round(self.endSelected-self.startSelected, 1):
            lineEdit.backspace()
            return
        
        # start > end
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
        multiZone = list(map(self.areaBtnNames.__getitem__, [0, 4, 5, 6]))
                    # Those allowing multiple zone selection            
        
        if self.areaBtn[newBtn].isChecked():
            self.checkedAreaBtn = newBtn
            self.mapButtons = []
            self.zoneCoord = np.zeros((self.numLasers, self.numLasers))
            if newBtn not in multiZone:
            # There will be only 2 zones
                self.addNewZone(fillTable=False)
                self.addNewZone(fillTable=False)
                # Will fill table from specific area function,
                # after updating zoneCoord
            [self.areaBtn[key].setDisabled(True) for key in self.areaBtnNames \
                                                         if key != newBtn]
            # if button is checked - disable others
            # if unchecked - enable others  
                
        else:
            # Delete old buttons
            for i in reversed(range(self.mapLayout.count())):
                item = self.mapLayout.itemAt(i).widget()      
                item.deleteLater()
            # and old map buttons' layout
            self.mapLayout.deleteLater()
            
            self.checkedAreaBtn = None
            self.addZoneBtn.setDisabled(True)
            [self.areaBtn[name].setEnabled(True) for name in self.areaBtn]
            # Enable all area buttons 
            
            self.table.setColumnCount(1)
            self.numZones = 0
            self.zoneCoord = np.ones((self.numLasers, self.numLasers)) 
            self.fillTable()
            self.table.setFixedWidth(self.tableWidth())
            delattr(self, 'mapLayout')
            
        # Set Style Sheet for all map buttons
        # with open('ButtonStyleSheet.css') as buttonStyleSheet:
        # self.map.setStyleSheet(buttonStyleSheet.read())
        self.map.setStyleSheet(styleSheet(self.numZones))
            
    @pyqtSlot()    
    def addNewZone(self, fillTable=True):
        if self.numZones == 4:                 # Maximum 4 zones
            return
        self.numZones += 1
        
        # Add new table column
        header = QTableWidgetItem(f'Zone {self.numZones}')
        num = self.table.columnCount()
        self.table.setColumnCount(num+1)
        self.table.setHorizontalHeaderItem(num, header)
        self.table.setFixedWidth(self.tableWidth())
        self.map.setStyleSheet(styleSheet(self.numZones))
        
        self.addZoneBtn.setDisabled(True)
        # We should't be able to add empty zone before we selected some new area
        if fillTable:
            self.fillTable()
        # self.adjustSize()
        
    def mapBtnChecked(self, x=-1, y=-1, s=-1):
        if self.numZones == 4:
            return
        self.addZoneBtn.setEnabled(True)
        # Now that we selected new area we can add it to new zone
        
        if s != -1:  # Square map button
            self.zoneCoord[[s, -s-1], s:self.numLasers-s] = self.numZones + 1
            self.zoneCoord[s:self.numLasers-s, [s, -s-1]] = self.numZones + 1
            self.mapButtons[(coord:=s)].setDisabled(True)
        elif y == -1:  # Row map button
            self.zoneCoord[x,:] = self.numZones + 1
            self.mapButtons[(coord:=x)].setDisabled(True)
        elif x == -1:  # Column map button
            self.zoneCoord[:,y] = self.numZones + 1
            self.mapButtons[(coord:=y)].setDisabled(True)
        else:  # Cell map button
            self.zoneCoord[x][y] = self.numZones + 1
            self.mapButtons[x][y].setEnabled(False)
            self.mapButtons[x][y].setProperty(f'zone{self.numZones}', True)
            self.map.setStyleSheet(styleSheet(self.numZones))
            return
        self.mapButtons[coord].setProperty(f'zone{self.numZones}', True)
        self.map.setStyleSheet(styleSheet(self.numZones))
        
    def cellMapButtons(self):        
        self.newAreaBtn('Cell')
        if not self.areaBtn['Cell'].isChecked():
            return
        
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
                self.mapButtons[i][j].clicked.connect(lambda checked, i=i, j=j: 
                                                      self.mapBtnChecked(x=i, y=j))
                
    def vHalfArea(self):
        self.newAreaBtn('Vertical_halves') 
        if not self.areaBtn['Vertical_halves'].isChecked():
            return
        
        self.mapLayout = QHBoxLayout(self.map)
        self.mapLayout.setSpacing(0)
        self.mapLayout.setContentsMargins(0, 0, 0, 0)
        
        n = self.numLasers
        self.zoneCoord[:, :n//2] = 1
        self.zoneCoord[:, n//2:] = 2
        
        halves = [QPushButton(), QPushButton()]
        for half in halves:
            half.setFixedSize(int(self.mapSide / 2), self.mapSide)
            self.mapLayout.addWidget(half)
        halves[0].setStyleSheet(f"background-color: rgba({color[0]}, 0.3)")
        halves[1].setStyleSheet(f"background-color: rgba({color[1]}, 0.3)")
        
        self.fillTable()
        
    def hHalfArea(self):
        self.newAreaBtn('Horizontal_halves')
        if not self.areaBtn['Horizontal_halves'].isChecked():
            return
        
        self.mapLayout = QVBoxLayout(self.map)
        self.mapLayout.setSpacing(0)
        self.mapLayout.setContentsMargins(0, 0, 0, 0)
        
        n = self.numLasers
        self.zoneCoord[:n//2, :] = 1
        self.zoneCoord[n//2:, :] = 2
        
        halves = [QPushButton(), QPushButton()]
        for half in halves:
            half.setFixedSize(self.mapSide, int(self.mapSide / 2))
            self.mapLayout.addWidget(half)
        halves[0].setStyleSheet(f"background-color: rgba({color[0]}, 0.3)")
        halves[1].setStyleSheet(f"background-color: rgba({color[1]}, 0.3)")
        
        self.fillTable()
    
    def wallArea(self):
        self.newAreaBtn('Wall')
        if not self.areaBtn['Wall'].isChecked():
            return
        
        self.mapLayout = QGridLayout(self.map)
        self.mapLayout.setSpacing(0)
        self.mapLayout.setContentsMargins(0, 0, 0, 0)
        
        n = self.numLasers
        self.zoneCoord = np.ones((n, n))
        self.zoneCoord[n//4 : 3*n//4, n//4 : 3*n//4] = 2
        
        pixmap = QPixmap(os.path.join('Area_pixmaps', 'wall.png'))
        outer = QPushButton()
        outer.setFixedSize(self.mapSide, self.mapSide)
        outer.setMask(pixmap.scaled(outer.size(), Qt.IgnoreAspectRatio).mask())
        outer.setStyleSheet(f"background-color: rgba({color[0]}, 0.3)")
        self.mapLayout.addWidget(outer, 0, 0)
        
        inner = outer = QPushButton()
        inner.setFixedSize(int(self.mapSide / 2), int(self.mapSide / 2))
        inner.setStyleSheet(f"background-color: rgba({color[1]}, 0.3)")
        self.mapLayout.addWidget(inner, 0, 0, alignment = Qt.AlignCenter)
        
        self.fillTable()

    def columnMapButtons(self):      
        self.newAreaBtn('Column')
        if not self.areaBtn['Column'].isChecked():
            return
        
        self.mapLayout = QHBoxLayout(self.map)
        self.mapLayout.setSpacing(0)
        self.mapLayout.setContentsMargins(0, 0, 0, 0)
        
        cell = int(self.mapSide / self.numLasers) # px
        
        for i in range(self.numLasers):
            self.mapButtons.append(QPushButton('', self.map))
            self.mapButtons[i].setFixedSize(cell, self.mapSide)
            self.mapButtons[i].setCheckable(True)
            self.mapLayout.addWidget(self.mapButtons[i])
            self.mapButtons[i].clicked.connect(lambda checked, i=i: 
                                                  self.mapBtnChecked(y=i))
            
    def rowMapButtons(self):      
        self.newAreaBtn('Row')
        if not self.areaBtn['Row'].isChecked():
            return
        
        self.mapLayout = QVBoxLayout(self.map)
        self.mapLayout.setSpacing(0)
        self.mapLayout.setContentsMargins(0, 0, 0, 0)
        
        cell = int(self.mapSide / self.numLasers) # px
        
        for i in range(self.numLasers):
            self.mapButtons.append(QPushButton('', self.map))
            self.mapButtons[i].setFixedSize(self.mapSide, cell)
            self.mapButtons[i].setCheckable(True)
            self.mapLayout.addWidget(self.mapButtons[i])
            self.mapButtons[i].clicked.connect(lambda checked, i=i: 
                                                  self.mapBtnChecked(x=i))
        
    def squareMapButtons(self):
        self.newAreaBtn('Square')
        if not self.areaBtn['Square'].isChecked():
            return
        
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
            self.mapButtons[i].clicked.connect(lambda checked, i=i: 
                                                  self.mapBtnChecked(s=i))
            
    def areaButtons(self):
        self.areaButtonLayout = QVBoxLayout()
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
            # Button is 2px larger than icon, otherwise some icons' pxls are outside
            self.areaBtn[name].setFixedSize(31, 31)
            self.areaButtonLayout.addWidget(self.areaBtn[name])
            self.areaBtn[name].setCheckable(True)

        self.areaButtonLayout.setSpacing(int((self.mapSide - (31 * numAreaBtn)) / \
                                         (numAreaBtn - 1)))
        self.areaButtonLayout.setContentsMargins(0, 0, 30, 0)
                
    def tableWidth(self):
        tableWidth = self.table.verticalHeader().width() + \
                     self.table.horizontalHeader().length() + \
                     self.table.verticalScrollBar().width() + \
                     self.table.frameWidth() * 2
        return tableWidth
    
    def fillTable(self):
        try:
            tableData = self.stat.table(self.zoneCoord, self.startSelected, 
                                        self.endSelected, self.period, 
                                        self.statParam)
        except AttributeError:  # If .csv has not yet been opened
            return
        s = self.hasSelectedStat
        n = self.numStatParam
        
        # Fill Total time statistics
        for zone in range(self.numZones+1):
            for k in range(n):
                key = self.statParam[k]
                val = round(tableData[0][zone][key], 1)
                item = QTableWidgetItem(str(val))
                self.table.setItem(k, zone, item)
                
        # Fill Selected time statistics
        if self.hasSelectedStat:
            for zone in range(self.numZones+1):
                for k in range(n):
                    key = self.statParam[k]
                    val = round(tableData[-1][zone][key], 1)
                    item = QTableWidgetItem(str(val))
                    self.table.setItem(n+k, zone, item)
              
        # Fill Whole field and all zone/period statistics
        for per in range(1, self.numPeriods+1):
            for zone in range(self.numZones+1):
                for k in range(n):
                    key = self.statParam[k]
                    val = round(tableData[per][zone][key], 1)
                    item = QTableWidgetItem(str(val))
                    self.table.setItem(n*(per+s) + k, zone, item)
                                  
    def saveData(self):
        self.outputFile = QFileDialog.getSaveFileName(self, 'Save statistics', 
                          os.path.splitext(self.inputFile)[0]+'_statistics.csv')
        with open(self.outputFile, 'w+') as output:
            writer = csv.writer(output)
            writer.writerow([''] + [f'Zone {x+1}' for x in range(self.numZones)])
            for per in range(self.numPeriods+2):
                for key in range(4):
                    pass
        
class Delegate(QStyledItemDelegate):
    
    def paint(self, painter, option, index):
        super().paint(painter, option, index) 
        if (index.row() // window.numStatParam) % 2 == 1:
            painter.fillRect(option.rect, QColor(200, 200, 200, 120))  
        if index.column() == 1:
            # painter.fillRect(option.rect, Delegate.columnColor[0])
            painter.fillRect(option.rect, QColor(*zoneColors[0], 80))
        if index.column() == 2:
            painter.fillRect(option.rect, QColor(*zoneColors[1], 80))
        if index.column() == 3:
            painter.fillRect(option.rect, QColor(*zoneColors[2], 80))
        if index.column() == 4:
            painter.fillRect(option.rect, QColor(*zoneColors[3], 80))
    
            
app = QApplication(os.sys.argv)
app.setStyle(QStyleFactory.create('Fusion'))
window = MainWindow()
window.show()
app.exec()