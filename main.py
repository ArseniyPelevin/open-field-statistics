#!/usr/bin/env python3

import os
import re
import pandas as pd
import numpy as np
import math as m
import csv

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QFileDialog,
    QLabel, QLineEdit, QPushButton, QSpacerItem,
    QVBoxLayout, QHBoxLayout, QGridLayout,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QStyleFactory, QStyledItemDelegate
)
from PyQt6.QtCore import Qt, QSize, pyqtSlot, QEvent
from PyQt6.QtGui import (
    QFontMetrics, QIcon,
    QPen, QPixmap, QPainter, QColor, QPalette
)

from superqt import QRangeSlider

from OpenFieldDataProcessing import DataProcessing
#TODO Expand zoneCoolors to allow more zones
from MapButtonStyleSheet import styleSheet, zoneColors, color


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Open Field Statistics')
        self.setWindowIcon(QIcon('logo.ico'))

        # screen = app.primaryScreen().size()
        # self.setMaximumSize(screen)
        self.setGeometry(100, 100, 100, 100)

        self.setVariables()
        self.setWidgets()
        self.setSignals()
        self.setLayouts()

    def setVariables(self):

        #TODO delete individual parameters to add global settings
        self.params = {'numLasers': 16,     # On one side
                       'mapSide': 320,      # px
                      'boxSide': 40,        # cm
                      'numStatParam': 5}    # Time, distance, velocity,
                                            # rearings number, rearings time
        self.numLasers = self.params['numLasers']
        self.mapSide = self.params['mapSide']
        # self.mapSide = min(self.height(), self.width()/2) * 2/3
        self.numStatParam = self.params['numStatParam']
        self.statParam = ['time', 'dist', 'vel', 'rear', 'rearTime']

        self.zoneCoord = np.ones((self.numLasers, self.numLasers))
        self.numZones = 0

        self.verticalHeaders = ['Time (s)', 'Distance (cm)', 'Velocity (cm/s)',
                                'Rearings number', 'Rearings time (s)']
        self.hasSelectedStat = False

    '''
    def resizeEvent(self, e):
        # try:
            availableHeight = self.height() \
                - sum([self.controlLayout.rowMinimumHeight(row)
                        for row in [0, 1, 4, 5]])
            print(self.controlLayout.rowMinimumHeight(5))
            availableWidth = 600 #self.width() - (self.tableWidth()
                                  # + self.controlLayout.columnMinimumWidth(0))
            self.mapSide = (s := min(availableHeight, availableWidth)) \
                            - (s % self.numLasers)
            self.drawMap()
        except AttributeError:
            raise
    '''


    def setWidgets(self):
        self.getFileButton = QPushButton('Select file')
        self.getFileButton.setFixedWidth(80)
        self.fileNameLabel = QLabel()

        self.startTime = QLineEdit(alignment = Qt.AlignLeft)
        self.startTime.setFixedWidth(60)
        self.startTime.setDisabled(True)
        self.endTime = QLineEdit(alignment = Qt.AlignRight)
        self.endTime.setFixedWidth(60)
        self.endTime.setDisabled(True)
        self.timeRangeSlider = QRangeSlider(Qt.Horizontal)
        self.timeRangeSlider.setDisabled(True)

        self.timePeriod = QLabel('Time period every ')
        self.periodLine = QLineEdit(alignment = Qt.AlignRight)
        self.periodLine.setFixedWidth(60)
        self.periodLine.setDisabled(True)
        self.mins = QLabel(' seconds')

        self.addZoneBtn = QPushButton('Add zone')
        self.addZoneBtn.setFixedWidth(80)
        self.addZoneBtn.setDisabled(True)

        self.saveButton = QPushButton('Save data')
        self.saveButton.setFixedWidth(80)
        self.saveButton.setDisabled(True)

        self.areaButtons()
        self.map = QLabel()
        # self.map.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        self.drawMap()
        self.setTable()

    def setTable(self):
        self.table = QTableWidget(self.numStatParam, 1)

        # Forbid user to touch anything in the table
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setFocusPolicy(Qt.NoFocus)
        self.table.setSelectionMode(QAbstractItemView.NoSelection)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Fixed)
        self.table.verticalHeader().setSectionResizeMode(QHeaderView.Fixed)
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        # Let Delegate control table coloring
        self.table.setItemDelegate(Delegate(self.table, self))

        # Set table headers
        self.table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        headersTotal = [f'Total time, {x}' for x in self.verticalHeaders]
        self.table.setVerticalHeaderLabels(headersTotal)
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

        # self.table.show()
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
        self.periodLine.textEdited.connect(lambda: self.checkCorrect(self.periodLine))
        self.startTime.textEdited.connect(lambda: self.checkCorrect(self.startTime))
        self.endTime.textEdited.connect(lambda: self.checkCorrect(self.endTime))

        # Update period
        self.periodLine.editingFinished.connect(lambda:
                                        self.updatePeriod(isUsersPeriod=True))

        # Update time range from text
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

        self.controlLayout = QGridLayout()
        self.controlLayout.addWidget(self.getFileButton, 0, 0, 1, 1, Qt.AlignLeft)
        self.controlLayout.addWidget(self.fileNameLabel, 0, 1, 1, 2)
        self.controlLayout.addWidget(self.addZoneBtn, 1, 0, 1, 2, Qt.AlignRight)
        self.controlLayout.addLayout(self.areaButtonLayout, 2, 0, 1, 1, Qt.AlignLeft)
        self.controlLayout.addWidget(self.map, 2, 1, 1, 1, Qt.AlignLeft)
        self.controlLayout.addLayout(periodLayout, 4, 0, 1, 2,
                                     (Qt.AlignRight | Qt.AlignBottom))
        self.controlLayout.addLayout(timeRangeLayout, 5, 0, 1, 2, Qt.AlignBottom)

        # Add spacers
        self.controlLayout.addItem(QSpacerItem(0, 0), 0, 2, 5, 1)
        self.controlLayout.setColumnStretch(3, 1)
        self.controlLayout.addItem(QSpacerItem(0, 0), 3, 0, 1, 2)
        self.controlLayout.setRowStretch(3, 1)

        self.dataLayout = QVBoxLayout()
        self.dataLayout.addWidget(self.table)
        self.dataLayout.addWidget(self.saveButton,
                                   alignment=(Qt.AlignmentFlag.AlignRight
                                              | Qt.AlignmentFlag.AlignBottom))

        self.generalLayout = QHBoxLayout()
        self.generalLayout.addLayout(self.controlLayout)
        self.generalLayout.addLayout(self.dataLayout)

        container = QWidget()
        container.setLayout(self.generalLayout)
        self.setCentralWidget(container)

    def getFile(self):
        '''Load raw data file, get statistics, update map and table'''
        #TODO Remember file location
        self.inputFileName, _filter = QFileDialog.getOpenFileName(self,
                              caption='Open .csv file',
                              directory=r'C:\OpenField',
                              filter='CSV files (*.csv)')
        # The extarnal program that generates the raw data saves
        # .csv files to C:\OpenField by default, thus predefined location

        # Create pandas dataframe and process it
        self.csv_df = pd.read_csv(self.inputFileName, delimiter=';')
        self.stat = DataProcessing(self.csv_df, self.params)

        # Update variables
        self.startSelected = 0
        self.endSelected = self.stat.totalTime
        self.period = self.stat.totalTime
        self.numPeriods = 0

        # Set file name label
        metrix = QFontMetrics(self.fileNameLabel.font())
        width = self.fileNameLabel.width() - 2;
        clippedText = metrix.elidedText(self.inputFileName, Qt.ElideMiddle, width)
        self.fileNameLabel.setText(clippedText)

        # Update window
        self.setTimeRange()
        self.drawPath(0, self.stat.data.index[-1])
        self.fillTable()
        self.saveButton.setEnabled(True)

    def selectedStatistics(self, start, end):
        '''
        User can selected a time range within recording time to analyze.
        All statistics will be shown for this range,
        except for Total time statistics
        '''
        n = self.numStatParam

        iStart = self.stat.timeIndex(start)
        iEnd = self.stat.timeIndex(end)

        if start == 0 and end == self.stat.totalTime:
            self.hasSelectedStat = False
        else:
            headersSelected = [QTableWidgetItem(f'Selected time {start}-{end} s,\n{x}')
                               for x in self.verticalHeaders]
            for i in range(n):
                # If there was Selected time statistics before - delete it
                if self.hasSelectedStat:
                    self.table.removeRow(n + i)
                self.table.insertRow(n + i)
                self.table.setVerticalHeaderItem(n + i, headersSelected[i])
            self.hasSelectedStat = True

        self.startSelected = start
        self.endSelected = end
        self.updatePeriod()

        self.drawPath(iStart, iEnd)

    def setTimeRange(self):
        '''Set selected time range based on loaded raw data'''

        sliderStep = 0.1   # Step of selected time range slider in seconds
        self.timeRangeSlider.setRange(0, self.stat.totalTime / sliderStep)
        self.timeRangeSlider.setValue([0, self.stat.totalTime / sliderStep])

        self.startTime.setEnabled(True)
        self.endTime.setEnabled(True)
        self.timeRangeSlider.setEnabled(True)
        self.periodLine.setEnabled(True)

        self.startTime.setText(str(0))
        self.endTime.setText(str(self.stat.totalTime))

    def updatePeriod(self, isUsersPeriod=False):
        '''
        Selected time is split to periods of user-defined length in seconds.
        Statistics for each period (and in each zone) is shown in the table.

        isUserPeriod == True: user defined the period itself
        isUserPeriod == False: the period is defined by Total or Selected time
        '''

        n = self.numStatParam
        self.table.setRowCount(n + n * self.hasSelectedStat)
        # Period statistics goes after Total time and Selected time in table

        try:
            self.period = float(self.periodLine.text())
        except ValueError:  # Empty line
            self.period = 0
        selectedInterval = round(self.endSelected-self.startSelected, 1)
        # Period is not defined
        if self.period == 0 or self.period >= selectedInterval \
                            or not isUsersPeriod:
            self.period = selectedInterval  # Default value
            self.periodLine.setText('')
            isUsersPeriod = False
            self.numPeriods = 0
            self.periodTimes = []
            self.fillTable()
            return

        self.numPeriods = m.ceil(selectedInterval / self.period)
        self.periodTimes = []   # Start and end of each period
                                # ! relative to Selected time !
        for i in range(self.numPeriods):
            timeStart = round(i * self.period, 1)
            timeEnd = round((i+1) * self.period, 1)
            if timeEnd > selectedInterval:
                timeEnd = selectedInterval
            self.periodTimes.append((timeStart, timeEnd))
            numRows = self.table.rowCount()
            self.table.setRowCount(numRows+n)
            # For each period add empty rows for its statistics in table
            for j in range(n):
                self.table.setVerticalHeaderItem(numRows + j,
                    QTableWidgetItem(f'{timeStart}-{timeEnd} s, '
                                     + f'{self.verticalHeaders[j]}'))

        self.fillTable()

    def sliderUpdateTimeRange(self):
        start, end = [x/10 for x in self.timeRangeSlider.value()]

        # Update values in text editors based on slider
        self.startTime.setText(str(start))
        self.endTime.setText(str(end))

        self.selectedStatistics(start, end)

    def textUpdateTimeRange(self):
        # If start time is empty - set start to 0
        try:
            start = float(self.startTime.text())
        except ValueError:  # Empty line
            start = 0
            self.startTime.setText(str(0))

        # If end time is empty - set end to max time
        try:
            end = float(self.endTime.text())
        except ValueError:  # Empty line
            end = self.stat.totalTime
            self.endTime.setText(str(self.stat.totalTime))

        # Update slider values based on text editors
        self.timeRangeSlider.setValue([start*10, end*10])

        self.selectedStatistics(start, end)

    def checkCorrect(self, lineEdit):
        '''
        Check if time range and period inputs are correct,
        delete last input char otherwise.

        lineEdit: the QLineEdit widget, which is being checked here
        period == True: if called from period edit
        period == False: if called from Selected time edit
        '''

        # Not a decimal
        if not re.match(r'^\d+\.?\d*$', lineEdit.text()):
            lineEdit.backspace()
            return

        inputValue = float(lineEdit.text())

        # Out of total time range
        # No need to check for start < 0, we can not enter negative numbers
        if inputValue > self.stat.totalTime:
            lineEdit.backspace()
            return

        # period > selected time interval
        if (lineEdit is self.periodLine
            and inputValue > round(self.endSelected-self.startSelected, 1)):
        # if period > round(self.endSelected-self.startSelected, 1):
            lineEdit.backspace()
            return

        # start >= end in Selected time
        if not float(self.startTime.text()) < float(self.endTime.text()):
            lineEdit.backspace()
            return

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

    def updateMap(self):
        start, end = [x/10 for x in self.timeRangeSlider.value()]

        # Update values in text editors based on slider
        self.startTime.setText(str(start))
        self.endTime.setText(str(end))

        iStart = self.stat.timeIndex(start)
        iEnd = self.stat.timeIndex(end)
        self.drawPath(iStart, iEnd)

    #OPTIMIZE
    def drawPath(self, iStart, iEnd):
        cell, canvas = self.drawMap()
        painter = QPainter(canvas)
        painter.setPen(QPen(Qt.red, 2))
        lastX, lastY = 0, 0
        for i, row in self.stat.data.iloc[iStart:iEnd, :].iterrows():
            if not lastX:
                lastX = int(row['x'] * cell - cell / 2)
                lastY = int(row['y'] * cell - cell / 2)
                continue
            x = int(row['x'] * cell - cell / 2)
            y = int(row['y'] * cell - cell / 2)
            painter.drawLine(lastX, lastY, x, y)
            lastX = x
            lastY = y

        painter.end()
        self.map.setPixmap(canvas)

    def newAreaBtn(self, newBtn):
        '''
        Actions when an area type button is checked or unchecked.

        There are 3 area types with predefined zones:
            - two vertical halves (vHalfArea)
            - two horizontal halves (hHalfArea)
            - walls and center (wallArea)

        There are 4 area types that support custom number and location of zones:
            - cell - one laser intersection
            - column
            - row
            - concentric square
        They are realized with checkable map buttons of corresponding shapes
        '''

        # List of area types allowing for multiple zone selection
        multiZone = list(map(self.areaBtnNames.__getitem__, [0, 4, 5, 6]))

        if self.areaBtn[newBtn].isChecked():
            self.checkedAreaBtn = newBtn
            # Define new empty list for map buttons
            self.mapButtons = []
            self.zoneCoord = np.zeros((self.numLasers, self.numLasers))
            if newBtn not in multiZone:
            # There will be only 2 zones
                self.addNewZone(fillTable=False, numNewZones=2)
                # Do not fill table now.
                # It will be updated from specific area type function,
                # after zoneCoord is updated.

            # Disable all other area type buttons except for the checked one
            [self.areaBtn[key].setDisabled(True) for key in self.areaBtnNames \
                                                         if key != newBtn]

        else:  # Area type button is unchecked
            # Delete old map buttons
            for i in reversed(range(self.mapLayout.count())):
                item = self.mapLayout.itemAt(i).widget()
                item.deleteLater()
            # Delete old map buttons' layout
            self.mapLayout.deleteLater()

            self.checkedAreaBtn = None
            self.addZoneBtn.setDisabled(True)

            # Enable all area buttons
            [self.areaBtn[name].setEnabled(True) for name in self.areaBtn]

            self.table.setColumnCount(1)
            self.numZones = 0
            self.zoneCoord = np.ones((self.numLasers, self.numLasers))
            self.fillTable()
            self.table.setFixedWidth(self.tableWidth())
            delattr(self, 'mapLayout')

        # Set style sheet for all map buttons
        self.map.setStyleSheet(styleSheet(self.numZones))

    @pyqtSlot()
    def addNewZone(self, fillTable=True, numNewZones=1):
        '''
        Add a new zone to map and table from two sources:
            - user-defined area with map buttons:
                fillTable=True, numNewZones=1
            - two predefined areas:
                fillTable=False, numNewZones=2
        '''

        for i in range(numNewZones):

            #TODO To make more zones delete it
            if self.numZones == 4:                 # Maximum 4 zones
                return
            self.numZones += 1

            # Add new table column
            header = QTableWidgetItem(f'Zone {self.numZones}')
            num = self.table.columnCount()
            self.table.setColumnCount(num + 1)
            self.table.setHorizontalHeaderItem(num, header)
            self.table.setFixedWidth(self.tableWidth())
            # app.processEvents()
            # self.adjustSize()

            # Show the new zone on map with a new color
            self.map.setStyleSheet(styleSheet(self.numZones))

        # Do not allow to add empty zone before a new area is selected
        self.addZoneBtn.setDisabled(True)

        if fillTable:
            self.fillTable()
        # self.adjustSize()

    def mapBtnChecked(self, x=-1, y=-1, s=-1):
        '''
        Actions when a map button was checked (add area for a new zone).

        Signals are defined in each area type method
        '''

        #TODO To make more zones delete it
        if self.numZones == 4:
            return

        # Allow to add a new zone after some area was selected
        self.addZoneBtn.setEnabled(True)

        # Depending on the area type, self.mapButtons (list of map buttons)
        # has different shape and indexing:
        if s != -1:     # Square map button
            self.zoneCoord[[s, -s-1], s:self.numLasers-s] = self.numZones + 1
            self.zoneCoord[s:self.numLasers-s, [s, -s-1]] = self.numZones + 1
            self.mapButtons[(coord:=s)].setDisabled(True)
        elif y == -1:   # Row map button
            self.zoneCoord[x,:] = self.numZones + 1
            self.mapButtons[(coord:=x)].setDisabled(True)
        elif x == -1:   # Column map button
            self.zoneCoord[:,y] = self.numZones + 1
            self.mapButtons[(coord:=y)].setDisabled(True)
        else:           # Cell map button
            self.zoneCoord[x][y] = self.numZones + 1
            self.mapButtons[x][y].setDisabled(True)
            self.mapButtons[x][y].setProperty(f'zone{self.numZones}', True)
            self.map.setStyleSheet(styleSheet(self.numZones))
            return

        # Property of the button (the number of zone it belongs to)
        # defines its color according the style sheet
        self.mapButtons[coord].setProperty(f'zone{self.numZones}', True)

        # Define color for this new area
        self.map.setStyleSheet(styleSheet(self.numZones))

    def cellMapButtons(self):
        '''One cell map button, corresponds to one laser intersection'''

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
        '''Split box vertically into two halves'''

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
        halves[0].setStyleSheet(f'background-color: rgba({color[0]}, 0.3)')
        halves[1].setStyleSheet(f'background-color: rgba({color[1]}, 0.3)')

        self.fillTable()

    def hHalfArea(self):
        '''Split box horizontally into two halves'''

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
        halves[0].setStyleSheet(f'background-color: rgba({color[0]}, 0.3)')
        halves[1].setStyleSheet(f'background-color: rgba({color[1]}, 0.3)')

        self.fillTable()

    def wallArea(self):
        '''Split box into central and peripheral zones'''

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
        outer.setStyleSheet(f'background-color: rgba({color[0]}, 0.3)')
        self.mapLayout.addWidget(outer, 0, 0)

        inner = outer = QPushButton()
        inner.setFixedSize(int(self.mapSide / 2), int(self.mapSide / 2))
        inner.setStyleSheet(f'background-color: rgba({color[1]}, 0.3)')
        self.mapLayout.addWidget(inner, 0, 0, alignment = Qt.AlignCenter)

        self.fillTable()

    def columnMapButtons(self):
        '''Map buttons are vertical columns'''

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
        '''Map buttons are horizontal rows'''

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
        '''Map buttons are concentric squares'''

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

