import numpy as np
import math as m
import inspect

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QFileDialog, QToolTip,
    QLabel, QLineEdit, QPushButton, QButtonGroup, QSpacerItem,
    QVBoxLayout, QHBoxLayout, QGridLayout, QStackedLayout,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QStyleFactory,
    QDoubleSpinBox, QAbstractSpinBox
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

        # self.params = self.window.params #!!!
        self.timeParams = dict.fromkeys(['startSelected', 'endSelected', 'period'])
        # self.numStatParam = len(self.params['statParams'])
        # self.hasSelectedStat = False

        self.setTimeWidgets()
        self.setTimeSignals()
        self.setTimeLayouts()

    def setTimeWidgets(self):
        print(__name__, inspect.currentframe().f_code.co_name)

        self.periodLabel = QLabel('Time period every ')

        self.periodLine = DoubleSpinBox(alignment=Qt.AlignRight)
        self.periodLine.setFixedWidth(60)
        self.periodLine.setDecimals(1)
        self.periodLine.setSuffix(' s')
        self.periodLine.setButtonSymbols(QAbstractSpinBox.NoButtons)
        self.periodLine.setCorrectionMode('max')
        self.periodLine.setKeyboardTracking(False)
        self.periodLine.setDisabled(True)

        self.startSelectedLine = DoubleSpinBox(alignment=Qt.AlignLeft)
        self.startSelectedLine.setFixedWidth(60)
        self.startSelectedLine.setDecimals(1)
        self.startSelectedLine.setSuffix(' s')
        self.startSelectedLine.setButtonSymbols(QAbstractSpinBox.NoButtons)
        self.startSelectedLine.setCorrectionMode('min')
        self.startSelectedLine.setKeyboardTracking(False)
        self.startSelectedLine.setDisabled(True)

        self.endSelectedLine = DoubleSpinBox(alignment=Qt.AlignRight)
        self.endSelectedLine.setFixedWidth(60)
        self.endSelectedLine.setDecimals(1)
        self.endSelectedLine.setSuffix(' s')
        self.endSelectedLine.setButtonSymbols(QAbstractSpinBox.NoButtons)
        self.endSelectedLine.setCorrectionMode('max')
        self.endSelectedLine.setKeyboardTracking(False)
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
        self.periodLayout.addWidget(self.periodLabel, alignment=Qt.AlignRight)
        self.periodLayout.addWidget(self.periodLine, alignment=Qt.AlignRight)

    def loadTimeVariables(self, stat):
        print(__name__, inspect.currentframe().f_code.co_name)

        ''' Update time variables based on loaded raw data '''

        self.totalTime = stat.df.index[-1].total_seconds()

        self.timeParams['startSelected'] = 0
        self.timeParams['endSelected'] = self.totalTime

        self.selectedTime = round(self.timeParams['endSelected']
                                  - self.timeParams['startSelected'], 1)

        self.timeParams['period'] = self.selectedTime

        self.loadTimeWidgets()

    def loadTimeWidgets(self):
        print(__name__, inspect.currentframe().f_code.co_name)

        ''' Update time widgets based on loaded raw data '''

        self.startSelectedLine.setRange(0., self.totalTime)
        self.startSelectedLine.setValue(self.timeParams['startSelected'])
        self.endSelectedLine.setRange(0., self.totalTime)
        self.endSelectedLine.setValue(self.timeParams['endSelected'])
        self.periodLine.setRange(1., self.totalTime)
        self.periodLine.setValue(self.timeParams['period'])

        self.selectedTimeLabel.setText(f'Selected time: {self.selectedTime} seconds')

        sliderStep = 0.1   # Step of selected time range slider in seconds

        with QSignalBlocker(self.timeRangeSlider):
            self.timeRangeSlider.setRange(0, self.totalTime / sliderStep)
            self.timeRangeSlider.setValue([self.timeParams['startSelected'] / sliderStep,
                                           self.timeParams['endSelected'] / sliderStep])

        self.startSelectedLine.setEnabled(True)
        self.endSelectedLine.setEnabled(True)
        self.periodLine.setEnabled(True)
        self.timeRangeSlider.setEnabled(True)

    def checkPeriod(self):
        print(__name__, inspect.currentframe().f_code.co_name)

        period = self.periodLine.value()

        errorMessage = ('Period should be in the range:\n'
                        + f'1 s ≤ period < {self.selectedTime} s')

        if period > self.selectedTime:
                self.errorWarning(self.periodLine, errorMessage)
                period = self.selectedTime

        self.updatePeriod(period)

    def checkStartSelected(self):
        print(__name__, inspect.currentframe().f_code.co_name)

        start = self.startSelectedLine.value()

        errorMessage = ('Start time should be in the range:\n'
                        + f"0 s ≤ start time < {self.timeParams['endSelected']} s")

        # Selected start > Selected end, back to initial value
        if start >= self.timeParams['endSelected']:
            self.errorWarning(self.startSelectedLine, errorMessage)
            start = self.timeParams['startSelected']
            self.startSelectedLine.setValue(start)

        self.updateSelectedTime(start, self.timeParams['endSelected'])

    def checkEndSelected(self):
        print(__name__, inspect.currentframe().f_code.co_name)

        end = self.endSelectedLine.value()

        errorMessage = ('End time should be in the range:\n'
                        + f"{self.timeParams['startSelected']} s < end time ≤ {self.totalTime} s")

        # Selected end < Selected start, back to previous value
        if end <= self.timeParams['startSelected']:
            self.errorWarning(self.endSelectedLine, errorMessage)
            end = self.timeParams['endSelected']
            self.endSelectedLine.setValue(end)

        # # Selected end > total time, set Selected time to max total time #!!!
        # elif end > self.totalTime:
        #     self.errorWarning(self.endSelectedLine, errorMessage)
        #     end = self.totalTime
        #     self.endSelectedLine.setValue(end)

        self.updateSelectedTime(self.timeParams['startSelected'], end)

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

        start, end = [x/10 for x in value]

        # Update values in text editors based on slider. Block their signals
        with QSignalBlocker(self.startSelectedLine):
            self.startSelectedLine.setValue(start)
        with QSignalBlocker(self.endSelectedLine):
            self.endSelectedLine.setValue(end)

        self.window.map.updateMapPath(start, end)
        # Do not update SelectedTime values here while slider is being moved

    def updateSelectedTime(self, start=None, end=None):
        print(__name__, inspect.currentframe().f_code.co_name)

        if start is None or end is None:
            start, end = self.timeRangeSlider.sliderPosition()
            start /= 10
            end /= 10

        self.timeParams['startSelected'] = start
        self.timeParams['endSelected'] = end

        # Update slider values based on text editors
        self.timeRangeSlider.setValue([start*10, end*10])

        oldSelectedTime = self.selectedTime
        self.selectedTime = round(end - start, 1)
        self.selectedTimeLabel.setText(f'Selected time: {self.selectedTime} seconds')

        period = self.timeParams['period']
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
        self.timeParams['period'] = period

        self.window.table.fillTable()

class DoubleSpinBox(QDoubleSpinBox):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def fixup(self, text):
        if self.correctionMode == 'min':
            self.setValue(self.minimum())
        elif self.correctionMode == 'max':
            self.setValue(self.maximum())

    def setCorrectionMode(self, correctionMode):
        self.correctionMode = correctionMode

    def wheelEvent(self, event):
        event.ignore()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Up or event.key() == Qt.Key.Key_Down:
            event.ignore()
        else:
            super().keyPressEvent(event)
