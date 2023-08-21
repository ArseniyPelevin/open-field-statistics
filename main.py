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
    QStyleFactory
)
from PyQt6.QtCore import (
    Qt, QSize, pyqtSlot, QEvent, QPointF, QVariantAnimation, QRegularExpression
    )
from PyQt6.QtGui import (
    QFontMetrics, QIcon,
    QPen, QPixmap, QPainter, QColor, QPalette, QRegularExpressionValidator
)

from superqt import QRangeSlider

from OpenFieldDataProcessing import DataProcessing
#TODO Expand zoneCoolors to allow more zones
from ColorStyle import Colors, Delegate
from MapFunctionality import MapWidget


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
        # self.numLasers = self.params['numLasers']
        # self.mapSide = min(self.height(), self.width()/2) * 2/3
        self.numStatParam = self.params['numStatParam']
        self.statParam = ['time', 'dist', 'vel', 'rear', 'rearTime']

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
        self.secondsLabel = QLabel(' seconds')

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

        self.map = MapWidget(self, self.params)
        # self.map.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)

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
        self.addZoneBtn.clicked.connect(self.map.addNewZone)
        self.saveButton.clicked.connect(self.saveData)

        self.map.areaBtnGroup.idToggled.connect(self.map.newAreaButton)
        # Update period
        self.periodLine.editingFinished.connect(self.checkPeriodValue)

        # Update time range from text
        self.startTime.editingFinished.connect(self.checkStartTimeValue)
        self.endTime.editingFinished.connect(self.checkEndTimeValue)

        # Update time range from slider
        self.timeRangeSlider.sliderMoved.connect(self.sliderUpdateTimeRange)
        self.timeRangeSlider.sliderReleased.connect(self.selectedStatistics)

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
        periodLayout.addWidget(self.secondsLabel, alignment = Qt.AlignRight)

        self.controlLayout = QGridLayout()
        self.controlLayout.addWidget(self.getFileButton, 0, 0, 1, 1, Qt.AlignLeft)
        self.controlLayout.addWidget(self.fileNameLabel, 0, 1, 1, 2)
        self.controlLayout.addWidget(self.addZoneBtn, 1, 0, 1, 2, Qt.AlignRight)
        self.controlLayout.addLayout(self.map.areaBtnLayout, 2, 0, 1, 1, Qt.AlignLeft)
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
        self.map.makePath(self.stat.data)

        # Update window
        self.setTimeRange()
        self.map.updateMapPath(0, self.stat.data.index[-1])
        self.fillTable()
        self.saveButton.setEnabled(True)

    def selectedStatistics(self):
        print(inspect.currentframe().f_code.co_name)

        '''
        User can selected a time range within recording time to analyze.
        All statistics will be shown for this range,
        except for Total time statistics
        '''

        n = self.numStatParam

        start = float(self.startTime.text())
        end = float(self.endTime.text())

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

        self.map.updateMapPath(iStart, iEnd)

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

    def sliderUpdateTimeRange(self, value):
        print(inspect.currentframe().f_code.co_name)

        ''' Update path while Selected time slider is being moved '''

        start, end = [x/10 for x in value] #self.timeRangeSlider.value()]

        # Update values in text editors based on slider
        self.startTime.setText(str(start))
        self.endTime.setText(str(end))

        iStart = self.stat.timeIndex(start)
        iEnd = self.stat.timeIndex(end)

        self.map.updateMapPath(iStart, iEnd)

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
            self.tableData = self.stat.table(self.map.zoneCoord, self.startSelected,
                                        self.endSelected, self.period,
                                        self.statParam)
        except AttributeError:  # If .csv has not yet been opened
            return

        s = self.hasSelectedStat
        n = self.numStatParam

        # Fill Total time statistics
        for zone in range(self.map.numZones+1):
            for k in range(n):
                key = self.statParam[k]
                val = round(self.tableData[0][zone][key], 1)
                item = QTableWidgetItem(str(val))
                self.table.setItem(k, zone, item)

        # Fill Selected time statistics
        if self.hasSelectedStat:
            for zone in range(self.map.numZones+1):
                for k in range(n):
                    key = self.statParam[k]
                    val = round(self.tableData[-1][zone][key], 1)
                    item = QTableWidgetItem(str(val))
                    self.table.setItem(n+k, zone, item)

        # Fill Periods statistics
        if self.numPeriods != 0:
            for per in range(1, self.numPeriods+1):
                for zone in range(self.map.numZones+1):
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
                            + [f'Zone {x+1}' for x in range(self.map.numZones)])

            # Write Total time statistics
            for k in range(n):
                key = self.statParam[k]
                writer.writerow(['Total time', f'{self.verticalHeaders[k]}']
                                + [round(self.tableData[0][zone][key], 1)
                                 for zone in range(self.map.numZones+1)])

            # Write Selected time statistics
            if self.hasSelectedStat:
                for k in range(n):
                        key = self.statParam[k]
                        writer.writerow([
                    f'Selected time {self.startSelected}-{self.endSelected} s',
                    f'{self.verticalHeaders[k]}']
                    + [round(self.tableData[-1][zone][key], 1)
                       for zone in range(self.map.numZones+1)])

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
                                           for zone in range(self.map.numZones+1)])

if __name__ == '__main__':
    app = QApplication(os.sys.argv)
    app.setStyle(QStyleFactory.create('Fusion'))
    window = MainWindow()
    window.show()
    app.exec()