#TODO Add sys._MEIPASS here to package into one file
            pixmap = QPixmap(os.path.join('Area_pixmaps', f'{i+1}.png'))
            self.mapButtons[i].setMask(pixmap.scaled(self.mapButtons[i].size(),
                                                    Qt.IgnoreAspectRatio).mask())
            self.mapLayout.addWidget(self.mapButtons[i], 0, 0)
            self.mapButtons[i].clicked.connect(lambda checked, i=i:
                                                  self.mapBtnChecked(s=i))

    def areaButtons(self):
        '''Area types buttons, arranged vertically to the left of the map'''

        self.areaButtonLayout = QVBoxLayout()
        self.areaBtnNames = ['Cell', 'Vertical_halves', 'Horizontal_halves',
                             'Wall', 'Column', 'Row', 'Square']
        self.areaBtn = {}
        numAreaBtn = 7
        for i in range(numAreaBtn):
            name = self.areaBtnNames[i]
            self.areaBtn[name] = QPushButton()

#TODO Add sys._MEIPASS here to package into one file
            pixmap = QPixmap(os.path.join('Area_Buttons_pixmaps',
                                  self.areaBtnNames[i] + '.png'))

            self.areaBtn[name].setIcon(QIcon(pixmap))
            self.areaBtn[name].setIconSize(QSize(30, 30))
            self.areaBtn[name].setFixedSize(30, 30)
            self.areaButtonLayout.addWidget(self.areaBtn[name])
            self.areaBtn[name].setCheckable(True)

        self.areaButtonLayout.setSpacing(int((self.mapSide - (30 * numAreaBtn)) /
                                         (numAreaBtn - 1)))
        # self.areaButtonLayout.setContentsMargins(0, 0, 30, 0)

    def tableWidth(self):
        app.processEvents()
        app.processEvents()
        tableWidth = self.table.verticalHeader().width() + \
                     self.table.horizontalHeader().length() + \
                     self.table.frameWidth() * 2
        if self.table.verticalScrollBar().isVisible():
            tableWidth += self.table.verticalScrollBar().width()

        return tableWidth

    def tableHeight(self):
        tableHeight = self.table.verticalHeader().length() + \
                      self.table.horizontalHeader().height() + \
                      self.table.frameWidth() * 2
        return tableHeight

    def fillTable(self):
        '''Fill table with statistics'''

        # Adjust table width to contents
        self.table.setFixedWidth(self.tableWidth())
        # Adjust window width to table
        app.processEvents()
        self.adjustSize()

        try:
            self.tableData = self.stat.table(self.zoneCoord, self.startSelected,
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
                val = round(self.tableData[0][zone][key], 1)
                item = QTableWidgetItem(str(val))
                self.table.setItem(k, zone, item)

        # Fill Selected time statistics
        if self.hasSelectedStat:
            for zone in range(self.numZones+1):
                for k in range(n):
                    key = self.statParam[k]
                    val = round(self.tableData[-1][zone][key], 1)
                    item = QTableWidgetItem(str(val))
                    self.table.setItem(n+k, zone, item)

        # Fill Periods statistics
        if self.numPeriods != 0:
            for per in range(1, self.numPeriods+1):
                for zone in range(self.numZones+1):
                    for k in range(n):
                        key = self.statParam[k]
                        val = round(self.tableData[per][zone][key], 1)
                        item = QTableWidgetItem(str(val))
                        self.table.setItem(n*(per+s) + k, zone, item)

    def saveData(self):
        self.outputFile, _filter = QFileDialog.getSaveFileName(self, 'Save statistics',
                          os.path.splitext(self.inputFileName)[0]+'_statistics.csv')
        with open(self.outputFile, 'w+', newline='') as output:
            writer = csv.writer(output, delimiter=';')
            writer.writerow(['sep=;'])

            n = self.numStatParam

            # Write horizontal header
            writer.writerow(['', '', 'Whole field']
                            + [f'Zone {x+1}' for x in range(self.numZones)])

            # Write Total time statistics
            for k in range(n):
                key = self.statParam[k]
                writer.writerow(['Total time', f'{self.verticalHeaders[k]}']
                                + [round(self.tableData[0][zone][key], 1)
                                 for zone in range(self.numZones+1)])

            # Write Selected time statistics
            if self.hasSelectedStat:
                for k in range(n):
                        key = self.statParam[k]
                        writer.writerow([
                    f'Selected time {self.startSelected}-{self.endSelected} s',
                    f'{self.verticalHeaders[k]}']
                    + [round(self.tableData[-1][zone][key], 1)
                       for zone in range(self.numZones+1)])

            # Write Periods statistics
            if self.numPeriods != 0:
                for per in range(self.numPeriods):
                    for k in range(n):
                        key = self.statParam[k]
                        start = self.periodTimes[per][0]
                        end = self.periodTimes[per][1]
                        writer.writerow([f'{start}-{end} s',
                                         f'{self.verticalHeaders[k]}']
                                        + [round(self.tableData[per+1][zone][key], 1)
                                           for zone in range(self.numZones+1)])

class Delegate(QStyledItemDelegate):
    def __init__ (self, parent, mywindow):
        super ().__init__ (parent)
        self.mywindow = mywindow

    def paint(self, painter, option, index):
        super().paint(painter, option, index)

        # Overlap of colored zone and grey even block
        if index.column() != 0 and \
           (index.row() // mywindow.numStatParam) % 2 == 1:
            color = self.overlap(np.array([120, 120, 120, 120]),
                            np.array([*zoneColors[index.column()-1], 80]))
        # Colored zone
        elif index.column() != 0:
            color = (*zoneColors[index.column()-1], 80)

        # Grey even block
        elif (index.row() // mywindow.numStatParam) % 2 == 1:
                color = (200, 200, 200, 120)

        try:
            index.model().setData(index, QColor(*color),
                                  Qt.BackgroundColorRole)
            option.palette.setColor(QPalette.Base,
                                    index.data(Qt.BackgroundColorRole))
        except UnboundLocalError:  # A white cell, no color was set
            pass

    def overlap(self, bg, fg):
        bga = bg[3] / 255
        fga = fg[3] / 255
        bg = bg[:3] / 255
        fg = fg[:3] / 255
        a = 1 - (1 - bga) * (1 - fga)
        color = fg * fga / a + bg * bga * (1 - fga) / a
        return map(int, [*(color * 255), a * 255])


if __name__ == '__main__':
    app = QApplication(os.sys.argv)
    app.setStyle(QStyleFactory.create('Fusion'))
    mywindow = MainWindow()
    mywindow.show()
    app.exec()
