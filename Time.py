
import numpy as np
import math as m
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


class TimePeriodSettings:

    def __init__(self, window):
        print(__name__, inspect.currentframe().f_code.co_name)

        self.window = window
        self.numStatParam = self.window.numStatParam
        self.hasSelectedStat = False

        self.setTimeWidgets()
        self.setTimeSignals()
        self.setTimeLayouts()

    def setTimeWidgets(self):
        print(__name__, inspect.currentframe().f_code.co_name)

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

        # Set input validator
        rx = QRegularExpression(r'^\d+\.?\d*$')  # float
        inputValidator = QRegularExpressionValidator(rx)
        self.periodLine.setValidator(inputValidator)
        self.startTime.setValidator(inputValidator)
        self.endTime.setValidator(inputValidator)

    def setTimeSignals(self):
        print(__name__, inspect.currentframe().f_code.co_name)

        # Update period
        self.periodLine.editingFinished.connect(self.checkPeriodValue)

        # Update time range from text
        self.startTime.editingFinished.connect(self.checkStartTimeValue)
        self.endTime.editingFinished.connect(self.checkEndTimeValue)

        # Update time range from slider
        self.timeRangeSlider.sliderMoved.connect(self.sliderUpdateTimeRange)
        self.timeRangeSlider.sliderReleased.connect(self.selectedStatistics)

    def setTimeLayouts(self):
        print(__name__, inspect.currentframe().f_code.co_name)

        self.timeRangeLayout = QGridLayout()
        self.timeRangeLayout.addWidget(self.startTime, 0, 0, Qt.AlignLeft)
        self.timeRangeLayout.addWidget(self.selectedTimeLabel, 0, 1, Qt.AlignCenter)
        self.timeRangeLayout.addWidget(self.endTime, 0, 2, Qt.AlignRight)
        self.timeRangeLayout.addWidget(self.timeRangeSlider, 1, 0, 1, 3, Qt.AlignBottom)

        self.periodLayout = QHBoxLayout()
        self.periodLayout.addWidget(self.timePeriod, alignment = Qt.AlignRight)
        self.periodLayout.addWidget(self.periodLine, alignment = Qt.AlignRight)
        self.periodLayout.addWidget(self.secondsLabel, alignment = Qt.AlignRight)

    def updateTimeVariables(self, stat):
        print(__name__, inspect.currentframe().f_code.co_name)

        self.stat = stat
        # Update variables
        self.startSelected = 0
        self.endSelected = self.stat.totalTime
        self.selectedTime = self.endSelected
        self.selectedTimeLabel.setText(f'Selected time: {self.selectedTime} seconds')
        self.period = self.stat.totalTime
        self.numPeriods = 0

        self.setTimeRange()
        self.table = self.window.table

    def setTimeRange(self):
        print(__name__, inspect.currentframe().f_code.co_name)

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

    def selectedStatistics(self):
        print(__name__, inspect.currentframe().f_code.co_name)

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
                               for x in self.table.verticalHeaders]
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

        self.window.map.updateMapPath(iStart, iEnd)

    def updatePeriod(self, period=0, isUsersPeriod=False):
        print(__name__, inspect.currentframe().f_code.co_name)

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
            self.table.fillTable()
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
                                     + f'{self.table.verticalHeaders[j]}'))

        self.table.fillTable()

    def sliderUpdateTimeRange(self, value):
        print(__name__, inspect.currentframe().f_code.co_name)

        ''' Update path while Selected time slider is being moved '''

        start, end = [x/10 for x in value] #self.timeRangeSlider.value()]

        # Update values in text editors based on slider
        self.startTime.setText(str(start))
        self.endTime.setText(str(end))

        iStart = self.stat.timeIndex(start)
        iEnd = self.stat.timeIndex(end)

        self.window.map.updateMapPath(iStart, iEnd)

    def textUpdateTimeRange(self, start, end):
        print(__name__, inspect.currentframe().f_code.co_name)

        # Update slider values based on text editors
        self.timeRangeSlider.setValue([start*10, end*10])
        self.selectedStatistics(start, end)

    def errorWarning(self, widget, errorMessage=''):
        print(__name__, inspect.currentframe().f_code.co_name)

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
        QToolTip.showText(self.window.mapToGlobal(widget.pos()), errorMessage, widget)

    def checkPeriodValue(self):
        print(__name__, inspect.currentframe().f_code.co_name)

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
        print(__name__, inspect.currentframe().f_code.co_name)

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
        print(__name__, inspect.currentframe().f_code.co_name)

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
