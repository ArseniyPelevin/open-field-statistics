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
    def __init__(self, window, settings):
        print(__name__, inspect.currentframe().f_code.co_name)

        self.window = window
        self.settings = settings
        self.params = self.window.params  #FIXME it shouldn't be here

        self.dataFilters = '''CSV (comma delimited) (*.csv);;
                              Text (tab delimited) (*.txt);;
                              Excel Workbook (*.xlsx)'''

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
        items = ['caption', 'action', 'slot', 'file']
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

        # Do not allow to save output data before raw data were loaded
        self.fileItems.loc['saveData', 'action'].setDisabled(True)
        self.fileItems.loc['saveMap', 'action'].setDisabled(True) #TODO


    def loadData(self):
        print(__name__, inspect.currentframe().f_code.co_name)

        ''' Load raw data file, get statistics, update map and table '''

        loadDataFile, filter = QFileDialog.getOpenFileName(
            parent=self.window,
            caption=self.fileItems.loc['loadData', 'caption'],
            directory=self.settings['dirs']['loadData'],
            filter=self.dataFilters,
            initialFilter=self.dataFilters)

        # Read pandas dataframe from file and preprocess it
        if loadDataFile:
            maxX, maxY = self.window.stat.read(loadDataFile)
            # Check if data correspond to field settings
            if maxX or maxY:
                self.incorrectData(maxX, maxY)
                return
        else:  # File dialog exited with Cancel
            return

#??? Call other modules through window here?
        # Update time variables based on loaded data
        self.window.time.loadTimeVariables(self.window.stat)

        # Get statistics and fill the table
        self.window.table.fillTable()

        # Update path on map
        self.window.map.updateMapPath(self.params['startSelected'],
                                      self.params['endSelected'])

        # Set file name label
        metrix = QFontMetrics(self.fileNameLabel.font())
        width = self.fileNameLabel.width() - 2;
        clippedText = metrix.elidedText(loadDataFile, Qt.ElideMiddle, width)
        self.fileNameLabel.setText(clippedText)

        # After raw data were loaded, allow saving output data
        self.fileItems.loc['saveData', 'action'].setEnabled(True)
        # self.fileItems.loc['saveMap', 'action'].setEnabled(True) #TODO
        self.saveDataButton.setEnabled(True)

        # Save raw data file's name to suggest name for output statistics file
        self.fileItems.loc['loadData', 'file'] = loadDataFile

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

        self.window.stat.has_file = False

    def loadParams(self):
        print(__name__, inspect.currentframe().f_code.co_name)

        self.fileItems.loc['loadParams', 'file'], _filter = (
            QFileDialog.getOpenFileName(
                parent=self.window,
                caption=self.fileItems.loc['loadParams', 'caption'],
                directory=self.settings['dirs']['params'],
                filter='JSON (*json)',
                initialFilter='JSON (*json)')
            )



    def saveData(self, data):
        print(__name__, inspect.currentframe().f_code.co_name)

        path = os.path.join(
            self.settings['dirs']['saveData'],
            f"{self.fileItems.loc['loadData', 'file']}_statiistics") # .csv #???
        self.outputDataFile, filter = QFileDialog.getSaveFileName(
            parent=self.window,
            caption=self.fileItems.loc['saveData', 'caption'],
            directory=path,
            filter=self.dataFilters,
            initialFilter=self.dataFilters)


        # with open(self.outputFile, 'w+', newline='') as output:

        # with open(file, 'w+', newline='') as output:
        #     data.to_csv(output, sep=';', decimal='.')

    def saveParams(self, params):
        print(__name__, inspect.currentframe().f_code.co_name)

        if self.fileItems.loc['loadParams', 'file']:
            path = os.path.join(
                self.settings['dirs']['params'],
                f"{self.fileItems.loc['loadParams', 'file']}")
        else:
            path = self.settings['dirs']['params']

        self.fileItems.loc['loadParams', 'file'], _filter = QFileDialog.getSaveFileName(
            parent=self.window,
            caption=self.fileItems.loc['loadParams', 'caption'],
            directory=path,
            filter='JSON (*json)',
            initialFilter='JSON (*json)')

    def saveMap(self, map):
        pass  #TODO
