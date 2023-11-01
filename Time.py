
import numpy as np
import math as m
import inspect

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QFileDialog, QToolTip,
    QLabel, QLineEdit, QPushButton, QButtonGroup, QSpacerItem,
    QVBoxLayout, QHBoxLayout, QGridLayout, QStackedLayout,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QStyleFactory,
    QDoubleSpinBox
)
from PyQt6.QtCore import (
    Qt, QSize, pyqtSlot, QEvent, QPointF, QVariantAnimation, QRegularExpression,
    QSignalBlocker
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
        self.map = self.window.map

        self.params = self.window.params
        # self.numStatParam = len(self.params['statParams'])
        # self.hasSelectedStat = False

        self.setTimeWidgets()
        self.setTimeSignals()
        self.setTimeLayouts()

    def setTimeWidgets(self):
        print(__name__, inspect.currentframe().f_code.co_name)

        self.periodLabel = QLabel('Time period every ')

        self.periodLine = QDoubleSpinBox(alignment = Qt.AlignRight)
        self.periodLine.setFixedWidth(60)
        self.periodLine.setDecimals(1)
        self.periodLine.setSuffix(' s')
        self.periodLine.setDisabled(True)

        self.startSelectedLine = QDoubleSpinBox(alignment = Qt.AlignLeft)
        self.startSelectedLine.setFixedWidth(60)
        self.startSelectedLine.setDecimals(1)
        self.startSelectedLine.setSuffix(' s')
        self.startSelectedLine.setDisabled(True)

        self.endSelectedLine = QDoubleSpinBox(alignment = Qt.AlignRight)
        self.endSelectedLine.setFixedWidth(60)
        self.endSelectedLine.setDecimals(1)
        self.endSelectedLine.setSuffix(' s')
        self.endSelectedLine.setDisabled(True)

        self.timeRangeSlider = QRangeSlider(Qt.Horizontal)
        self.timeRangeSlider.setDisabled(True)

        self.selectedTimeLabel = QLabel()

        # Default LineEdit background will be needed for error warning
        self.defaultLineEditBackground = self.periodLine.palette().color(
                                         QPalette.Active, QPalette.Base)

    def setTimeSignals(self):
        print(__name__, inspect.currentframe().f_code.co_name)

        # Update period
        self.periodLine.valueChanged.connect(self.checkPeriod)

        # Update time range from text
        self.startSelectedLine.valueChanged.connect(self.checkStartSelected)
        self.endSelectedLine.valueChanged.connect(self.checkEndSelected)

        # Update time range from slider
        self.timeRangeSlider.sliderMoved.connect(self.sliderUpdateSelectedTime)
        self.timeRangeSlider.sliderReleased.connect(self.updateSelectedTime)

    def setTimeLayouts(self):
        print(__name__, inspect.currentframe().f_code.co_name)

        self.timeRangeLayout = QGridLayout()
        self.timeRangeLayout.addWidget(self.startSelectedLine, 0, 0, Qt.AlignLeft)
        self.timeRangeLayout.addWidget(self.selectedTimeLabel, 0, 1, Qt.AlignCenter)
        self.timeRangeLayout.addWidget(self.endSelectedLine, 0, 2, Qt.AlignRight)
        self.timeRangeLayout.addWidget(self.timeRangeSlider, 1, 0, 1, 3, Qt.AlignBottom)

        self.periodLayout = QHBoxLayout()
        self.periodLayout.addWidget(self.periodLabel, alignment = Qt.AlignRight)
        self.periodLayout.addWidget(self.periodLine, alignment = Qt.AlignRight)
        # self.periodLayout.addWidget(self.secondsLabel, alignment = Qt.AlignRight)

    def loadTimeVariables(self, stat):
        print(__name__, inspect.currentframe().f_code.co_name)

        ''' Update time variables based on loaded raw data '''

        self.stat = stat
        self.data = self.stat.data
        print(self.data)
        self.totalTime = self.data.loc[("Total_time", "time"), "Whole_field"]

        if 'startSelected' not in self.params:
            self.params['startSelected'] = 0
        if 'endSelected' not in self.params:
            self.params['endSelected'] = self.totalTime
        if 'period' not in self.params:
            self.params['period'] = self.totalTime

        self.selectedTime = round(self.params['endSelected']
                                  - self.params['startSelected'], 1)

        self.loadTimeWidgets()
        # self.table = self.window.table

    def loadTimeWidgets(self):
        print(__name__, inspect.currentframe().f_code.co_name)

        ''' Update time widgets based on loaded raw data '''

        self.startSelectedLine.setRange(0., self.totalTime)
        self.endSelectedLine.setRange(0., self.totalTime)
        self.periodLine.setRange(1., self.totalTime)

        self.startSelectedLine.setValue(self.params['startSelected'])
        self.endSelectedLine.setValue(self.params['endSelected'])
        if self.params['period'] < self.selectedTime:
            self.periodLine.setValue(self.params['period'])

        self.selectedTimeLabel.setText(f'Selected time: {self.selectedTime} seconds')

        sliderStep = 0.1   # Step of selected time range slider in seconds
        self.timeRangeSlider.setRange(0, self.totalTime / sliderStep)
        self.timeRangeSlider.setValue([self.params['startSelected'],
                                       self.params['endSelected'] / sliderStep])

        self.startSelectedLine.setEnabled(True)
        self.endSelectedLine.setEnabled(True)
        self.periodLine.setEnabled(True)
        self.timeRangeSlider.setEnabled(True)

#%%
#??? Delete this method alltogether?
    # def updateSelectedTime(self):
    #     print(__name__, inspect.currentframe().f_code.co_name)

    #     '''
    #     User can selected a time range within recording time to analyze.
    #     All statistics will be shown for this range,
    #     except for Total time statistics
    #     '''

        # n = self.numStatParam



#!!!
        # iStart = self.stat.timeIndex(start)
        # iEnd = self.stat.timeIndex(end)

        # if start == 0 and end == self.totalTime:
        #     self.hasSelectedStat = False
        # else:
        #     headersSelected = [QTableWidgetItem
        #                        (f'Selected time {start}-{end} s,\n{header}')
        #                        for header in self.table.verticalHeaders]
        #     for i in range(n):
        #         # If there was Selected time statistics before - delete it
        #         if self.hasSelectedStat:
        #             self.table.removeRow(n + i)
        #         self.table.insertRow(n + i)
        #         self.table.setVerticalHeaderItem(n + i, headersSelected[i])
        #     self.hasSelectedStat = True

        # self.params['startSelected'] = start
        # self.params['endSelected'] = end
        # self.selectedTime = round(end - start, 1)
        # self.selectedTimeLabel.setText(f'Selected time: {self.selectedTime} seconds')

        # self.updatePeriod()

        # self.map.updateMapPath(iStart, iEnd)
        # self.map.updateMapPath(start, end) #??? Passing df here?
        #%%

    def checkPeriod(self):
        print(__name__, inspect.currentframe().f_code.co_name)

#??? Don't need try now
        try:
            period = self.periodLine.value()
        # Empty line was entered
        except ValueError:
            period = 0
        else:
            if period > self.selectedTime:
                errorMessage = ('Period should be in the range:\n'
                                + f'1 s < period < {self.selectedTime} s')
                self.errorWarning(self.periodLine, errorMessage)
                period = self.selectedTime

        self.updatePeriod(period)

    def checkStartSelected(self):
        print(__name__, inspect.currentframe().f_code.co_name)

#???
        try:
            start = self.startSelectedLine.value()
        # Empty line was entered as start time, set start to 0
        except ValueError:
            start = 0
            self.startSelectedLine.setValue(start)
        else:
            # Selected start > Selected end, back to initial value
            if start >= self.params['endSelected']:
                errorMessage = ('Start time should be in the range:\n'
                                + f"0 s <= start time < {self.params['endSelected']} s")
                self.errorWarning(self.startSelectedLine, errorMessage)

                start = self.params['startSelected']
                self.startSelectedLine.setValue(start)

        self.updateSelectedTime(start, self.params['endSelected'])

    def checkEndSelected(self):
        print(__name__, inspect.currentframe().f_code.co_name)

#???
        try:
            end = self.endSelectedLine.value()
        # Empty line was entered as end time, set end to max total time
        except ValueError:
            end = self.totalTime
            self.endSelectedLine.setValue(end)
        else:
            errorMessage = ('End time should be in the range:\n'
                            + f"{self.params['startSelected']} s < end time <= {self.totalTime} s")

            # Selected end < Selected start, back to previous value
            if end <= self.params['startSelected']:
                self.errorWarning(self.endSelectedLine, errorMessage)

                end = self.params['endSelected']
                self.endSelectedLine.setValue(end)

            # Selected end > total time, set Selected time to max total time
            elif end > self.totalTime:
                self.errorWarning(self.endSelectedLine, errorMessage)

                end = self.totalTime
                self.endSelectedLine.setValue(end)

        self.updateSelectedTime(self.params['startSelected'], end)

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

    def sliderUpdateSelectedTime(self, value):
        print(__name__, inspect.currentframe().f_code.co_name)

        ''' Update path while Selected time slider is being moved '''

        start, end = [x/10 for x in value] #self.timeRangeSlider.value()]

        # Update values in text editors based on slider. Block their signals
        with QSignalBlocker(self.startSelectedLine):
            self.startSelectedLine.setValue(start)
        with QSignalBlocker(self.endSelectedLine):
            self.endSelectedLine.setValue(end)

        self.map.updateMapPath(start, end)
        # Do not update SelectedTime values here while slider is being moved

    def updateSelectedTime(self, start=None, end=None):
        print(__name__, inspect.currentframe().f_code.co_name)

        if start is None or end is None:
            start, end = self.timeRangeSlider.sliderPosition()
            start /= 10
            end /= 10

        self.params['startSelected'] = start
        self.params['endSelected'] = end

        # Update slider values based on text editors
        self.timeRangeSlider.setValue([start*10, end*10])

        self.selectedTime = round(end - start, 1)
        self.selectedTimeLabel.setText(f'Selected time: {self.selectedTime} seconds')

        self.updatePeriod()

    def updatePeriod(self, period=0):
        print(__name__, inspect.currentframe().f_code.co_name)

        '''
        Selected time is split to periods of user-defined length in seconds.
        Statistics for each period (and in each zone) is shown in the table.
        '''

        # Period statistics goes after Total time and Selected time in table
        # n = self.numStatParam
        # self.table.setRowCount(n + n * self.hasSelectedStat)

        self.params['period'] = period
        self.periodLine.lineEdit().setVisible(True)

        # Period is not defined
        if period == 0 or period == self.selectedTime:
            self.params['period'] = self.selectedTime  # Default value
            self.periodLine.setValue(0)
            # self.periodLine.lineEdit().setVisible(False)
            self.periodLine.setSpecialValueText(' s')
            # self.numPeriods = 0
            # self.periodTimes = []
            # self.table.fillTable() #!!!
            # self.table.model.layoutChanged.emit()
            # return

        # self.period = period
        # self.numPeriods = m.ceil(self.selectedTime / self.period)
        # self.periodTimes = []   # Start and end of each period
        #                         # ! relative to Selected time !
        # for i in range(self.numPeriods):
        #     timeStart = round(i * self.period, 1)
        #     timeEnd = round((i+1) * self.period, 1)
        #     if timeEnd > self.selectedTime:
        #         timeEnd = self.selectedTime
        #     self.periodTimes.append((timeStart, timeEnd))
        #     numRows = self.table.rowCount()
        #     self.table.setRowCount(numRows+n)
        #     # For each period add empty rows for its statistics in table
        #     for j in range(n):
        #         self.table.setVerticalHeaderItem(numRows + j,
        #             QTableWidgetItem(f'{timeStart}-{timeEnd} s, '
        #                              + f'{self.table.verticalHeaders[j]}'))

        self.window.table.fillTable()
