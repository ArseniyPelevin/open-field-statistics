import pandas as pd
import json
import os
import inspect

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QFileDialog, QToolTip,
    QLabel, QLineEdit, QPushButton, QButtonGroup, QSpacerItem,
    QVBoxLayout, QHBoxLayout, QGridLayout, QStackedLayout,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QStyleFactory,
    QDialog, QDialogButtonBox,
    QGroupBox, QCheckBox, QSpinBox, QDoubleSpinBox, QComboBox
)
from PyQt6.QtCore import (
    Qt, QSize, pyqtSlot, QEvent, QPointF, QVariantAnimation, QRegularExpression
    )
from PyQt6.QtGui import (
    QFontMetrics, QIcon,
    QPen, QPixmap, QPainter, QColor, QPalette,
    QRegularExpressionValidator, QIntValidator, QDoubleValidator
)

from superqt import QRangeSlider

ALL_STAT_PARAMS = ['time', 'dist', 'velocity', 'rearing_n', 'rearing_time']
DEFAULT_PARAMS = {
    'numLasersX': 16,
    'numLasersY': 16,
    'boxSideX': 40.,      # Physical dimensions of the filed, cm
    'boxSideY': 40.,
    'statParams': set(ALL_STAT_PARAMS),
    'samplingFrequency': 0.1,
    'startTime': 1,  # First beam break
    'separator': ';',
    'decimal': ','
    }


class Settings(QDialog):
    def __init__(self, window):
        print(__name__, inspect.currentframe().f_code.co_name)

        super().__init__(window)

        self.window = window
        self.loadParameters()


