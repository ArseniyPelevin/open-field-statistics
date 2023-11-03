#!/usr/bin/env python3

import os
import pandas as pd
import inspect

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QStyleFactory, QFileDialog,
    QWidget, QLabel, QPushButton,
    QVBoxLayout, QHBoxLayout, QGridLayout, QSpacerItem,
    QMessageBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFontMetrics, QIcon, QAction

from superqt import QRangeSlider

from settings import Settings
from data_processing import DataProcessing
from field_map import MapWidget
from time_parameters import TimeParameters
from output_table import TableView
from app_info import Info


class MainWindow(QMainWindow):
    def __init__(self):
        print(__name__, inspect.currentframe().f_code.co_name)

        super().__init__()
        self.setWindowTitle('Open Field Statistics')
        self.setWindowIcon(QIcon('logo.ico'))

        # screen = app.primaryScreen().size()
        # self.setMaximumSize(screen)
        self.setGeometry(100, 100, 100, 100)

        # self.setVariables()
        self.setWidgets()

        self.params = {}
        self.settings = Settings(self)
        self.map = MapWidget(self)
        # self.map.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        self.time = TimeParameters(self)
        self.stat = DataProcessing(self.params, self.map.zoneCoord)
        self.table = TableView(self, app)

        self.setMenu()
        self.setSignals()
        self.setLayouts()

    # def setVariables(self):
        # self.mapSide = min(self.height(), self.width()/2) * 2/3


    def setWidgets(self):
        print(__name__, inspect.currentframe().f_code.co_name)

        self.getFileButton = QPushButton('Select file')
        self.getFileButton.setFixedWidth(80)
        self.fileNameLabel = QLabel()

        self.saveButton = QPushButton('Save data')
        self.saveButton.setFixedWidth(80)
        self.saveButton.setDisabled(True)

    def setMenu(self):
        print(__name__, inspect.currentframe().f_code.co_name)

        openData = QAction('Open raw data', self)
        openParameters = QAction('Open parameters', self)
        saveData = QAction('Save data', self)
        saveParameters = QAction('Save parameters', self)
        saveMap = QAction('Save map as image', self)

        openData.triggered.connect(self.getFile)
        openParameters.triggered.connect(lambda x: x)
        saveData.triggered.connect(lambda x: x)
        saveParameters.triggered.connect(lambda x: x)
        saveMap.triggered.connect(lambda x: x)

        settingsAction = QAction('Settings', self)
        settingsAction.triggered.connect(self.settings.settingsDialog)

        infoAction = QAction('Info', self)
        infoAction.triggered.connect(lambda: Info(self))

        menu = self.menuBar()

        fileMenu = menu.addMenu('File')
        fileMenu.addAction(openData)
        fileMenu.addAction(openParameters)
        fileMenu.addSeparator()
        fileMenu.addAction(saveData)
        fileMenu.addAction(saveParameters)
        fileMenu.addAction(saveMap)

        menu.addAction(settingsAction)
        menu.addAction(infoAction)

    def setSignals(self):
        print(__name__, inspect.currentframe().f_code.co_name)

        self.getFileButton.clicked.connect(self.getFile)
        self.saveButton.clicked.connect(self.table.saveData)

    def setLayouts(self):
        print(__name__, inspect.currentframe().f_code.co_name)

        self.controlLayout = QGridLayout()
        self.controlLayout.addWidget(self.getFileButton, 0, 0, 1, 1, Qt.AlignLeft)
        self.controlLayout.addWidget(self.fileNameLabel, 0, 1, 1, 2)
        self.controlLayout.addWidget(self.map.addZoneBtn, 1, 1, 1, 1, Qt.AlignRight)
        self.controlLayout.addLayout(self.map.areaBtnLayout, 2, 0, 1, 1, Qt.AlignLeft)
        self.controlLayout.addWidget(self.map, 2, 1, 1, 1, Qt.AlignLeft)
        self.controlLayout.addLayout(self.time.periodLayout, 4, 0, 1, 2,
                                     (Qt.AlignRight | Qt.AlignBottom))
        self.controlLayout.addLayout(self.time.timeRangeLayout, 5, 0, 1, 2, Qt.AlignBottom)

        # Add spacers
        self.controlLayout.addItem(QSpacerItem(0, 0), 0, 2, 5, 1)
        self.controlLayout.setColumnStretch(3, 1)
        # self.controlLayout.addItem(QSpacerItem(0, 0), 3, 0, 1, 2)
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
        print(__name__, inspect.currentframe().f_code.co_name)

        ''' Load raw data file, get statistics, update map and table '''

        #TODO Remember file location
        inputFileName, _filter = QFileDialog.getOpenFileName(self,
                              caption='Open .csv file',
                              directory=r'C:\OpenField',
                              filter='CSV files (*.csv)')
        # The extarnal program that generates the raw data saves
        # .csv files to C:\OpenField by default, thus predefined location

        # Read pandas dataframe from file and preprocess it
        if inputFileName:
            maxX, maxY = self.stat.read(inputFileName)
            # Check if data correspond to field settings
            if maxX or maxY:
                self.incorrectData(maxX, maxY)
                return
        else:  # File dialog exited with Cancel
            return

        # Update time variables based on loaded data
        self.time.loadTimeVariables(self.stat)

        # Get statistics and fill the table
        self.table.fillTable()

        # Update path on map
        self.map.updateMapPath(self.params['startSelected'], self.params['endSelected'])

        # Set file name label
        metrix = QFontMetrics(self.fileNameLabel.font())
        width = self.fileNameLabel.width() - 2;
        clippedText = metrix.elidedText(inputFileName, Qt.ElideMiddle, width)
        self.fileNameLabel.setText(clippedText)

        self.saveButton.setEnabled(True) #??? Disable save actions in menu bar

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

        QMessageBox.warning(self, 'Incorrect raw data', warningMessage)

        self.stat.has_file = False

    def closeEvent(self, event):
        print(__name__, inspect.currentframe().f_code.co_name)

        self.settings.saveRecentParameters()

    # def resizeEvent(self, e):
    #     # try:
    #         availableHeight = self.height() \
    #             - sum([self.controlLayout.rowMinimumHeight(row)
    #                     for row in [0, 1, 4, 5]])
    #         print(self.controlLayout.rowMinimumHeight(5))
    #         availableWidth = 600 #self.width() - (self.tableWidth()
    #                               # + self.controlLayout.columnMinimumWidth(0))
    #         self.mapSide = (s := min(availableHeight, availableWidth)) \
    #                         - (s % self.numLasers)
    #         self.drawMap()
    #     except AttributeError:
    #         raise



if __name__ == '__main__':
    app = QApplication(os.sys.argv)
    app.setStyle(QStyleFactory.create('Fusion'))
    window = MainWindow()
    window.show()
    app.exec()