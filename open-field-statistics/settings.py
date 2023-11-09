import json
import os
import copy
import inspect
import numpy as np
import pandas as pd

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
    Qt, QSize, pyqtSlot, QEvent, QPointF, QVariantAnimation, QRegularExpression, QDir
    )
from PyQt6.QtGui import (
    QFontMetrics, QIcon,
    QPen, QPixmap, QPainter, QColor, QPalette,
    QRegularExpressionValidator, QIntValidator, QDoubleValidator, QKeySequence
)

from superqt import QRangeSlider

DEFAULT_FOLDER_TYPES = ['loadData', 'params', 'saveData', 'saveMap']
ALL_STAT_PARAMS = ['time', 'dist', 'velocity', 'rearing_n', 'rearing_time']
DEFAULT_SETTINGS = {
    # File parameters:
    'dirs': {folder: None for folder in DEFAULT_FOLDER_TYPES},

    # Field parameters:
    'numLasersX': 16,
    'numLasersY': 16,
    'boxSideX': 40.,      # Physical dimensions of the filed, cm
    'boxSideY': 40.,

    # Statistics parameters
    'statParams': ALL_STAT_PARAMS,

    # Sampling parameters
    'samplingFrequency': 0.1,
    'startTime': 1,  # First beam break

    # Output parameters:
    'separator': ';',
    'decimal': ','
    }



class Settings():
    def __init__(self, window):
        print(__name__, inspect.currentframe().f_code.co_name)

        self.window = window
        self.params = self.loadRecentSettings()

