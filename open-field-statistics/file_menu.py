import os
import copy
import json
import inspect
import pandas as pd
import numpy as np

from PyQt6.QtWidgets import (QFileDialog, QMessageBox,
                             QLabel, QPushButton)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFontMetrics, QAction


class File:
    def __init__(self, window):
        print(__class__.__name__, inspect.currentframe().f_code.co_name)

        self.window = window
        self.params = self.window.settings.params

        self.hasDataFile = False

        self.dataFilters = '''CSV (comma delimited) (*.csv)'''#;;
                              # Text (tab delimited) (*.txt);;
                              # Excel Workbook (*.xlsx)'''  #TODO

        self.setButtons()

    def setButtons(self):
        print(__class__.__name__, inspect.currentframe().f_code.co_name)

        self.loadFileButton = QPushButton('Select data')
        self.loadFileButton.setFixedWidth(80)

        self.fileNameLabel = QLabel()

        self.saveDataButton = QPushButton('Save data')
        self.saveDataButton.setFixedWidth(80)
        self.saveDataButton.setDisabled(True)

        self.loadFileButton.clicked.connect(self.loadData)
        self.saveDataButton.clicked.connect(self.saveData)

    def setFileMenu(self, menu):
        print(__class__.__name__, inspect.currentframe().f_code.co_name)

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

    def loadData(self, loadDataFile=None, defaultTimeVariables=True):
        print(__class__.__name__, inspect.currentframe().f_code.co_name)

        ''' Load raw data file, get statistics, update map and table '''

        # Open FileDialog if it is original 'Load raw data' call.
        # Do not open FileDialog for reloading the same data file for new params
        # isNewDataFile = False
        if not loadDataFile:
            loadDataFile, filter = QFileDialog.getOpenFileName(
                parent=self.window,
                caption=self.fileItems.loc['loadData', 'caption'],
                directory=self.params['dirs']['loadData'],
                filter=self.dataFilters
                )
            # FileDialog was exited with cancel
            if not loadDataFile:
                return
            # isNewDataFile = True
        self.hasDataFile = True

        raw_df = pd.read_csv(
            loadDataFile,
            sep=None,   # Uses 'csv.Sniffer' for decimal separator,
            # needs python engine
            engine='python',
            # engine='c',  # Needs specified decimal separator
            parse_dates=[0], date_format='%H:%M:%S.%f',
            names=['time', 'x1', 'x2', 'y1', 'y2', 'z'], header=0,
            index_col=0
            )

        # Check if data correspond to field settings
        maxX, maxY = self.window.stat.checkDataToField(raw_df)
        # Show warning message and abort if not
        if maxX or maxY:
            self.incorrectData(maxX, maxY)
            self.hasDataFile = False
            return

        self.window.stat.process_raw_data(raw_df)

        # If new data - update time variables to default (based on loaded data)
        if defaultTimeVariables:
            self.window.time.loadTimeVariables(self.window.stat)
        # If old data - skip loading default variables and directly load time widgets
        else:
            self.window.time.loadTimeWidgets()

        # Update path on map
        self.window.map.updateMapPath(
            self.window.time.timeParams['startSelected'],
            self.window.time.timeParams['endSelected'])

        # Get statistics and fill the table
        self.window.table.fillTable()

        # After raw data were loaded, allow saving output data
        self.fileItems.loc['saveData', 'action'].setEnabled(True)
        # self.fileItems.loc['saveMap', 'action'].setEnabled(True) #TODO
        self.saveDataButton.setEnabled(True)

        # Reuse file name later to suggest name for output statistics file,
        # and to reload this data if they fit a new params file
        self.loadDataFile = loadDataFile
        self.updateDataFileNameLabel(self.loadDataFile)

    def incorrectData(self, maxX, maxY):
        print(__class__.__name__, inspect.currentframe().f_code.co_name)

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

    def updateDataFileNameLabel(self, loadDataFile):
        print(__class__.__name__, inspect.currentframe().f_code.co_name)

        metrix = QFontMetrics(self.fileNameLabel.font())
        width = self.fileNameLabel.width() - 2;
        clippedDataFileName = metrix.elidedText(loadDataFile,
                                                Qt.TextElideMode.ElideMiddle, width)
        self.fileNameLabel.setText(clippedDataFileName)

    def deleteData(self):
        print(__class__.__name__, inspect.currentframe().f_code.co_name)

        ''' If numLasers parameter was changed - reset zoneCoord '''

        self.updateDataFileNameLabel('')

        self.window.map.deleteMapButtons()
        self.window.time.deleteTime()

    def loadParams(self):
        print(__class__.__name__, inspect.currentframe().f_code.co_name)

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

        # Check if old data (if any) can be used with new parameters.
        #TIP If new field params differ from data's field params - DISCARD DATA
        if self.hasDataFile:
            # All field params are the same as before?
            for param in ['numLasersX', 'numLasersY', 'boxSideX', 'boxSideY']:
                if params['settings'][param] != self.window.settings.params[param]:
                    self.hasDataFile = False
                    break

        # Update settings
        self.window.settings.params.update(params['settings'])

        # Delete data in any case, bring field and time params to defaults
        # according to the new settings
        self.deleteData()

        # Update zoneCoord, implement zone map from new parameters
        self.window.map.zoneCoord[:, :] = params['zoneCoord']
        self.window.map.loadMap()

        # Update time parameters and load back existing data (if appropriate)
        if self.hasDataFile:
            #TIP If new time params are incompatible with data - DISCARD TIME PARAMS
            defaultTimeVariables = True
            # endSelected of new parameters is no more than totalTime of old data?
            if params['timeParams']['endSelected'] <= self.window.time.totalTime:
                self.window.time.timeParams.update(params['timeParams'])
                defaultTimeVariables = False

            self.loadData(self.loadDataFile, defaultTimeVariables)
            return  # fillTable will be called from loadData() in this case

        # Fill table with empty dataframe
        self.window.table.fillTable()

    def saveData(self):
        print(__class__.__name__, inspect.currentframe().f_code.co_name)

        # Take loadDataFile's name and drop file extension
        self.loadDataFileName = os.path.splitext(
                                    os.path.basename(self.loadDataFile))[0]
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
        print(__class__.__name__, inspect.currentframe().f_code.co_name)

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
