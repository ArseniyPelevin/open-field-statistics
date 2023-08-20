#!/usr/bin/env python3

import os
import pandas as pd
import numpy as np
import math as m
import csv
import inspect

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QFileDialog, QToolTip,
    QLabel, QLineEdit, QPushButton, QButtonGroup, QSpacerItem,
    QVBoxLayout, QHBoxLayout, QGridLayout, QStackedLayout,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QStyleFactory, QStyledItemDelegate, QWidgetItem
)
from PyQt6.QtCore import (Qt, QSize, pyqtSlot, QEvent, QPointF,
                          QVariantAnimation, QRegularExpression)
from PyQt6.QtGui import (
    QFontMetrics, QIcon,
    QPen, QPixmap, QPainter, QColor, QPalette, QRegularExpressionValidator
)

from superqt import QRangeSlider

from OpenFieldDataProcessing import DataProcessing
#TODO Expand zoneCoolors to allow more zones
from MapButtonStyleSheet import styleSheet, zoneColors# , color


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
        print(inspect.currentframe().f_code.co_name)

        #TODO delete individual parameters to add global settings
        self.params = {'numLasers': 16,     # On one side
                       'mapSide': 320,      # px
                      'boxSide': 40,        # cm
                      'numStatParam': 5}    # Time, distance, velocity,
                                            # rearings number, rearings time
        self.numLasers = self.params['numLasers']
        self.mapSide = self.params['mapSide']
        self.cell = self.mapSide // self.numLasers
        # self.mapSide = min(self.height(), self.width()/2) * 2/3
        self.numStatParam = self.params['numStatParam']
        self.statParam = ['time', 'dist', 'vel', 'rear', 'rearTime']

        self.zoneCoord = np.zeros((self.numLasers, self.numLasers), dtype=int)
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
        print(inspect.currentframe().f_code.co_name)

        self.getFileButton = QPushButton('Select file')
        self.getFileButton.setFixedWidth(80)
        self.fileNameLabel = QLabel()

        self.startTime = QLineEdit(alignment = Qt.AlignLeft)
        self.startTime.setFixedWidth(60)
        self.startTime.setDisabled(True)
        self.endTime = QLineEdit(alignment = Qt.AlignRight)
        self.endTime.setFixedWidth(60)
        self.endTime.setDisabled(True)
        self.selectedTimeLabel = QLabel()
        self.timeRangeSlider = QRangeSlider(Qt.Horizontal)
        self.timeRangeSlider.setDisabled(True)

        self.timePeriod = QLabel('Time period every ')
        self.periodLine = QLineEdit(alignment = Qt.AlignRight)
        self.periodLine.setFixedWidth(60)
        self.periodLine.setDisabled(True)
        # Default LineEdit background will be needed for error warning
        self.defaultLineEditBackground = self.periodLine.palette().color(
                                         QPalette.Active, QPalette.Base)
        #???
        self.mins = QLabel(' seconds')

        self.addZoneBtn = QPushButton('Add zone')
        self.addZoneBtn.setFixedWidth(80)
        self.addZoneBtn.setDisabled(True)

        self.saveButton = QPushButton('Save data')
        self.saveButton.setFixedWidth(80)
        self.saveButton.setDisabled(True)

        # Set input validator
        rx = QRegularExpression(r'^\d+\.?\d*$')  # float
        inputValidator = QRegularExpressionValidator(rx)
        self.periodLine.setValidator(inputValidator)
        self.startTime.setValidator(inputValidator)
        self.endTime.setValidator(inputValidator)

        self.map = QLabel()
        self.defineAreaTypes()
        # self.map.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        self.drawMap()
        self.setTable()

    def setTable(self):
        print(inspect.currentframe().f_code.co_name)

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

                                QHeaderView::background-color:gray {
                                    background-color: 200, 200, 200, 0,5;
                                }

                                QTableWidget QTableCornerButton::section {
                                    border: 1px solid black;
                                }''')

        # self.table.show()
        self.table.setFixedWidth(self.tableWidth())
        self.adjustSize()

    def setSignals(self):
        print(inspect.currentframe().f_code.co_name)

        self.getFileButton.clicked.connect(self.getFile)
        self.addZoneBtn.clicked.connect(self.addNewZone)
        self.saveButton.clicked.connect(self.saveData)

        self.areaBtnGroup.idToggled.connect(self.newAreaButton)
        # Update period
        self.periodLine.editingFinished.connect(self.checkPeriodValue)

        # Update time range from text
        self.startTime.editingFinished.connect(self.checkStartTimeValue)
        self.endTime.editingFinished.connect(self.checkEndTimeValue)

        # Update time range from slider
        self.timeRangeSlider.sliderMoved.connect(self.sliderUpdateMapPath)
        self.timeRangeSlider.sliderReleased.connect(self.sliderUpdateTimeRange)

    def setLayouts(self):
        print(inspect.currentframe().f_code.co_name)

        timeRangeLayout = QGridLayout()
        timeRangeLayout.addWidget(self.startTime, 0, 0, Qt.AlignLeft)
        timeRangeLayout.addWidget(self.selectedTimeLabel, 0, 1, Qt.AlignCenter)
        timeRangeLayout.addWidget(self.endTime, 0, 2, Qt.AlignRight)
        timeRangeLayout.addWidget(self.timeRangeSlider, 1, 0, 1, 3, Qt.AlignBottom)

        periodLayout = QHBoxLayout()
        periodLayout.addWidget(self.timePeriod, alignment = Qt.AlignRight)
        periodLayout.addWidget(self.periodLine, alignment = Qt.AlignRight)
        periodLayout.addWidget(self.mins, alignment = Qt.AlignRight)

        self.controlLayout = QGridLayout()
        self.controlLayout.addWidget(self.getFileButton, 0, 0, 1, 1, Qt.AlignLeft)
        self.controlLayout.addWidget(self.fileNameLabel, 0, 1, 1, 2)
        self.controlLayout.addWidget(self.addZoneBtn, 1, 0, 1, 2, Qt.AlignRight)
        self.controlLayout.addLayout(self.areaBtnLayout, 2, 0, 1, 1, Qt.AlignLeft)
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
        print(inspect.currentframe().f_code.co_name)

        ''' Load raw data file, get statistics, update map and table '''

        #TODO Remember file location
        self.inputFileName, _filter = QFileDialog.getOpenFileName(self,
                              caption='Open .csv file',
                              directory=r'C:\OpenField',
                              filter='CSV files (*.csv)')
        # The extarnal program that generates the raw data saves
        # .csv files to C:\OpenField by default, thus predefined location

        # Create pandas dataframe and process it
        try:
            self.csv_df = pd.read_csv(self.inputFileName, delimiter=';')
        except FileNotFoundError:
            return

        self.stat = DataProcessing(self.csv_df, self.params)

        # Update variables
        self.startSelected = 0
        self.endSelected = self.stat.totalTime
        self.selectedTime = self.endSelected
        self.selectedTimeLabel.setText(f'Selected time: {self.selectedTime} seconds')
        self.period = self.stat.totalTime
        self.numPeriods = 0

        # Set file name label
        metrix = QFontMetrics(self.fileNameLabel.font())
        width = self.fileNameLabel.width() - 2;
        clippedText = metrix.elidedText(self.inputFileName, Qt.ElideMiddle, width)
        self.fileNameLabel.setText(clippedText)

        # Make path for visualization
        self.pathPoints = []
        for _, row in self.stat.data.iterrows():
            x = int(row['x'] * self.cell - self.cell / 2)
            y = int(row['y'] * self.cell - self.cell / 2)
            self.pathPoints.append(QPointF(x, y))
        self.pathPoints = np.array(self.pathPoints)

        # Update window
        self.setTimeRange()
        self.updateMapPath(0, self.stat.data.index[-1])
        self.fillTable()
        self.saveButton.setEnabled(True)

    def selectedStatistics(self, start, end):
        print(inspect.currentframe().f_code.co_name)

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
        self.selectedTime = round(self.endSelected - self.startSelected, 1)
        self.selectedTimeLabel.setText(f'Selected time: {self.selectedTime} seconds')
        self.updatePeriod()

        self.updateMapPath(iStart, iEnd)

    def setTimeRange(self):
        print(inspect.currentframe().f_code.co_name)

        ''' Set selected time range based on loaded raw data '''

        sliderStep = 0.1   # Step of selected time range slider in seconds
        self.timeRangeSlider.setRange(0, self.stat.totalTime / sliderStep)
        self.timeRangeSlider.setValue([0, self.stat.totalTime / sliderStep])

        self.startTime.setEnabled(True)
        self.endTime.setEnabled(True)
        self.timeRangeSlider.setEnabled(True)
        self.periodLine.setEnabled(True)

        self.startTime.setText(str(0))
        self.endTime.setText(str(self.stat.totalTime))

    def updatePeriod(self, period=0, isUsersPeriod=False):
        print(inspect.currentframe().f_code.co_name)

        '''
        Selected time is split to periods of user-defined length in seconds.
        Statistics for each period (and in each zone) is shown in the table.

        isUserPeriod == True: user defined the period itself
        isUserPeriod == False: the period is defined by Total or Selected time
        '''

        # Period statistics goes after Total time and Selected time in table
        n = self.numStatParam
        self.table.setRowCount(n + n * self.hasSelectedStat)

        # Period is not defined
        if period == 0 or period == self.selectedTime or not isUsersPeriod:
            self.period = self.selectedTime  # Default value
            self.periodLine.setText('')
            self.numPeriods = 0
            self.periodTimes = []
            self.fillTable()
            return

        self.period = period
        self.numPeriods = m.ceil(self.selectedTime / self.period)
        self.periodTimes = []   # Start and end of each period
                                # ! relative to Selected time !
        for i in range(self.numPeriods):
            timeStart = round(i * self.period, 1)
            timeEnd = round((i+1) * self.period, 1)
            if timeEnd > self.selectedTime:
                timeEnd = self.selectedTime
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
        print(inspect.currentframe().f_code.co_name)

        start, end = [x/10 for x in self.timeRangeSlider.value()]

        # Update values in text editors based on slider
        self.startTime.setText(str(start))
        self.endTime.setText(str(end))

        self.selectedStatistics(start, end)

    def textUpdateTimeRange(self, start, end):
        print(inspect.currentframe().f_code.co_name)

        # Update slider values based on text editors
        self.timeRangeSlider.setValue([start*10, end*10])
        self.selectedStatistics(start, end)

    def errorWarning(self, widget, errorMessage=''):
        print(inspect.currentframe().f_code.co_name)

        ''' Flash red in the field with an error '''

        def updateColor(w):
            # Calculate weighted average with changing weight ratio
            nextColor = np.average(colors, axis=0, weights=(w, 1-w))
            nextColor = QColor(*nextColor.astype(int).tolist())

            palette.setColor(QPalette.Active, QPalette.Base, nextColor)
            widget.setPalette(palette)

        palette = QPalette()

        # Start from red and average it to the default background over a second
        defaultColor = self.defaultLineEditBackground
        warningColor = QColor(Qt.red)
        colors = np.zeros((2, 4))
        colors[0] = defaultColor.getRgb()
        colors[1] = warningColor.getRgb()

        # Variant animation over ratio between default and warning colors
        self.animation = QVariantAnimation()
        self.animation.setDuration(1000)
        self.animation.setStartValue(0.)
        self.animation.setEndValue(1.)

        self.animation.valueChanged.connect(updateColor)
        self.animation.start()

        # Show a tooltip explaining the error
        QToolTip.showText(self.mapToGlobal(widget.pos()), errorMessage, widget)

    def checkPeriodValue(self):
        print(inspect.currentframe().f_code.co_name)

        try:
            period = float(self.periodLine.text())
        # Empty line was entered
        except ValueError:
            period = 0
        else:
            if period > self.selectedTime:
                errorMessage = ('Period should be in the range:\n'
                                + f'0 < period < {self.selectedTime}')
                self.errorWarning(self.periodLine, errorMessage)
                period = self.selectedTime

        self.updatePeriod(period, isUsersPeriod=True)

    def checkStartTimeValue(self):
        print(inspect.currentframe().f_code.co_name)

        try:
            start = float(self.startTime.text())
        # Empty line was entered as start time, set start to 0
        except ValueError:
            start = 0
            self.startTime.setText(str(start))
        else:
            # Selected start > Selected end, back to initial value
            if start >= self.endSelected:
                errorMessage = ('Start time should be in the range:\n'
                                + f'0 <= start time < {self.endSelected}')
                self.errorWarning(self.startTime, errorMessage)

                start = self.startSelected
                self.startTime.setText(str(start))

        self.textUpdateTimeRange(start, self.endSelected)

    def checkEndTimeValue(self):
        print(inspect.currentframe().f_code.co_name)

        try:
            end = float(self.endTime.text())
        # Empty line was entered as end time, set end to max total time
        except ValueError:
            end = self.stat.totalTime
            self.endTime.setText(str(end))
        else:
            errorMessage = ('End time should be in the range:\n'
                            + f'{self.startSelected} < end time <= {self.stat.totalTime}')

            # Selected end < Selected start, back to previous value
            if end <= self.startSelected:
                self.errorWarning(self.endTime, errorMessage)

                end = self.endSelected
                self.endTime.setText(str(end))

            # Selected end > total time, set Selected time to max total time
            elif end > self.stat.totalTime:
                self.errorWarning(self.endTime, errorMessage)

                end = self.stat.totalTime
                self.endTime.setText(str(end))

        self.textUpdateTimeRange(self.startSelected, end)

    def drawMap(self):
        print(inspect.currentframe().f_code.co_name)

        ''' Create empty map '''

        self.mapCanvas = QPixmap(self.mapSide + 1, self.mapSide + 1)

        # Define separate layers for grid, zone colors and path
        self.gridLayer = QPixmap(self.mapSide + 1, self.mapSide + 1)
        self.zoneLayer = QPixmap(self.mapSide + 1, self.mapSide + 1)
        self.pathLayer = QPixmap(self.mapSide + 1, self.mapSide + 1)

        self.gridLayer.fill()
        self.zoneLayer.fill(Qt.transparent)
        self.pathLayer.fill(Qt.transparent)

        gridPainter = QPainter(self.gridLayer)

        # Draw grid
        for i in range(self.numLasers + 1): #TODO add second loop for rectangle field
            step = self.cell * i
            gridPainter.drawLine(0, step, self.mapSide, step)
            gridPainter.drawLine(step, 0, step, self.mapSide)

        gridPainter.end()

        self.updateMap()

        self.map.setStyleSheet(styleSheet(self.numZones))

    def updateMap(self):
        print(inspect.currentframe().f_code.co_name)

        ''' Add Zone and Path layers to the map widget '''

        mapPainter = QPainter(self.mapCanvas)

        mapPainter.drawPixmap(0, 0, self.gridLayer)
        mapPainter.drawPixmap(0, 0, self.zoneLayer)
        mapPainter.drawPixmap(0, 0, self.pathLayer)

        mapPainter.end()

        self.map.setPixmap(self.mapCanvas)

    def updateMapZones(self):
        print(inspect.currentframe().f_code.co_name)

        ''' Update map area coloring based on zone selection '''

        self.zoneLayer.fill(Qt.transparent)

        zonePainter = QPainter(self.zoneLayer)

        # Fill cells with color
        for i in range(self.numLasers):
            for j in range(self.numLasers):
                zone = self.zoneCoord[i][j]
                zoneColor = QColor(*zoneColors[zone], int(0.3*255))
                zonePainter.setBrush(zoneColor)
                x = self.cell * j
                y = self.cell * i
                zonePainter.drawRect(x, y, self.cell, self.cell)

        zonePainter.end()

        self.updateMap()

    def updateMapPath(self, iStart, iEnd):
        print(inspect.currentframe().f_code.co_name)

        ''' Draw path in Selected time '''

        self.pathLayer.fill(Qt.transparent)

        pathPainter = QPainter(self.pathLayer)

        pathPainter.setPen(QPen(Qt.red, 2))
        pathPainter.drawPolyline(self.pathPoints[iStart:iEnd])

        pathPainter.end()

        self.updateMap()

    def sliderUpdateMapPath(self):
        print(inspect.currentframe().f_code.co_name)

        ''' Update path while Selected time slider is being moved '''

        start, end = [x/10 for x in self.timeRangeSlider.value()]

        # Update values in text editors based on slider
        self.startTime.setText(str(start))
        self.endTime.setText(str(end))

        iStart = self.stat.timeIndex(start)
        iEnd = self.stat.timeIndex(end)

        self.updateMapPath(iStart, iEnd)

    def newAreaButton(self, newBtnId, checked):
        print(inspect.currentframe().f_code.co_name)

        ''' A new area button was checked '''

        newBtn = self.areaBtnIdx[newBtnId]

        # User can define custom zone
        if newBtn in self.customAreas:
            # Show hidden map buttons after predefined area mode
            self.mapLayout.currentWidget().show()
            # Activate map buttons according to the current custom area type
            self.mapLayout.setCurrentIndex(newBtnId)

        # Zones are predefined
        else:
            # Hide custom area map buttons when in predefined area mode
            self.mapLayout.currentWidget().hide()
            # Define the predefined areas according to the chosen one
            self.fillPredefinedZones(newBtn)

    @pyqtSlot()
    def addNewZone(self, numNewZones=1):
        print(inspect.currentframe().f_code.co_name)

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
            # app.processEvents()
            # self.adjustSize()

        # Do not allow to add empty zone before a new area is selected
        self.addZoneBtn.setDisabled(True)

        self.fillTable()

        # Loop through all map buttons in all map layouts and uncheck them
        for i in range(self.mapLayout.count()):
            layout = self.mapLayout.widget(i).layout()
            for i in range(layout.count()):
                button = layout.itemAt(i).widget()
                button.blockSignals(True)
                button.setChecked(False)
                button.blockSignals(False)

        self.map.setStyleSheet(styleSheet(self.numZones))
        # self.adjustSize()

    def fillPredefinedZones(self, newBtn):
        print(inspect.currentframe().f_code.co_name)

        n = self.numLasers

        # Split field vertically into two halves
        if newBtn == 'Vertical_halves':
            self.zoneCoord[:, :n//2] = 1
            self.zoneCoord[:, n//2:] = 2

        # Split field horizontally into two halves
        elif newBtn == 'Horizontal_halves':
            self.zoneCoord[:n//2, :] = 1
            self.zoneCoord[n//2:, :] = 2

        # Split field into central and peripheral zones
        elif newBtn == 'Wall':
            self.zoneCoord[:, :] = 1
            self.zoneCoord[n//4 : 3*n//4, n//4 : 3*n//4] = 2

        self.updateMapZones()
        self.numZones = 0
        self.table.setColumnCount(1)
        self.addNewZone(numNewZones=2)

    def mapBtnToggled(self, checked, x=-1, y=-1, s=-1):
        print(inspect.currentframe().f_code.co_name)

        '''
        Actions when a map button was checked (add area for a new zone).
        Signals are defined in each area type method
        '''

        buttonType = self.areaBtnIdx[self.areaBtnGroup.checkedId()]
        #TODO To make more zones delete it
        if self.numZones == 4:
            return

        if checked:
            # Assign area coordinated to the index of the next zone
            zoneValue = self.numZones + 1
            # Allow to add a new zone after some area was selected
            self.addZoneBtn.setEnabled(True)
        else:
            # Exclude unchecked area from any zone
            zoneValue = 0

        # Assign the area checked with a custom button to the new zone
        if buttonType == 'Cell':
            self.zoneCoord[x][y] = zoneValue
        elif buttonType == 'Column':
            self.zoneCoord[:,y] = zoneValue
        elif buttonType == 'Row':
            self.zoneCoord[x,:] = zoneValue
        elif buttonType == 'Square':
            self.zoneCoord[[s, -s-1], s:self.numLasers-s] = zoneValue
            self.zoneCoord[s:self.numLasers-s, [s, -s-1]] = zoneValue

        # If all new areas were unchecked - do not allow adding empty zone
        if not checked and self.numZones + 1 not in self.zoneCoord:
            self.addZoneBtn.setEnabled(False)

        self.updateMapZones()

    def cellMapButtons(self):
        print(inspect.currentframe().f_code.co_name)

        ''' One cell map button, corresponds to one laser intersection '''

        self.cellMap = QWidget(self.map)
        self.cellMapLayout = QGridLayout(self.cellMap)
        self.cellMapLayout.setSpacing(0)
        self.cellMapLayout.setContentsMargins(0, 0, 0, 0)
        self.cellMapButtons = []

        for i in range(self.numLasers):
            self.cellMapButtons.append([])
            for j in range(self.numLasers):
                self.cellMapButtons[i].append(QPushButton('', self.map))
                self.cellMapButtons[i][j].setFixedSize(self.cell, self.cell)
                self.cellMapButtons[i][j].setCheckable(True)
                self.cellMapLayout.addWidget(self.cellMapButtons[i][j], i, j)
                self.cellMapButtons[i][j].toggled.connect(
                    lambda checked, i=i, j=j:
                        self.mapBtnToggled(checked=checked, x=i, y=j))

        return self.cellMap

    def columnMapButtons(self):
        print(inspect.currentframe().f_code.co_name)

        ''' Map buttons are vertical columns '''

        self.columnMap = QWidget(self.map)
        self.columnMapLayout = QHBoxLayout(self.columnMap)
        self.columnMapLayout.setSpacing(0)
        self.columnMapLayout.setContentsMargins(0, 0, 0, 0)
        self.columnMapButtons = []

        for i in range(self.numLasers):
            self.columnMapButtons.append(QPushButton('', self.map))
            self.columnMapButtons[i].setFixedSize(self.cell, self.mapSide)
            self.columnMapButtons[i].setCheckable(True)
            self.columnMapLayout.addWidget(self.columnMapButtons[i])
            self.columnMapButtons[i].toggled.connect(
                lambda checked, i=i:
                    self.mapBtnToggled(checked=checked, y=i))

        return self.columnMap

    def rowMapButtons(self):
        print(inspect.currentframe().f_code.co_name)

        ''' Map buttons are horizontal rows '''

        self.rowMap = QWidget(self.map)
        self.rowMapLayout = QVBoxLayout(self.rowMap)
        self.rowMapLayout.setSpacing(0)
        self.rowMapLayout.setContentsMargins(0, 0, 0, 0)
        self.rowMapButtons = []

        for i in range(self.numLasers):
            self.rowMapButtons.append(QPushButton('', self.map))
            self.rowMapButtons[i].setFixedSize(self.mapSide, self.cell)
            self.rowMapButtons[i].setCheckable(True)
            self.rowMapLayout.addWidget(self.rowMapButtons[i])
            self.rowMapButtons[i].toggled.connect(
                lambda checked, i=i:
                    self.mapBtnToggled(checked=checked, x=i))

        return self.rowMap

    def squareMapButtons(self):
        print(inspect.currentframe().f_code.co_name)

        ''' Map buttons are concentric squares '''

        self.squareMap = QWidget(self.map)
        self.squareMapLayout = QGridLayout(self.squareMap)
        self.squareMapLayout.setSpacing(0)
        self.squareMapLayout.setContentsMargins(0, 0, 0, 0)
        self.squareMapButtons = []

        for i in range(8):
            self.squareMapButtons.append(QPushButton('', self.map))
            self.squareMapButtons[i].setFixedSize(self.mapSide, self.mapSide)
            self.squareMapButtons[i].setCheckable(True)

            #TODO Add sys._MEIPASS here to package into one file
            pixmap = QPixmap(os.path.join('Area_pixmaps', f'{i+1}.png'))
            self.squareMapButtons[i].setMask(pixmap.scaled(self.squareMapButtons[i].size(),
                                                    Qt.IgnoreAspectRatio).mask())
            self.squareMapLayout.addWidget(self.squareMapButtons[i], 0, 0)
            self.squareMapButtons[i].toggled.connect(
                lambda checked, i=i:
                    self.mapBtnToggled(checked=checked, s=i))

        return self.squareMap



    def makeAreaButtons(self):
        print(inspect.currentframe().f_code.co_name)

        ''' Create area type buttons, arranged vertically to the left of the map '''

        numAreaBtn = len(self.areaBtnIdx)
        size = int(self.mapSide / (numAreaBtn * 1.5))

        self.areaBtnGroup = QButtonGroup()
        self.areaBtnLayout = QVBoxLayout()

        for idx, name in self.areaBtnIdx.items():
            # Make current button
            button = QPushButton()
            # Add button to QButtonGroup
            self.areaBtnGroup.addButton(button, id=idx)

            #TODO Add sys._MEIPASS here to package into one file
            pixmap = QPixmap(os.path.join('Area_Buttons_pixmaps', f'{name}.png'))

            # Set button's parameters
            self.areaBtnGroup.button(idx).setIcon(QIcon(pixmap))
            self.areaBtnGroup.button(idx).setIconSize(QSize(size, size))
            self.areaBtnGroup.button(idx).setFixedSize(size, size)
            self.areaBtnGroup.button(idx).setCheckable(True)

            # Set Cell as the default area type
            if name == 'Cell':
                self.areaBtnGroup.button(idx).setChecked(True)

            # Add button to QVBoxLayout
            self.areaBtnLayout.addWidget(self.areaBtnGroup.button(idx))

        self.areaBtnLayout.setSpacing(size // 2)
        # Add additional spacing between custom and predefined area buttons
        self.areaBtnLayout.insertSpacing(len(self.customAreas), size // 2)

        # self.areaBtnLayout.setContentsMargins(0, 0, 30, 0)

    def defineAreaTypes(self):
        print(inspect.currentframe().f_code.co_name)

        '''
        Define custom and predefined areas,
        make stacked layout with map buttons of different types
        '''

        self.customAreas = ['Cell', 'Column', 'Row', 'Square']
        self.predefinedAreas = ['Vertical_halves', 'Horizontal_halves', 'Wall']
        customAreaMethods = [self.cellMapButtons, self.columnMapButtons,
                                  self.rowMapButtons, self.squareMapButtons]

        # Make dict to index through QButtonGroup and QStackedLayout
        self.areaBtnIdx = {i: k for i, k
                           in enumerate(self.customAreas + self.predefinedAreas)}

        self.mapLayout = QStackedLayout()

        for idx, name in self.areaBtnIdx.items():
            # Create custom area map buttons with separate methods,
            # and them to self.mapLayout - a QStackedLayout
            if name in self.customAreas:
                areaMap = customAreaMethods[idx]()
                self.mapLayout.insertWidget(idx, areaMap)

        self.makeAreaButtons()

    def tableWidth(self):
        print(inspect.currentframe().f_code.co_name)

        app.processEvents()
        app.processEvents()
        tableWidth = self.table.verticalHeader().width() + \
                     self.table.horizontalHeader().length() + \
                     self.table.frameWidth() * 2
        if self.table.verticalScrollBar().isVisible():
            tableWidth += self.table.verticalScrollBar().width()

        return tableWidth

    # def tableHeight(self):
    #     print(inspect.currentframe().f_code.co_name)
    #     tableHeight = self.table.verticalHeader().length() + \
    #                   self.table.horizontalHeader().height() + \
    #                   self.table.frameWidth() * 2
    #     return tableHeight

    def fillTable(self):
        print(inspect.currentframe().f_code.co_name)

        ''' Fill table with statistics '''

        # Adjust table width to contents
        self.table.setFixedWidth(self.tableWidth())
        # Adjust window width to table
        # app.processEvents()
        # self.adjustSize()

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
        print(inspect.currentframe().f_code.co_name)

        ''' Save table with statistics to a new .csv file '''

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
    def __init__ (self, parent, window):
        super ().__init__ (parent)
        self.window = window

    def paint(self, painter, option, index):
        super().paint(painter, option, index)

        # Overlap of colored zone and gray even block
        if index.column() != 0 and \
           (index.row() // window.numStatParam) % 2 == 1:
            color = self.overlap(np.array([120, 120, 120, 120]),  # gray
                                 np.array([*zoneColors[index.column()], 80]))
        # Colored zone
        elif index.column() != 0:
            color = (*zoneColors[index.column()], 80)

        # Gray even block
        elif (index.row() // window.numStatParam) % 2 == 1:
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
    window = MainWindow()
    window.show()
    app.exec()
