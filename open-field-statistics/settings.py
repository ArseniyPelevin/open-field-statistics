import os
import copy
import json
import inspect
import pandas as pd

from PyQt6.QtWidgets import (
    QDialog, QFileDialog, QDialogButtonBox,
    QLabel, QLineEdit, QPushButton,
    QVBoxLayout, QGridLayout,
    QGroupBox, QCheckBox, QSpinBox, QDoubleSpinBox, QComboBox
)
from PyQt6.QtGui import QKeySequence

from superqt import QRangeSlider


DEFAULT_FOLDER_TYPES = ['loadData', 'params', 'saveData', 'saveMap']
FIELD_PARAMETERS = ['numLasersX', 'numLasersY', 'boxSideX', 'boxSideY']
ALL_STAT_PARAMS = ['time', 'dist_total', 'dist_amb', 'velocity',
                   'rearing_n', 'rearing_time']
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

    # Output parameters:
    'separator': ';',
    'decimal': ','
    }


class Settings():
    def __init__(self, window):
        print(__class__.__name__, inspect.currentframe().f_code.co_name)

        self.window = window
        self.params = self.loadRecentSettings()

#TODO QTabBar ?
#https://doc.qt.io/qt-5/qtabwidget.html

    def loadRecentSettings(self):
        print(__class__.__name__, inspect.currentframe().f_code.co_name)

        if 'recent_settings.json' in os.listdir('temp'):
            path = os.path.join('temp', 'recent_settings.json')
            with open(path, 'r', newline='') as file:
                recentSettings = json.load(file)
        else:
            recentSettings = DEFAULT_SETTINGS

        return recentSettings

    def openSettingsDialog(self):
        print(__class__.__name__, inspect.currentframe().f_code.co_name)

        self.settingsDialog = self.SettingsDialog(self.window, self.params)
        newSettings = self.settingsDialog.show()
        if newSettings:
            newSettings['statParams'].sort(key = lambda i: ALL_STAT_PARAMS.index(i))
            self.params.update(newSettings)
            if self.settingsDialog.fieldParameterChanged:
                self.window.file.deleteData()
                self.window.file.hasDataFile = False
                self.window.map.loadMap()
            self.window.table.fillTable()
            self.saveRecentSettings()

    def saveRecentSettings(self):
        print(__class__.__name__, inspect.currentframe().f_code.co_name)

        path = os.path.join('temp', 'recent_settings.json')
        with open(path, 'w+', newline='') as file:
            json.dump(self.params, file, indent='\t')


    class SettingsDialog(QDialog):
        def __init__(self, window, settings):
            print(__class__.__name__, inspect.currentframe().f_code.co_name)

            super().__init__(window)

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
            self.layout.addWidget(self.createOutputFormatGroup())

            self.layout.addWidget(self.buttonBox)

        def show(self):
            print(__class__.__name__, inspect.currentframe().f_code.co_name)

            if self.exec():
                return copy.deepcopy(self.tempSettings)
            else:
                self.fieldParameterChanged = False

        def createFileGroup(self):
            print(__class__.__name__, inspect.currentframe().f_code.co_name)

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
            print(__class__.__name__, inspect.currentframe().f_code.co_name)

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
            print(__class__.__name__, inspect.currentframe().f_code.co_name)

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
            print(__class__.__name__, inspect.currentframe().f_code.co_name)

            self.tempSettings.update({parameter: value})
            self.fieldParameterChanged = True

        def createStatisticsGroup(self):
            print(__class__.__name__, inspect.currentframe().f_code.co_name)

            statisticsGroup = QGroupBox('Output statistics')
            statisticsGroupLayout = QVBoxLayout(statisticsGroup)

            stats = ALL_STAT_PARAMS
            items = ['caption', 'checkBox']
            statItems = pd.DataFrame(index=stats, columns=items)

            statItems.loc[:, 'caption'] = [
                'Time',
                'Distance-total',
                'Distance-ambulatory',
                'Velocity',
                'Rearings number',
                'Rearings time'
                ]

            for stat in stats:
                statItems.loc[stat, 'checkBox'] = QCheckBox(
                    statItems.loc[stat, 'caption'])
                statItems.loc[stat, 'checkBox'].setChecked(
                    stat in self.tempSettings['statParams'])

                statItems.loc[stat, 'checkBox'].toggled.connect(
                    lambda checked, stat_=stat:
                    self.tempSettings['statParams'].append(stat_) if checked
                    else self.tempSettings['statParams'].remove(stat_))

                statisticsGroupLayout.addWidget(statItems.loc[stat, 'checkBox'])

            return statisticsGroup

        #??? Just trust some locale?
        def createOutputFormatGroup(self):
            print(__class__.__name__, inspect.currentframe().f_code.co_name)

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
