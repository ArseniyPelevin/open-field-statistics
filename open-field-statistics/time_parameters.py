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


class TimeParameters:

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
        self.periodLine.editingFinished.connect(self.checkPeriod)

        # Update time range from text
        self.startSelectedLine.editingFinished.connect(self.checkStartSelected)
        self.endSelectedLine.editingFinished.connect(self.checkEndSelected)

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

        self.totalTime = stat.df.index[-1].total_seconds()

        if 'startSelected' not in self.params:
            self.params['startSelected'] = 0
        if 'endSelected' not in self.params:
            self.params['endSelected'] = self.totalTime

        self.selectedTime = round(self.params['endSelected']
                                  - self.params['startSelected'], 1)

        if 'period' not in self.params:
            self.params['period'] = self.selectedTime

        self.loadTimeWidgets()

    def loadTimeWidgets(self):
        print(__name__, inspect.currentframe().f_code.co_name)

        ''' Update time widgets based on loaded raw data '''

        self.startSelectedLine.setRange(0., self.totalTime)
        self.startSelectedLine.setValue(self.params['startSelected'])
        self.endSelectedLine.setRange(0., self.totalTime)
        self.endSelectedLine.setValue(self.params['endSelected'])
        self.periodLine.setRange(1., self.totalTime)
        self.periodLine.setValue(self.params['period'])

        self.selectedTimeLabel.setText(f'Selected time: {self.selectedTime} seconds')

        sliderStep = 0.1   # Step of selected time range slider in seconds

        with QSignalBlocker(self.timeRangeSlider):
            self.timeRangeSlider.setRange(0, self.totalTime / sliderStep)
            self.timeRangeSlider.setValue([self.params['startSelected'] / sliderStep,
                                           self.params['endSelected'] / sliderStep])

        self.startSelectedLine.setEnabled(True)
        self.endSelectedLine.setEnabled(True)
        self.periodLine.setEnabled(True)
        self.timeRangeSlider.setEnabled(True)

    def checkPeriod(self):
        print(__name__, inspect.currentframe().f_code.co_name)

        period = self.periodLine.value()
        if period > self.selectedTime:
                errorMessage = ('Period should be in the range:\n'
                                + f'1 s ≤ period < {self.selectedTime} s')
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
                                + f"0 s ≤ start time < {self.params['endSelected']} s")
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
                            + f"{self.params['startSelected']} s < end time ≤ {self.totalTime} s")

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
        # with QSignalBlocker(self.startSelectedLine): #!!!
        self.startSelectedLine.setValue(start)
        # with QSignalBlocker(self.endSelectedLine):
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

        oldSelectedTime = self.selectedTime
        self.selectedTime = round(end - start, 1)
        self.selectedTimeLabel.setText(f'Selected time: {self.selectedTime} seconds')

        period = self.params['period']
        if (period == oldSelectedTime or period > self.selectedTime):
            period = self.selectedTime
        self.updatePeriod(period)

    def updatePeriod(self, period):
        print(__name__, inspect.currentframe().f_code.co_name)

        '''
        Selected time is split to periods of user-defined length in seconds.
        Statistics for each period (and in each zone) is shown in the table.
        '''

        self.periodLine.setValue(period)
        self.params['period'] = period

        self.window.table.fillTable()
