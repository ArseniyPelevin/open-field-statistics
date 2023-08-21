#!/usr/bin/env python3

import os
import pandas as pd
import inspect

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QFileDialog,
    QLabel, QPushButton,
    QVBoxLayout, QHBoxLayout, QGridLayout, QSpacerItem,
    QStyleFactory
)
from PyQt6.QtCore import (
    Qt, QSize, QEvent, QPointF
    )
from PyQt6.QtGui import (
    QFontMetrics, QIcon
)

from superqt import QRangeSlider

from DataProcessing import DataProcessing
from MapFunctionality import MapWidget
from Time import TimePeriodSettings
from Table import TableWidget


class MainWindow(QMainWindow):
    def __init__(self):
        print(__name__, inspect.currentframe().f_code.co_name)

        super().__init__()
        self.setWindowTitle('Open Field Statistics')
        self.setWindowIcon(QIcon('logo.ico'))

        # screen = app.primaryScreen().size()
        # self.setMaximumSize(screen)
        self.setGeometry(100, 100, 100, 100)

        self.setVariables()
        self.setWidgets()

        self.map = MapWidget(self, self.params)
        # self.map.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        self.time = TimePeriodSettings(self)
        self.table = TableWidget(self, app, self.numStatParam, 1)

        self.setSignals()
        self.setLayouts()

    def setVariables(self):
        print(__name__, inspect.currentframe().f_code.co_name)

        #TODO delete individual parameters to add global settings
        self.params = {'numLasers': 16,     # On one side
                       'mapSide': 320,      # px
                       'boxSide': 40,        # cm
                       'numStatParam': 5}    # Time, distance, velocity,
                                            # rearings number, rearings time
        # self.numLasers = self.params['numLasers']
        # self.mapSide = min(self.height(), self.width()/2) * 2/3
        self.numStatParam = self.params['numStatParam']
        self.statParam = ['time', 'dist', 'vel', 'rear', 'rearTime']

    '''
    def resizeEvent(self, e):
        # try:
            availableHeight = self.height() \
                - sum([self.controlLayout.rowMinimumHeight(row)
                        for row in [0, 1, 4, 5]])
            print(self.controlLayout.rowMinimumHeight(5))
            availableWidth = 600 #self.width() - (self.tableWidth()
                                  # + self.controlLayout.columnMinimumWidth(0))
            self.mapSide = (s := min(availableHeight, availableWidth)) \
                            - (s % self.numLasers)
            self.drawMap()
        except AttributeError:
            raise
    '''


    def setWidgets(self):
        print(__name__, inspect.currentframe().f_code.co_name)

        self.getFileButton = QPushButton('Select file')
        self.getFileButton.setFixedWidth(80)
        self.fileNameLabel = QLabel()

        self.addZoneBtn = QPushButton('Add zone')
        self.addZoneBtn.setFixedWidth(80)
        self.addZoneBtn.setDisabled(True)

        self.saveButton = QPushButton('Save data')
        self.saveButton.setFixedWidth(80)
        self.saveButton.setDisabled(True)

    def setSignals(self):
        print(__name__, inspect.currentframe().f_code.co_name)

        self.getFileButton.clicked.connect(self.getFile)
        self.addZoneBtn.clicked.connect(self.map.addNewZone)
        self.saveButton.clicked.connect(self.table.saveData)

    def setLayouts(self):
        print(__name__, inspect.currentframe().f_code.co_name)

        self.controlLayout = QGridLayout()
        self.controlLayout.addWidget(self.getFileButton, 0, 0, 1, 1, Qt.AlignLeft)
        self.controlLayout.addWidget(self.fileNameLabel, 0, 1, 1, 2)
        self.controlLayout.addWidget(self.addZoneBtn, 1, 0, 1, 2, Qt.AlignRight)
        self.controlLayout.addLayout(self.map.areaBtnLayout, 2, 0, 1, 1, Qt.AlignLeft)
        self.controlLayout.addWidget(self.map, 2, 1, 1, 1, Qt.AlignLeft)
        self.controlLayout.addLayout(self.time.periodLayout, 4, 0, 1, 2,
                                     (Qt.AlignRight | Qt.AlignBottom))
        self.controlLayout.addLayout(self.time.timeRangeLayout, 5, 0, 1, 2, Qt.AlignBottom)

        # Add spacers
        self.controlLayout.addItem(QSpacerItem(0, 0), 0, 2, 5, 1)
        self.controlLayout.setColumnStretch(3, 1)
        self.controlLayout.addItem(QSpacerItem(0, 0), 3, 0, 1, 2)
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
        self.inputFileName, _filter = QFileDialog.getOpenFileName(self,
                              caption='Open .csv file',
                              directory=r'C:\OpenField',
                              filter='CSV files (*.csv)')
        # The extarnal program that generates the raw data saves
        # .csv files to C:\OpenField by default, thus predefined location

        # Create pandas dataframe and process it
        try:
            self.csv_df = pd.read_csv(self.inputFileName, delimiter=';')
        except FileNotFoundError:
            return

        self.stat = DataProcessing(self.csv_df, self.params)
        self.time.stat = self.stat

        self.time.updateTimeVariables(self.stat)

        # Set file name label
        metrix = QFontMetrics(self.fileNameLabel.font())
        width = self.fileNameLabel.width() - 2;
        clippedText = metrix.elidedText(self.inputFileName, Qt.ElideMiddle, width)
        self.fileNameLabel.setText(clippedText)

        # Make path for visualization
        self.map.makePath(self.stat.data)

        # Update window
        self.map.updateMapPath(0, self.stat.data.index[-1])
        self.table.fillTable()
        self.saveButton.setEnabled(True)


if __name__ == '__main__':
    app = QApplication(os.sys.argv)
    app.setStyle(QStyleFactory.create('Fusion'))
    window = MainWindow()
    window.show()
    app.exec()
