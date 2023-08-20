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
        self.areaButtons()
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

        # self.areaBtn[self.areaBtnIdx['Vertical_halves']].toggled.connect(self.vHalfArea)
        # self.areaBtn[self.areaBtnIdx['Horizontal_halves']].toggled.connect(self.hHalfArea)
        # self.areaBtn[self.areaBtnIdx['Wall']].toggled.connect(self.wallArea)

        # self.areaBtn[self.areaBtnIdx['Cell']].toggled.connect(self.cellMapButtons)
        # self.areaBtn[self.areaBtnIdx['Column']].toggled.connect(self.columnMapButtons)
        # self.areaBtn[self.areaBtnIdx['Row']].toggled.connect(self.rowMapButtons)
        # self.areaBtn[self.areaBtnIdx['Square']].toggled.connect(self.squareMapButtons)
        self.areaBtnGroup.idToggled.connect(self.newAreaButton)
        # Update period
        self.periodLine.editingFinished.connect(self.checkPeriodValue)

        # Update time range from text
        self.startTime.editingFinished.connect(self.checkStartTimeValue)
        self.endTime.editingFinished.connect(self.checkEndTimeValue)

        # Update time range from slider
        self.timeRangeSlider.sliderMoved.connect(self.updateMapPath)
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
        '''Load raw data file, get statistics, update map and table'''
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

        self.mapCanvas = QPixmap(self.mapSide + 1, self.mapSide + 1)

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

        mapPainter = QPainter(self.mapCanvas)

        mapPainter.drawPixmap(0, 0, self.gridLayer)
        mapPainter.drawPixmap(0, 0, self.zoneLayer)
        mapPainter.drawPixmap(0, 0, self.pathLayer)

        mapPainter.end()

        self.map.setPixmap(self.mapCanvas)

    def updateMapZones(self):
        print(inspect.currentframe().f_code.co_name)

        self.zoneLayer.fill(Qt.transparent)

        zonePainter = QPainter(self.zoneLayer)

        print(self.zoneCoord)
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

        start, end = [x/10 for x in self.timeRangeSlider.value()]

        # Update values in text editors based on slider
        self.startTime.setText(str(start))
        self.endTime.setText(str(end))

        iStart = self.stat.timeIndex(start)
        iEnd = self.stat.timeIndex(end)


        self.pathLayer.fill(Qt.transparent)

        pathPainter = QPainter(self.pathLayer)

        pathPainter.setPen(QPen(Qt.red, 2))
        pathPainter.drawPolyline(self.pathPoints[iStart:iEnd])

        pathPainter.end()

        self.updateMap()

    def newAreaButton(self, newBtnId, checked):
        print(inspect.currentframe().f_code.co_name)

        self.mapLayout.setCurrentIndex(newBtnId)

    # def addNewAreaBtn(self, newBtn):
        # print(f'start {inspect.currentframe().f_code.co_name}')
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
        # multiZone = list(map(self.areaBtnGroup.__getitem__, ['Cell', 'Column',
        #                                                 'Row', 'Square']))

        # If new area type was selected without unchecking the old one
        # for btn in self.areaBtnGroup.values():
        #     if btn != newBtn and btn.isChecked():
        #         btn.setChecked(False)

        # self.checkedAreaBtn = newBtn
        # Define new empty list for map buttons
        # self.mapButtons = []
        # There will be only 2 zones:

        #!!!
        '''
        if newBtn not in multiZone:
            self.zoneCoord = np.zeros((self.numLasers, self.numLasers), dtype=int)
            self.addNewZone(fillTable=False, numNewZones=2)
            # Do not fill table now.
            # It will be updated from specific area type function,
            # after zoneCoord is updated.

        # Disable all other area type buttons except for the checked one
        # [self.areaBtn[key].setDisabled(True) for key in self.areaBtnNames \
        #                                               if key != newBtn]
        self.map.setStyleSheet(styleSheet(self.numZones))
        '''
        #!!!

        # print(f'end {inspect.currentframe().f_code.co_name}')

    # def clearMapButtons(self):
    #     print(f'start {inspect.currentframe().f_code.co_name}')

    #     # Delete old map buttons
    #     #for i in reversed(range(self.mapLayout.count())):
    #     # while self.mapLayout.count():
    #     #     item = self.mapLayout.takeAt(0).widget()
    #     #     item.deleteLater()
    #     # # Delete old map buttons' layout
    #     # self.mapLayout.deleteLater()


    #     def clearLayout(layout):
    #         if layout is not None:
    #             while layout.count():
    #                 item = layout.takeAt(0)
    #                 widget = item.widget()
    #                 if widget is not None:
    #                     widget.deleteLater()
    #                 else:
    #                     self.clearLayout(item.layout())

    #         layout.deleteLater()
    #     app.processEvents()
    #     app.processEvents()
    #     clearLayout(self.mapLayout)


        # self.checkedAreaBtn = None
        # self.addZoneBtn.setDisabled(True)

        # Enable all area buttons
        # [self.areaBtn[name].setEnabled(True) for name in self.areaBtn]

        # self.table.setColumnCount(1)
        # self.numZones = 0
        # self.zoneCoord = np.zeros((self.numLasers, self.numLasers), dtype=int)
        # self.fillTable()
        # self.table.setFixedWidth(self.tableWidth())
        # delattr(self, 'mapLayout')

        # Set style sheet for all map buttons
        # self.map.setStyleSheet(styleSheet(self.numZones))

        # print(f'end {inspect.currentframe().f_code.co_name}')

    @pyqtSlot()
    def addNewZone(self, fillTable=True, numNewZones=1):
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
            self.table.setFixedWidth(self.tableWidth())
            # app.processEvents()
            # self.adjustSize()

            # Show the new zone on map with a new color
        # self.map.setStyleSheet(styleSheet(self.numZones))

        # Do not allow to add empty zone before a new area is selected
        self.addZoneBtn.setDisabled(True)

        if fillTable:
            self.fillTable()

        # # Loop through all map buttons in all map layouts and uncheck them
        for i in range(self.mapLayout.count()):
            layout = self.mapLayout.widget(i).layout()
            for i in range(layout.count()):
                # Uncheck the button
                button = layout.itemAt(i).widget()
                button.blockSignals(True)
                button.setChecked(False)
                button.blockSignals(False)

        self.map.setStyleSheet(styleSheet(self.numZones))
        # self.adjustSize()

    def fillPredefinedZones(self, newBtnId):
        pass

    def mapBtnChecked(self, checked, x=-1, y=-1, s=-1):
        print(inspect.currentframe().f_code.co_name)
        '''
        Actions when a map button was checked (add area for a new zone).

        Signals are defined in each area type method
        '''

        #TODO To make more zones delete it
        if self.numZones == 4:
            return

        # Allow to add a new zone after some area was selected #???
        self.addZoneBtn.setEnabled(True)

        if checked:
            zoneValue = self.numZones + 1
        else:
            zoneValue = 0

        # Depending on the area type, self.mapButtons (list of map buttons)
        # has different shape and indexing:
        if s != -1:     # Square map button
            self.zoneCoord[[s, -s-1], s:self.numLasers-s] = zoneValue
            self.zoneCoord[s:self.numLasers-s, [s, -s-1]] = zoneValue
            # coord = s
            # self.mapButtons[(coord:=s)].setDisabled(True)
        elif y == -1:   # Row map button
            self.zoneCoord[x,:] = zoneValue
            # coord = x
            # self.mapButtons[(coord:=x)].setDisabled(True)
        elif x == -1:   # Column map button
            self.zoneCoord[:,y] = zoneValue
            # coord = y
            # self.mapButtons[(coord:=y)].setDisabled(True)
        else:           # Cell map button
            self.zoneCoord[x][y] = zoneValue
            # self.mapButtons[x][y].setDisabled(True)
            # self.mapButtons[x][y].setProperty(f'zone{self.numZones}', True)
            # self.map.setStyleSheet(styleSheet(self.numZones))

        # Property of the button (the number of zone it belongs to)
        # defines its color according the style sheet
        # self.mapButtons[coord].setProperty(f'zone{self.numZones}', True)

        # Define color for this new area
        # self.map.setStyleSheet(styleSheet(self.numZones))

        self.updateMapZones()

    def vHalfArea(self):
        print(inspect.currentframe().f_code.co_name)
        '''Split box vertically into two halves'''

        # button = self.sender()
        # if button.isChecked():
        #     self.addNewAreaBtn(button)
        # else:
        #     self.clearMapButtons()
        #     return

        # self.mapLayout = QHBoxLayout(self.map)
        # self.mapLayout.setSpacing(0)
        # self.mapLayout.setContentsMargins(0, 0, 0, 0)
        n = self.numLasers
        self.zoneCoord[:, :n//2] = 1
        self.zoneCoord[:, n//2:] = 2

        # halves = [QPushButton(), QPushButton()]
        # for half in halves:
        #     half.setFixedSize(int(self.mapSide / 2), self.mapSide)
        #     self.mapLayout.addWidget(half)
        # halves[0].setStyleSheet(f'background-color: rgba({color[0]}, 0.3)')
        # halves[1].setStyleSheet(f'background-color: rgba({color[1]}, 0.3)')
        self.fillTable()

    def hHalfArea(self):
        print(inspect.currentframe().f_code.co_name)
        '''Split box horizontally into two halves'''

        # button = self.sender()
        # if button.isChecked():
        #     self.addNewAreaBtn(button)
        # else:
        #     self.clearMapButtons()
        #     return

        # self.mapLayout = QVBoxLayout(self.map)
        # self.mapLayout.setSpacing(0)
        # self.mapLayout.setContentsMargins(0, 0, 0, 0)

        n = self.numLasers
        self.zoneCoord[:n//2, :] = 1
        self.zoneCoord[n//2:, :] = 2

        # halves = [QPushButton(), QPushButton()]
        # for half in halves:
        #     half.setFixedSize(self.mapSide, int(self.mapSide / 2))
        #     self.mapLayout.addWidget(half)
        # halves[0].setStyleSheet(f'background-color: rgba({color[0]}, 0.3)')
        # halves[1].setStyleSheet(f'background-color: rgba({color[1]}, 0.3)')

        self.fillTable()

    def wallArea(self):
        print(inspect.currentframe().f_code.co_name)
        '''Split box into central and peripheral zones'''

        # button = self.sender()
        # if button.isChecked():
        #     self.addNewAreaBtn(button)
        # else:
        #     self.clearMapButtons()
        #     return

        # self.mapLayout = QGridLayout(self.map)
        # self.mapLayout.setSpacing(0)
        # self.mapLayout.setContentsMargins(0, 0, 0, 0)

        n = self.numLasers
        self.zoneCoord = np.zeros((n, n), dtype=int)
        self.zoneCoord[n//4 : 3*n//4, n//4 : 3*n//4] = 2

        # pixmap = QPixmap(os.path.join('Area_pixmaps', 'wall.png'))
        # outer = QPushButton()
        # outer.setFixedSize(self.mapSide, self.mapSide)
        # outer.setMask(pixmap.scaled(outer.size(), Qt.IgnoreAspectRatio).mask())
        # outer.setStyleSheet(f'background-color: rgba({color[0]}, 0.3)')
        # self.mapLayout.addWidget(outer, 0, 0)

        # inner = outer = QPushButton()
        # inner.setFixedSize(int(self.mapSide / 2), int(self.mapSide / 2))
        # inner.setStyleSheet(f'background-color: rgba({color[1]}, 0.3)')
        # self.mapLayout.addWidget(inner, 0, 0, alignment = Qt.AlignCenter)

        self.fillTable()

    def cellMapButtons(self):
        print(inspect.currentframe().f_code.co_name)
        '''One cell map button, corresponds to one laser intersection'''

        # button = self.sender()
        # if button.isChecked():
        #     self.addNewAreaBtn(button)
        # else:
        #     self.clearMapButtons()
        #     return

        self.cellMap = QWidget(self.map)
        self.cellMapLayout = QGridLayout(self.cellMap)
        self.cellMapLayout.setSpacing(0)
        self.cellMapLayout.setContentsMargins(0, 0, 0, 0)
        self.cellMapButtons = []
        # self.mapLayout.addWidget(self.cellMapLayout)

        for i in range(self.numLasers):
            self.cellMapButtons.append([])
            for j in range(self.numLasers):
                self.cellMapButtons[i].append(QPushButton('', self.map))
                self.cellMapButtons[i][j].setFixedSize(self.cell, self.cell)
                self.cellMapButtons[i][j].setCheckable(True)
                self.cellMapLayout.addWidget(self.cellMapButtons[i][j], i, j)
                self.cellMapButtons[i][j].toggled.connect(
                    lambda checked, i=i, j=j:
                        self.mapBtnChecked(checked=checked, x=i, y=j))

        return self.cellMap

    def columnMapButtons(self):
        print(inspect.currentframe().f_code.co_name)
        '''Map buttons are vertical columns'''

        # button = self.sender()
        # if button.isChecked():
        #     self.addNewAreaBtn(button)
        # else:
        #     self.clearMapButtons()
        #     return

        self.columnMap = QWidget(self.map)
        self.columnMapLayout = QHBoxLayout(self.columnMap)
        self.columnMapLayout.setSpacing(0)
        self.columnMapLayout.setContentsMargins(0, 0, 0, 0)
        self.columnMapButtons = []
        # self.mapLayout.addWidget(self.columnMapLayout)

        for i in range(self.numLasers):
            self.columnMapButtons.append(QPushButton('', self.map))
            self.columnMapButtons[i].setFixedSize(self.cell, self.mapSide)
            self.columnMapButtons[i].setCheckable(True)
            self.columnMapLayout.addWidget(self.columnMapButtons[i])
            self.columnMapButtons[i].toggled.connect(
                lambda checked, i=i:
                    self.mapBtnChecked(checked=checked, y=i))

        return self.columnMap

    def rowMapButtons(self):
        print(inspect.currentframe().f_code.co_name)
        '''Map buttons are horizontal rows'''

        # button = self.sender()
        # if button.isChecked():
        #     self.addNewAreaBtn(button)
        # else:
        #     self.clearMapButtons()
        #     return

        self.rowMap = QWidget(self.map)
        self.rowMapLayout = QVBoxLayout(self.rowMap)
        self.rowMapLayout.setSpacing(0)
        self.rowMapLayout.setContentsMargins(0, 0, 0, 0)
        self.rowMapButtons = []
        # self.mapLayout.addWidget(self.rowMapLayout)

        for i in range(self.numLasers):
            self.rowMapButtons.append(QPushButton('', self.map))
            self.rowMapButtons[i].setFixedSize(self.mapSide, self.cell)
            self.rowMapButtons[i].setCheckable(True)
            self.rowMapLayout.addWidget(self.rowMapButtons[i])
            self.rowMapButtons[i].toggled.connect(
                lambda checked, i=i:
                    self.mapBtnChecked(checked=checked, x=i))

        return self.rowMap

    def squareMapButtons(self):
        print(inspect.currentframe().f_code.co_name)
        '''Map buttons are concentric squares'''

        # button = self.sender()
        # if button.isChecked():
        #     self.addNewAreaBtn(button)
        # else:
        #     self.clearMapButtons()
        #     return

        self.squareMap = QWidget(self.map)
        self.squareMapLayout = QGridLayout(self.squareMap)
        self.squareMapLayout.setSpacing(0)
        self.squareMapLayout.setContentsMargins(0, 0, 0, 0)
        self.squareMapButtons = []
        # self.mapLayout.addWidget(self.squareMapLayout)

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
                    self.mapBtnChecked(checked=checked, s=i))

        return self.squareMap

    def areaButtons(self):
        print(inspect.currentframe().f_code.co_name)
        '''Area types buttons, arranged vertically to the left of the map'''


        customAreaBtn = ['Cell', 'Column', 'Row', 'Square']
        predefinedAreaBtn = ['Vertical_halves', 'Horizontal_halves', 'Wall']
        areaBtnMethodsList = [self.cellMapButtons, self.columnMapButtons,
                                  self.rowMapButtons, self.squareMapButtons]
                                 # self.vHalfArea, self.vHalfArea, self.wallArea]
        # Make a bidirectional dict to index through QButtonGroup
        self.areaBtnIdx = {}
        areaBtnMethods = {}
        for i, k in enumerate(customAreaBtn + predefinedAreaBtn):
            self.areaBtnIdx.update({i: k}) #{k: i, i: k})
            # areaBtnMethods.update({i: areaBtnMethodsList[i]})

        self.areaBtnGroup = QButtonGroup()
        self.areaBtnLayout = QVBoxLayout()
        self.mapLayout = QStackedLayout()

        # Create area buttons
        numAreaBtn = len(self.areaBtnIdx)
        size = int(self.mapSide / (numAreaBtn * 1.5))

        for idx, name in self.areaBtnIdx.items():
            # Make current button
            # self.areaBtn[name] = QPushButton()
            button = QPushButton()
            self.areaBtnGroup.addButton(button, id=idx)

            #TODO Add sys._MEIPASS here to package into one file
            pixmap = QPixmap(os.path.join('Area_Buttons_pixmaps', f'{name}.png'))

            # Set button's parameters
            self.areaBtnGroup.button(idx).setIcon(QIcon(pixmap))
            self.areaBtnGroup.button(idx).setIconSize(QSize(size, size))
            self.areaBtnGroup.button(idx).setFixedSize(size, size)
            self.areaBtnLayout.addWidget(self.areaBtnGroup.button(idx))
            self.areaBtnGroup.button(idx).setCheckable(True)

            if name in customAreaBtn:
                areaMap = areaBtnMethodsList[idx]()
                self.mapLayout.insertWidget(idx, areaMap)

            # Cell is the default area type
            if name == 'Cell':
                self.areaBtnGroup.button(idx).setChecked(True)

        self.areaBtnLayout.setSpacing(size // 2)
        self.areaBtnLayout.insertSpacing(4, size // 2)



        # self.areaBtnLayout.setContentsMargins(0, 0, 30, 0)

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

    def tableHeight(self):
        print(inspect.currentframe().f_code.co_name)
        tableHeight = self.table.verticalHeader().length() + \
                      self.table.horizontalHeader().height() + \
                      self.table.frameWidth() * 2
        return tableHeight

    def fillTable(self):
        print(inspect.currentframe().f_code.co_name)
        '''Fill table with statistics'''

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

        # self.updateMap()

    def saveData(self):
        print(inspect.currentframe().f_code.co_name)
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