#TODO QTabBar
#https://doc.qt.io/qt-5/qtabwidget.html

    def loadParameters(self):
        if 'RecentParameters.json' in os.listdir():
            with open('RecentParameters.json', 'r', newline='') as file:
                self.params = json.load(file)
                self.params['statParams'] = set(self.params['statParams'])
        else:
            self.params = DEFAULT_PARAMS

        self.window.params = self.params


    def settingsDialog(self):
        print(__name__, inspect.currentframe().f_code.co_name)

        self.tempParams = self.params.copy()

        self.setWindowTitle('Settings')

        dialogButtons = QDialogButtonBox.Save | QDialogButtonBox.Cancel

        self.buttonBox = QDialogButtonBox(dialogButtons)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        self.layout = QVBoxLayout(self)
        self.layout.addWidget(self.createFileGroup())
        self.layout.addWidget(self.createFieldParametersGroup())
        self.layout.addWidget(self.createStatisticsGroup())
        self.layout.addWidget(self.createSamplingGroup())
        self.layout.addWidget(self.createOutputFormatGroup())

        self.layout.addWidget(self.buttonBox)

        if self.exec():
            self.updateParameters()

    def updateParameters(self):
        #TODO statParams from booleans to Series

        self.params = self.tempParams.copy() #OK

        self.tempParams['statParams'] = list(self.tempParams['statParams'])

        with open('RecentParameters.json', 'w+', newline='') as file:
            json.dump(self.tempParams, file, indent='\t')

    def createFileGroup(self):
        fileGroup = QGroupBox('Default files locations')
        fileGroupLayout = QGridLayout(fileGroup)


        return fileGroup



    def createFieldParametersGroup(self):
        fieldParametersGroup = QGroupBox('Field parameters')
        fieldParametersGroupLayout = QGridLayout(fieldParametersGroup)

        numLasersXLabel = QLabel('Number of beams by horizontal axis')
        numLasersX = QSpinBox()
        numLasersX.setRange(1, 999) #TODO Test 1
        numLasersX.setValue(self.tempParams['numLasersX'])


        numLasersYLabel = QLabel('Number of beams by vertical axis')
        numLasersY = QSpinBox()
        numLasersY.setRange(1, 999)
        numLasersY.setValue(self.tempParams['numLasersY'])

        boxSideXLabel = QLabel('Horizontal field size (cm)')
        boxSideX = QDoubleSpinBox()
        boxSideX.setRange(1., 999.)
        boxSideX.setDecimals(2)
        boxSideX.setSuffix(' cm')
        boxSideX.setValue(self.tempParams['boxSideX'])

        boxSideYLabel = QLabel('Vertical field size (cm)')
        boxSideY = QDoubleSpinBox()
        boxSideY.setRange(1., 999.)
        boxSideY.setDecimals(2)
        boxSideY.setSuffix(' cm')
        boxSideY.setValue(self.tempParams['boxSideY'])

        numLasersX.valueChanged.connect(lambda val:
            self.tempParams.update({'numLasersX': val}))
        numLasersY.valueChanged.connect(lambda val:
            self.tempParams.update({'numLasersY': val}))
        boxSideX.valueChanged.connect(lambda val:
            self.tempParams.update({'boxSideX': val}))
        boxSideY.valueChanged.connect(lambda val:
            self.tempParams.update({'boxSideY': val}))

        fieldParametersGroupLayout.addWidget(numLasersXLabel, 0, 0)
        fieldParametersGroupLayout.addWidget(numLasersX, 0, 1)
        fieldParametersGroupLayout.addWidget(numLasersYLabel, 1, 0)
        fieldParametersGroupLayout.addWidget(numLasersY, 1, 1)
        fieldParametersGroupLayout.addWidget(boxSideXLabel, 2, 0)
        fieldParametersGroupLayout.addWidget(boxSideX, 2, 1)
        fieldParametersGroupLayout.addWidget(boxSideYLabel, 3, 0)
        fieldParametersGroupLayout.addWidget(boxSideY, 3, 1)

        return fieldParametersGroup

    def createStatisticsGroup(self):
        statisticsGroup = QGroupBox('Output statistics')
        statisticsGroupLayout = QVBoxLayout(statisticsGroup)

        time = QCheckBox('Time')
        time.setChecked('time' in self.tempParams['statParams'])
        dist = QCheckBox('Distance')
        dist.setChecked('dist' in self.tempParams['statParams'])
        velocity = QCheckBox('Velocity')
        velocity.setChecked('velocity' in self.tempParams['statParams'])
        rearingN = QCheckBox('Rearings number')
        rearingN.setChecked('rearing_n' in self.tempParams['statParams'])
        rearingTime = QCheckBox('Rearings time')
        rearingTime.setChecked('rearing_time' in self.tempParams['statParams'])

        time.toggled.connect(lambda checked:
            self.tempParams['statParams'].add('time') if checked
            else self.tempParams['statParams'].remove('time'))
        dist.toggled.connect(lambda checked:
            self.tempParams['statParams'].add('dist') if checked
            else self.tempParams['statParams'].remove('dist'))
        velocity.toggled.connect(lambda checked:
            self.tempParams['statParams'].add('velocity') if checked
            else self.tempParams['statParams'].remove('velocity'))
        rearingN.toggled.connect(lambda checked:
            self.tempParams['statParams'].add('rearing_n') if checked
            else self.tempParams['statParams'].remove('rearing_n'))
        rearingTime.toggled.connect(lambda checked:
            self.tempParams['statParams'].add('rearing_time') if checked
            else self.tempParams['statParams'].remove('rearing_time'))

        statisticsGroupLayout.addWidget(time)
        statisticsGroupLayout.addWidget(dist)
        statisticsGroupLayout.addWidget(velocity)
        statisticsGroupLayout.addWidget(rearingN)
        statisticsGroupLayout.addWidget(rearingTime)

        return statisticsGroup

    def createSamplingGroup(self):
        samplingGroup = QGroupBox('Sampling parameters')
        samplingGroupLayout = QGridLayout(samplingGroup)

        samplingFrequencyLabel = QLabel('Sampling frequency (s)')
        samplingFrequency = QDoubleSpinBox()
        samplingFrequency.setRange(0.1, 1)
        samplingFrequency.setSingleStep(0.1)
        samplingFrequency.setSuffix(' s')
        samplingFrequency.setValue(self.tempParams['samplingFrequency'])

        startTimeLabel = QLabel('Start time from: ')
        startTime = QComboBox()
        startTime.addItems(['Start of recording', 'First beam break'])
        startTime.setCurrentIndex(self.tempParams['startTime'])

        samplingFrequency.valueChanged.connect(lambda val:
           self.tempParams.update({'samplingFrequency': val}))
        startTime.currentIndexChanged.connect(lambda val:
           self.tempParams.update({'startTime': val}))

        samplingGroupLayout.addWidget(samplingFrequencyLabel, 0, 0)
        samplingGroupLayout.addWidget(samplingFrequency, 0, 1)
        samplingGroupLayout.addWidget(startTimeLabel, 1, 0)
        samplingGroupLayout.addWidget(startTime, 1, 1)

        return samplingGroup

    def createOutputFormatGroup(self):
        outputFormatGroup = QGroupBox('Output format')
        outputFormatGroupLayout = QGridLayout(outputFormatGroup)

        separatorLabel = QLabel('Output separator')
        separator = QLineEdit()
        separator.setMaxLength(1)
        separator.setFixedWidth(20)
        separator.setText(self.tempParams['separator'])

        decimalLabel = QLabel('Output decimal point')
        decimal = QLineEdit()
        decimal.setMaxLength(1)
        decimal.setFixedWidth(20)
        decimal.setText(self.tempParams['decimal'])

        separator.textEdited.connect(lambda val:
            self.tempParams.update({'separator': val}))
        decimal.textEdited.connect(lambda val:
            self.tempParams.update({'decimal': val}))

        outputFormatGroupLayout.addWidget(separatorLabel, 0, 0)
        outputFormatGroupLayout.addWidget(separator, 0, 1)
        outputFormatGroupLayout.addWidget(decimalLabel, 1, 0)
        outputFormatGroupLayout.addWidget(decimal, 1, 1)

        return outputFormatGroup

    # def setParam(self, key, value):
    #     self.params[key] = value
    #     print(self.params)
