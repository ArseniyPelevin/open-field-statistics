import json
import os
import inspect
import copy
import numpy as np
import pandas as pd

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QFileDialog, QToolTip,
    QLabel, QLineEdit, QPushButton, QButtonGroup, QSpacerItem,
    QVBoxLayout, QHBoxLayout, QGridLayout, QStackedLayout,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QStyleFactory,
    QDialog, QDialogButtonBox,
    QGroupBox, QCheckBox, QSpinBox, QDoubleSpinBox, QComboBox, QMessageBox
)
from PyQt6.QtCore import (
    Qt, QSize, pyqtSlot, QEvent, QPointF, QVariantAnimation, QRegularExpression, QDir
    )
from PyQt6.QtGui import (
    QFontMetrics, QIcon,
    QPen, QPixmap, QPainter, QColor, QPalette,
    QRegularExpressionValidator, QIntValidator, QDoubleValidator, QAction
)

from superqt import QRangeSlider

class File:
    def __init__(self, window):
        print(__name__, inspect.currentframe().f_code.co_name)

        self.window = window
        self.params = self.window.settings.params

        self.dataFilters = '''CSV (comma delimited) (*.csv)'''#;;
                              # Text (tab delimited) (*.txt);;
                              # Excel Workbook (*.xlsx)'''  #TODO

        self.setButtons()

    def setButtons(self):
        print(__name__, inspect.currentframe().f_code.co_name)

        self.loadFileButton = QPushButton('Select data')
        self.loadFileButton.setFixedWidth(80)

        self.fileNameLabel = QLabel()

        self.saveDataButton = QPushButton('Save data')
        self.saveDataButton.setFixedWidth(80)
        self.saveDataButton.setDisabled(True)

        self.loadFileButton.clicked.connect(self.loadData)
        self.saveDataButton.clicked.connect(self.saveData)

    def setFileMenu(self, menu):
        print(__name__, inspect.currentframe().f_code.co_name)

        fileMenu = menu.addMenu('File')

        files = ['loadData', 'loadParams', 'saveData', 'saveParams', 'saveMap']
        items = ['caption', 'action', 'slot']
        self.fileItems = pd.DataFrame(index=files, columns=items)
        self.fileItems.loc[:, ['caption', 'slot']] = [
            ['Load raw data', self.loadData],
            ['Load parameters', self.loadParams],
            ['Save statistics', self.saveData],
            ['Save parameters', self.saveParams],
            ['Save map as image', self.saveMap]
            ]

        for file in files:
            # Create QAction objects
            self.fileItems.loc[file, 'action'] = QAction(
                self.fileItems.loc[file, 'caption'])

            # Set signals
            self.fileItems.loc[file, 'action'].triggered.connect(
                lambda _checked, file_=file: self.fileItems.loc[file_, 'slot']())

            # Add actions to fileMenu
            fileMenu.addAction(self.fileItems.loc[file, 'action'])

        fileMenu.insertSeparator(self.fileItems.loc['saveData', 'action'])

        # Do not allow to save output data before raw data were loaded
        self.fileItems.loc['saveData', 'action'].setDisabled(True)
        self.fileItems.loc['saveMap', 'action'].setDisabled(True)

    def loadData(self):
        print(__name__, inspect.currentframe().f_code.co_name)

        ''' Load raw data file, get statistics, update map and table '''

        # Make raw data file's name an atribute
        # to suggest name for output statistics file
        self.loadDataFile, filter = QFileDialog.getOpenFileName(
            parent=self.window,
            caption=self.fileItems.loc['loadData', 'caption'],
            directory=self.params['dirs']['loadData'],
            filter=self.dataFilters
            )

        # FileDialog was exited with cancel
        if not self.loadDataFile:
            return

        self.raw_df = pd.read_csv(
            self.loadDataFile,
            sep=None,   # Uses 'csv.Sniffer' for decimal separator,
            # needs python engine
            engine='python',
            # engine='c',  # Needs specified decimal separator
            parse_dates=[0], date_format='%H:%M:%S.%f',
            names=['time', 'x1', 'x2', 'y1', 'y2', 'z'], header=0,
            index_col=0
            )

        # Data are incompatible to current parameters
        if not self.updateData():
            return

        # Set file name label
        metrix = QFontMetrics(self.fileNameLabel.font())
        width = self.fileNameLabel.width() - 2;
        clippedText = metrix.elidedText(self.loadDataFile, Qt.ElideMiddle, width)
        self.fileNameLabel.setText(clippedText)

        # After raw data were loaded, allow saving output data
        self.fileItems.loc['saveData', 'action'].setEnabled(True)
        # self.fileItems.loc['saveMap', 'action'].setEnabled(True) #TODO
        self.saveDataButton.setEnabled(True)

    def updateData(self):
        print(__name__, inspect.currentframe().f_code.co_name)

        if hasattr(self, 'loadDataFile') and self.loadDataFile:
            maxX, maxY = self.window.stat.read(self.raw_df) #??? attr here?
            # Check if data correspond to field settings
            if maxX or maxY:
                self.incorrectData(maxX, maxY)
                return False

            # Update time variables based on loaded data
            self.window.time.loadTimeVariables(self.window.stat)

            # Update path on map
            self.window.map.updateMapPath(
                self.window.time.timeParams['startSelected'],
                self.window.time.timeParams['endSelected'])

        # Get statistics and fill the table
        self.window.table.fillTable()

        # Confirm to sender (loadData or loadParams) that data are correct
        return True

    def incorrectData(self, maxX, maxY):
        print(__name__, inspect.currentframe().f_code.co_name)

        warningMessage = ('Loaded raw data do not correspond to the '
                          + 'field parameters specified:\n\n')
        if maxX:
            warningMessage += (
                'Number of beams by the horizontal (X) axis'
                + f' is set to {self.params["numLasersX"]},\n'
                + f'but the loaded raw data contain X values up to {maxX}.\n\n')
        if maxY:
            warningMessage += (
                'Number of beams by the vertical (Y) axis'
                + f' is set to {self.params["numLasersY"]},\n'
                + f'but the loaded raw data contain Y values up to {maxY}.\n\n')
        warningMessage += 'Change beam parameters or load another raw data file.'

        QMessageBox.warning(self.window, 'Incorrect raw data', warningMessage)

    def loadParams(self, loadParamsFile=None):
        print(__name__, inspect.currentframe().f_code.co_name)

        # Called to open FileDialog, not to load recentSettings
        if not loadParamsFile:
            loadParamsFile, _filter = QFileDialog.getOpenFileName(
                parent=self.window,
                caption=self.fileItems.loc['loadParams', 'caption'],
                directory=self.params['dirs']['params'],
                filter='JSON (*.json)'
                )

        # FileDialog was exited with cancel
        if not loadParamsFile:
            return

        with open(loadParamsFile, 'r', newline='') as file:
            params = json.load(file)

        # Update settings
        self.window.settings.params.update(params['settings'])

        # Update map
        self.window.map.zoneCoord.resize((self.params['numLasersY'],
                                          self.params['numLasersX']),
                                         refcheck=False)
        self.window.map.zoneCoord[:, :] = params['zoneCoord']
        self.window.map.deleteMap()
        self.window.map.loadMap()

        # Update time (if data were loaded and correspond to timeParams)
        if (self.window.stat.has_file and
           params['timeParams']['endSelected'] <= self.window.time.totalTime):
            self.window.time.timeParams.update(params['timeParams'])

        self.updateData()

    def saveData(self):
        print(__name__, inspect.currentframe().f_code.co_name)

        # Take loadDataFile's name and drop file extension
        self.loadDataFileName = os.path.splitext(self.loadDataFile)[0]
        path = os.path.join(
            self.params['dirs']['saveData'],
            f"{self.loadDataFileName}_statistics")

        saveDataFile, filter = QFileDialog.getSaveFileName(
            parent=self.window,
            caption=self.fileItems.loc['saveData', 'caption'],
            directory=path,
            filter=self.dataFilters
            )

        # FileDialog was exited with cancel
        if not saveDataFile:
            return

        with open(saveDataFile, 'w+', newline='') as file:
            self.window.stat.data.to_csv(file,
                                         sep=self.params['separator'],
                                         decimal=self.params['decimal'])

    def saveParams(self, saveParamsFile=None):
        print(__name__, inspect.currentframe().f_code.co_name)

        # File was not provided by sender
        # (as if called from Settings.saveRecentSettings)
        if not saveParamsFile:
            saveParamsFile, _filter = QFileDialog.getSaveFileName(
                parent=self.window,
                caption=self.fileItems.loc['saveParams', 'caption'],
                directory=self.params['dirs']['params'],
                filter='JSON (*.json)'
                )
            # FileDialog was exited with cancel
            if not saveParamsFile:
                return

        params = {}
        params['settings'] = copy.deepcopy(self.params)
        params['zoneCoord'] = self.window.map.zoneCoord.tolist()
        params['timeParams'] = self.window.time.timeParams.copy()

        with open(saveParamsFile, 'w+', newline='') as file:
            json.dump(params, file, indent='\t')

    def saveMap(self):
        pass  #TODO