#TODO QTabBar ?
#https://doc.qt.io/qt-5/qtabwidget.html

    def loadRecentSettings(self):
        print(__name__, inspect.currentframe().f_code.co_name)

        if 'recent_settings.json' in os.listdir('temp'):
            path = os.path.join('temp', 'recent_settings.json')
            with open(path, 'r', newline='') as file:
                recentSettings = json.load(file)
        else:
            recentSettings = DEFAULT_SETTINGS

        return recentSettings

        # self.window.params.update(recentSettings)  #!!!

    def openSettingsDialog(self):
        print(__name__, inspect.currentframe().f_code.co_name)

        self.settingsDialog = self.SettingsDialog(self.window, self.params)
        newSettings = self.settingsDialog.show()
        if newSettings:
            self.params.update(newSettings)
            if self.settingsDialog.fieldParameterChanged:
                self.clearZoneCoord()
            self.window.file.updateData()
            self.saveRecentSettings()

    def clearZoneCoord(self):  #???
        print(__name__, inspect.currentframe().f_code.co_name)

        ''' If numLasers parameter was changed - reset zoneCoord '''

        # Change size of zoneCoord and fill it with zeros in-place
        self.window.map.zoneCoord.resize((self.params['numLasersY'],
                                          self.params['numLasersX']),
                                         refcheck=False)
        self.window.map.zoneCoord[:, :] = np.zeros((self.params['numLasersY'],
                                                    self.params['numLasersX']),
                                                   dtype=int)
        self.window.map.deleteMap()
        self.window.map.loadMap()

    def saveRecentSettings(self):
        print(__name__, inspect.currentframe().f_code.co_name)

        path = os.path.join('temp', 'recent_settings.json')
        with open(path, 'w+', newline='') as file:
            json.dump(self.params, file)


    class SettingsDialog(QDialog):
        def __init__(self, window, settings):
            print(__name__, inspect.currentframe().f_code.co_name)

            super().__init__(window)

            # self.tempSettings = copy.deepcopy(window.params)  #!!!
            self.tempSettings = copy.deepcopy(settings)

            self.fieldParameterChanged = False

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

        def show(self):
            print(__name__, inspect.currentframe().f_code.co_name)

            if self.exec():
                return copy.deepcopy(self.tempSettings)
            else:
                self.fieldParameterChanged = False

        def createFileGroup(self):
            print(__name__, inspect.currentframe().f_code.co_name)

            fileGroup = QGroupBox('Default files locations')
            fileGroupLayout = QGridLayout(fileGroup)

            folders = DEFAULT_FOLDER_TYPES
            items = ['caption', 'label', 'lineEdit', 'button', 'dialog']
            self.folderItems = pd.DataFrame(index=folders, columns=items)

            self.folderItems.loc[:, 'caption'] = [
                'Location of input raw data files:',
                'Location of saved parameters:',
                'Location of output statistics:',
                'Location of output map image:'
                ]

            for folder in folders:
                # Create label
                self.folderItems.loc[folder, 'label'] = QLabel(
                    self.folderItems.loc[folder, 'caption'])
                # Create LineEdit to write default folders path
                self.folderItems.loc[folder, 'lineEdit'] = QLineEdit()
                self.folderItems.loc[folder, 'lineEdit'].setFixedWidth(300)
                self.folderItems.loc[folder, 'lineEdit'].setText(
                    self.tempSettings['dirs'][folder])
                # Create buttons to select default folders
                self.folderItems.loc[folder, 'button'] = QPushButton('...')
                self.folderItems.loc[folder, 'button'].setFixedWidth(20)
                # Create dialog for folder selection
                self.folderItems.loc[folder, 'dialog'] = QFileDialog()

                # Set signals of LineEdit and button
                self.folderItems.loc[folder, 'lineEdit'].editingFinished.connect(
                    lambda folder_=folder:
                        self.tempSettings['dirs'].update(
                            {folder_:
                             self.folderItems.loc[folder_, 'lineEdit'].text()}))
                self.folderItems.loc[folder, 'button'].clicked.connect(
                    lambda _checked, folder_=folder:
                        self.tempSettings['dirs'].update(
                            {folder_: self.selectFolder(folder_)}))

                # Add created widgets to fileGroupLayout
                lineNum = 2 * self.folderItems.index.get_loc(folder)
                fileGroupLayout.addWidget(self.folderItems.loc[folder, 'label'],
                                          lineNum, 0)
                fileGroupLayout.addWidget(self.folderItems.loc[folder, 'lineEdit'],
                                          lineNum + 1, 0)
                fileGroupLayout.addWidget(self.folderItems.loc[folder, 'button'],
                                          lineNum + 1, 1)

            return fileGroup

        def selectFolder(self, folder):
            print(__name__, inspect.currentframe().f_code.co_name)

            folderName = self.folderItems.loc[folder, 'dialog'].getExistingDirectory(
                parent=self,
                caption=self.folderItems.loc[folder, 'caption'],
                directory=self.tempSettings['dirs'][folder]
                )
            if folderName:
                self.tempSettings['dirs'][folder] = folderName
                self.folderItems.loc[folder, 'lineEdit'].setText(folderName)
            return folderName


        def createFieldParametersGroup(self):
            print(__name__, inspect.currentframe().f_code.co_name)

            fieldParametersGroup = QGroupBox('Field parameters')
            fieldParametersGroupLayout = QGridLayout(fieldParametersGroup)

            numLasersXLabel = QLabel('Number of beams by horizontal axis')
            numLasersX = QSpinBox()
            numLasersX.setRange(1, 999) #TODO Test 1
            numLasersX.setValue(self.tempSettings['numLasersX'])


            numLasersYLabel = QLabel('Number of beams by vertical axis')
            numLasersY = QSpinBox()
            numLasersY.setRange(1, 999)
            numLasersY.setValue(self.tempSettings['numLasersY'])

            boxSideXLabel = QLabel('Horizontal field size (cm)')
            boxSideX = QDoubleSpinBox()
            boxSideX.setRange(1., 999.)
            boxSideX.setDecimals(1)
            boxSideX.setSuffix(' cm')
            boxSideX.setValue(self.tempSettings['boxSideX'])

            boxSideYLabel = QLabel('Vertical field size (cm)')
            boxSideY = QDoubleSpinBox()
            boxSideY.setRange(1., 999.)
            boxSideY.setDecimals(1)
            boxSideY.setSuffix(' cm')
            boxSideY.setValue(self.tempSettings['boxSideY'])

            numLasersX.valueChanged.connect(lambda val:
                self.updateFieldParameter('numLasersX', val))
            numLasersY.valueChanged.connect(lambda val:
                self.updateFieldParameter('numLasersY', val))
            boxSideX.valueChanged.connect(lambda val:
                self.updateFieldParameter('boxSideX', val))
            boxSideY.valueChanged.connect(lambda val:
                self.updateFieldParameter('boxSideY', val))

            fieldParametersGroupLayout.addWidget(numLasersXLabel, 0, 0)
            fieldParametersGroupLayout.addWidget(numLasersX, 0, 1)
            fieldParametersGroupLayout.addWidget(numLasersYLabel, 1, 0)
            fieldParametersGroupLayout.addWidget(numLasersY, 1, 1)
            fieldParametersGroupLayout.addWidget(boxSideXLabel, 2, 0)
            fieldParametersGroupLayout.addWidget(boxSideX, 2, 1)
            fieldParametersGroupLayout.addWidget(boxSideYLabel, 3, 0)
            fieldParametersGroupLayout.addWidget(boxSideY, 3, 1)

            return fieldParametersGroup

        def updateFieldParameter(self, parameter, value):
            print(__name__, inspect.currentframe().f_code.co_name)

            self.tempSettings.update({parameter: value})
            self.fieldParameterChanged = True

        def createStatisticsGroup(self):
            print(__name__, inspect.currentframe().f_code.co_name)

            statisticsGroup = QGroupBox('Output statistics')
            statisticsGroupLayout = QVBoxLayout(statisticsGroup)

            time = QCheckBox('Time')
            time.setChecked('time' in self.tempSettings['statParams'])
            dist = QCheckBox('Distance')
            dist.setChecked('dist' in self.tempSettings['statParams'])
            velocity = QCheckBox('Velocity')
            velocity.setChecked('velocity' in self.tempSettings['statParams'])
            rearingN = QCheckBox('Rearings number')
            rearingN.setChecked('rearing_n' in self.tempSettings['statParams'])
            rearingTime = QCheckBox('Rearings time')
            rearingTime.setChecked('rearing_time' in self.tempSettings['statParams'])

            time.toggled.connect(lambda checked:
                self.tempSettings['statParams'].append('time') if checked
                else self.tempSettings['statParams'].remove('time'))
            dist.toggled.connect(lambda checked:
                self.tempSettings['statParams'].append('dist') if checked
                else self.tempSettings['statParams'].remove('dist'))
            velocity.toggled.connect(lambda checked:
                self.tempSettings['statParams'].append('velocity') if checked
                else self.tempSettings['statParams'].remove('velocity'))
            rearingN.toggled.connect(lambda checked:
                self.tempSettings['statParams'].append('rearing_n') if checked
                else self.tempSettings['statParams'].remove('rearing_n'))
            rearingTime.toggled.connect(lambda checked:
                self.tempSettings['statParams'].append('rearing_time') if checked
                else self.tempSettings['statParams'].remove('rearing_time'))

            statisticsGroupLayout.addWidget(time)
            statisticsGroupLayout.addWidget(dist)
            statisticsGroupLayout.addWidget(velocity)
            statisticsGroupLayout.addWidget(rearingN)
            statisticsGroupLayout.addWidget(rearingTime)

            return statisticsGroup

        def createSamplingGroup(self):
            print(__name__, inspect.currentframe().f_code.co_name)

            samplingGroup = QGroupBox('Sampling parameters')
            samplingGroupLayout = QGridLayout(samplingGroup)

            samplingFrequencyLabel = QLabel('Sampling frequency (s)')
            samplingFrequency = QDoubleSpinBox()
            samplingFrequency.setRange(0.1, 1)
            samplingFrequency.setSingleStep(0.1)
            samplingFrequency.setSuffix(' s')
            samplingFrequency.setValue(self.tempSettings['samplingFrequency'])

            startTimeLabel = QLabel('Start time from: ')
            startTime = QComboBox()
            startTime.addItems(['Start of recording', 'First beam break'])
            startTime.setCurrentIndex(self.tempSettings['startTime'])

            samplingFrequency.valueChanged.connect(lambda val:
               self.tempSettings.update({'samplingFrequency': val}))
            startTime.currentIndexChanged.connect(lambda val:
               self.tempSettings.update({'startTime': val}))

            samplingGroupLayout.addWidget(samplingFrequencyLabel, 0, 0)
            samplingGroupLayout.addWidget(samplingFrequency, 0, 1)
            samplingGroupLayout.addWidget(startTimeLabel, 1, 0)
            samplingGroupLayout.addWidget(startTime, 1, 1)

            return samplingGroup

        def createOutputFormatGroup(self):
            print(__name__, inspect.currentframe().f_code.co_name)

            outputFormatGroup = QGroupBox('Output format')
            outputFormatGroupLayout = QGridLayout(outputFormatGroup)

            separatorLabel = QLabel('Output separator')
            separator = QLineEdit()
            separator.setMaxLength(1)
            separator.setFixedWidth(20)
            separator.setText(self.tempSettings['separator'])

            decimalLabel = QLabel('Output decimal point')
            decimal = QLineEdit()
            decimal.setMaxLength(1)
            decimal.setFixedWidth(20)
            decimal.setText(self.tempSettings['decimal'])

            separator.textEdited.connect(lambda val:
                self.tempSettings.update({'separator': val}))
            decimal.textEdited.connect(lambda val:
                self.tempSettings.update({'decimal': val}))

            outputFormatGroupLayout.addWidget(separatorLabel, 0, 0)
            outputFormatGroupLayout.addWidget(separator, 0, 1)
            outputFormatGroupLayout.addWidget(decimalLabel, 1, 0)
            outputFormatGroupLayout.addWidget(decimal, 1, 1)

            return outputFormatGroup

        def keyPressEvent(self, event):
            if event.matches(QKeySequence.Cancel):
                self.reject()
            else:
                event.ignore()
