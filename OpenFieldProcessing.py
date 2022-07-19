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

from OpenFieldStatistics import OFStatistics

import os
import re
     

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("OpenField processing")
        self.setGeometry(100, 100, 100, 100)
        
        self.numLasers = 16
        self.mapSide = 320 # px
        
        generalLayout = QHBoxLayout()
        controlLayout = QGridLayout()
        timeRangeLayout = QGridLayout()
        dataLayout = QVBoxLayout()
        self.areaButtonLayout = QVBoxLayout()
        
        getFileButton = QPushButton("Select file")
        getFileButton.setFixedWidth(80)
        self.fileName = QLabel()
        
        periodLayout = QHBoxLayout()
        timePeriod = QLabel("Time period every ")
        self.period = QLineEdit(alignment = Qt.AlignRight)
        self.period.setFixedWidth(60)
        mins = QLabel(" min")
        periodLayout.addWidget(timePeriod, alignment = Qt.AlignRight)
        periodLayout.addWidget(self.period, alignment = Qt.AlignRight)
        periodLayout.addWidget(mins, alignment = Qt.AlignRight)
        
        self.numZones = 0
        self.zoneCoord = np.zeros((self.numLasers, self.numLasers))
        self.zoneColors = [QColor(255, 0, 0, 80), QColor(0, 255, 0, 80),
                           QColor(0, 0, 255, 80), QColor(100, 0, 100, 80)]
        
        self.table = QTableWidget(20, 1)
        
        # Forbid user touch anything in the table
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setFocusPolicy(Qt.NoFocus)
        self.table.setSelectionMode(QAbstractItemView.NoSelection)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Fixed)
        self.table.verticalHeader().setSectionResizeMode(QHeaderView.Fixed)
        
        self.table.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        header = QTableWidgetItem()
        header.setBackground(QColor(200, 200, 200, 100))
        self.table.setVerticalHeaderItem(3, header)
        self.table.setItemDelegate(Delegate(self.table))

        self.table.setVerticalHeaderLabels(['Total time, s', 'Total distance, cm', 
                                            'Total velocity, cm/s', 'Total rearings',
                                            'Selected time, s', 'Selected distance, cm', 
                                            'Selected velocity, cm/s', 'Selected rearings'])
        self.table.setHorizontalHeaderLabels(['Whole field'])
        
        self.table.show()
        self.table.setFixedWidth(self.tableWidth())
        self.adjustSize()
        
        self.saveButton = QPushButton('Save data')
        
        # self.table.setHorizontalHeaderItem(1, QTableWidgetItem('new'))
        # self.table.setHorizontalHeader(header)      
        
        # self.totalTime = QLabel("Total time:")
        # self.totalDistance = QLabel("Total distance:") 
        # self.totalVelocity = QLabel("Total velocity:")
        # self.totalRearings = QLabel("Total rearings:")
        
        # self.selectedTime = QLabel("Selected time:")
        # self.selectedDistance = QLabel("Selected distance:")
        # self.selectedVelocity = QLabel("Selected velocity:")
        # self.selectedRearings = QLabel("Selected rearings:")
        
        self.startTime = QLineEdit(alignment = Qt.AlignLeft)
        self.startTime.setFixedWidth(60)
        self.startTime.setDisabled(True)
        self.endTime = QLineEdit(alignment = Qt.AlignRight)
        self.endTime.setFixedWidth(60)
        self.endTime.setDisabled(True)
        self.timeRangeSlider = QRangeSlider(Qt.Horizontal)
        self.timeRangeSlider.setDisabled(True)
        
        self.addZoneBtn = QPushButton('Add zone')
        self.addZoneBtn.setDisabled(True)
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
                
        getFileButton.clicked.connect(self.getFile)
        self.addZoneBtn.clicked.connect(self.addNewZone)
        
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
        
        controlLayout.addWidget(getFileButton, 0, 0, 1, 1, Qt.AlignLeft)
        controlLayout.addWidget(self.fileName, 1, 0, 1, 2, Qt.AlignTop)
        controlLayout.addWidget(self.addZoneBtn, 2, 0, 1, 2, Qt.AlignRight)
        controlLayout.addLayout(self.areaButtonLayout, 3, 0, 1, 1, Qt.AlignLeft)
        controlLayout.addWidget(self.map, 3, 1, 1, 1, Qt.AlignHCenter)
        controlLayout.addLayout(periodLayout, 4, 0, 1, 2, Qt.AlignRight)
        controlLayout.addLayout(timeRangeLayout, 5, 0, 1, 2, Qt.AlignBottom)
        
        # dataLayout.addWidget(self.totalTime)
        # dataLayout.addWidget(self.totalDistance)
        # dataLayout.addWidget(self.totalVelocity)
        # dataLayout.addWidget(self.totalRearings)
        # dataLayout.addSpacing(QFontMetrics(QFont()).height())
        # dataLayout.addWidget(self.selectedTime)
        # dataLayout.addWidget(self.selectedDistance)
        # dataLayout.addWidget(self.selectedVelocity)
        # dataLayout.addWidget(self.selectedRearings)
        
        dataLayout.addWidget(self.table)
        dataLayout.addWidget(self.saveButton)
        
        generalLayout.addLayout(controlLayout)
        generalLayout.addLayout(dataLayout)
        # generalLayout.addWidget(self.table, Qt.AlignCenter)
        # generalLayout.setSizeConstraint(QLayout.SetMinimumSize)
                
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
        # self.totalTime.setText(f"Total time: {self.stat.totalTime} s")
        # self.totalDistance.setText(f"Total distance: {self.stat.totalDistance} cm")
        # self.totalVelocity.setText(f"Total velocity: {self.stat.totalVelocity} cm/s")
        # self.totalRearings.setText(f"Total rearings: {self.stat.totalRearings}")
        
        item = QTableWidgetItem(str(self.stat.totalTime))
        self.table.setItem(0, 0, item)
        item = QTableWidgetItem(str(self.stat.totalDistance))
        self.table.setItem(1, 0, item)
        item = QTableWidgetItem(str(self.stat.totalVelocity))
        self.table.setItem(2, 0, item)
        item = QTableWidgetItem(str(self.stat.totalRearings))
        self.table.setItem(3, 0, item)
        
    def selectedStat(self, start, end):
        iStart = self.stat.timePoint(self.df, start)
        iEnd = self.stat.timePoint(self.df, end)
        
        # self.selectedTime.setText(f"Selected time: {start}-{end} s")
        item = QTableWidgetItem(f'{start}-{end}')
        self.table.setItem(4, 0, item)
        
        selectedDistance = self.stat.calcDistance(self.df, iStart, iEnd)
        item = QTableWidgetItem(str(selectedDistance))
        self.table.setItem(5, 0, item)
        # self.selectedDistance.setText(f"Selected distance: {selectedDistance} cm")
        
        selectedVelocity = self.stat.calcVelocity(start, end, selectedDistance)
        item = QTableWidgetItem(str(selectedVelocity))
        self.table.setItem(6, 0, item)
        # self.selectedVelocity.setText(f"Selected velocity: {selectedVelocity} cm/s")
        
        selectedRearings = self.stat.calcRearings(self.df, iStart, iEnd)
        item = QTableWidgetItem(str(selectedRearings))
        self.table.setItem(7, 0, item)
        # self.selectedRearings.setText(f"Selected rearings: {selectedRearings}")
        
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
        multiZone = list(map(self.areaBtnNames.__getitem__, [0, 4, 5, 6]))
                    # Those allowing multiple zone selection            
        
        if self.areaBtn[newBtn].isChecked():
            self.checkedAreaBtn = newBtn
            self.mapButtons = []
            if newBtn in multiZone:
            # There can be 1-4 zones
                self.addZoneBtn.setEnabled(True)
            else:
            # There will be only 2 zones
                self.addNewZone()
                self.addNewZone()
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
            self.zoneCoord = np.zeros((self.numLasers, self.numLasers))
            self.table.setFixedWidth(self.tableWidth())
            delattr(self, 'mapLayout')
            
        # Set Style Sheet for all map buttons
        with open('ButtonStyleSheet.css') as buttonStyleSheet:
            self.map.setStyleSheet(buttonStyleSheet.read())
            
    def addNewZone(self):
        if self.numZones == 4:                 # Maximum 4 zones
            return
        self.numZones += 1
        header = QTableWidgetItem(f'Zone {self.numZones}')
        num = self.table.columnCount()
        self.table.setColumnCount(num+1)
        self.table.setHorizontalHeaderItem(num, header)
        self.table.setFixedWidth(self.tableWidth())
        # self.adjustSize()
        
    def mapBtnChecked(self, x=-1, y=-1, s=-1):
        if s != -1:
            self.zoneCoord[[s, -s-1], s:self.numLasers-s] = self.numZones + 1
            self.zoneCoord[s:self.numLasers-s, [s, -s-1]] = self.numZones + 1
            self.mapButtons[s].setEnabled(False)
        elif y == -1:
            self.zoneCoord[x,:] = self.numZones + 1
            self.mapButtons[x].setEnabled(False)
        elif x == -1:
            self.zoneCoord[:,y] = self.numZones + 1
            self.mapButtons[y].setEnabled(False)
        else:
            self.zoneCoord[x][y] = self.numZones + 1
            self.mapButtons[x][y].setEnabled(False)
            
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
        halves[0].setStyleSheet("background-color: rgba(255, 0, 0, 0.3)")
        halves[1].setStyleSheet("background-color: rgba(0, 255, 0, 0.3)")
        
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
        halves[0].setStyleSheet("background-color: rgba(255, 0, 0, 0.3)")
        halves[1].setStyleSheet("background-color: rgba(0, 255, 0, 0.3)")
    
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
        outer.setStyleSheet("background-color: rgba(255, 0, 0, 0.3)")
        self.mapLayout.addWidget(outer, 0, 0)
        
        inner = outer = QPushButton()
        inner.setFixedSize(int(self.mapSide / 2), int(self.mapSide / 2))
        inner.setStyleSheet("background-color: rgba(0, 255, 0, 0.3)")
        self.mapLayout.addWidget(inner, 0, 0, alignment = Qt.AlignCenter)

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
            self.areaBtn[name].setFixedSize(32, 32)
            self.areaButtonLayout.addWidget(self.areaBtn[name])
            self.areaBtn[name].setCheckable(True)

        self.areaButtonLayout.setSpacing(int((self.mapSide - (32 * numAreaBtn)) / \
                                         (numAreaBtn - 1)))
        self.areaButtonLayout.setContentsMargins(0, 0, 30, 0)
                
    def tableWidth(self):
        tableWidth = self.table.verticalHeader().width() + \
                     self.table.horizontalHeader().length() + \
                     self.table.verticalScrollBar().width() + \
                     self.table.frameWidth() * 2
        return tableWidth
    
class Delegate(QStyledItemDelegate):
    
    columnColor = [QColor(255, 0, 0, 80), QColor(0, 255, 0, 80),
                   QColor(0, 0, 255, 80), QColor(100, 0, 100, 80)]
    
    def paint(self, painter, option, index):
        super().paint(painter, option, index) 
        if (index.row() // 4) % 2 == 1:
            painter.fillRect(option.rect, QColor(200, 200, 200, 120))  
        if index.column() == 1:
            painter.fillRect(option.rect, Delegate.columnColor[0])
        if index.column() == 2:
            painter.fillRect(option.rect, Delegate.columnColor[1])
        if index.column() == 3:
            painter.fillRect(option.rect, Delegate.columnColor[2])
        if index.column() == 4:
            painter.fillRect(option.rect, Delegate.columnColor[3])
    
            
app = QApplication(os.sys.argv)
app.setStyle(QStyleFactory.create('Fusion'))
window = MainWindow()
window.show()
app.exec()