import sys
import inspect

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QStyleFactory,
    QVBoxLayout, QHBoxLayout, QGridLayout, QSpacerItem,
    QWidget
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon, QAction

from settings import Settings
from file_menu import File
from data_processing import DataProcessing
from field_map import MapWidget
from time_parameters import TimeParameters
from output_table import TableView
from app_info import Info


class MainWindow(QMainWindow):
    def __init__(self, app):
        print(__class__.__name__, inspect.currentframe().f_code.co_name)

        super().__init__()

        self.app = app  #???

        self.setWindowTitle('Open Field Statistics')
        self.setWindowIcon(QIcon('logo.ico'))

        # screen = app.primaryScreen().size()
        # self.setMaximumSize(screen)
        self.setGeometry(100, 100, 100, 100)

        # self.setVariables()

        self.settings = Settings(self)
        self.file = File(self)
        self.map = MapWidget(self)
        # self.map.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        self.time = TimeParameters(self)
        self.stat = DataProcessing(self)
        self.table = TableView(self, app)

        self.setMenu()
        self.setLayouts()

    # def setVariables(self):
        # self.mapSide = min(self.height(), self.width()/2) * 2/3

    def setMenu(self):
        print(__class__.__name__, inspect.currentframe().f_code.co_name)

        menu = self.menuBar()

        self.file.setFileMenu(menu)

        settingsAction = QAction('Settings', self)
        settingsAction.triggered.connect(self.settings.openSettingsDialog)

        infoAction = QAction('Info', self)
        infoAction.triggered.connect(lambda: Info(self))

        menu.addAction(settingsAction)
        menu.addAction(infoAction)

    def setLayouts(self):
        print(__class__.__name__, inspect.currentframe().f_code.co_name)

        self.controlLayout = QGridLayout()
        self.controlLayout.addWidget(self.file.loadFileButton, 0, 0, 1, 1,
                                     Qt.AlignmentFlag.AlignLeft)
        self.controlLayout.addWidget(self.file.fileNameLabel, 0, 1, 1, 2)

        # Load map widgets to window's layout
        self.controlLayout.addWidget(self.map.addZoneBtn, 1, 1, 1, 1,
                                      Qt.AlignmentFlag.AlignRight)
        self.controlLayout.addLayout(self.map.areaBtnLayout, 2, 0, 1, 1,
                                      Qt.AlignmentFlag.AlignLeft)
        self.controlLayout.addWidget(self.map, 2, 1, 1, 1,
                                      Qt.AlignmentFlag.AlignLeft)
        self.controlLayout.addWidget(self.map.mapModeBox, 3, 1, 1, 1,
                                     Qt.AlignmentFlag.AlignRight)
        # self.controlLayout.addLayout(self.map.mapControlLayout, 1, 0, 1, 2)

        self.controlLayout.addWidget(self.time.timeGroup, 4, 0, 1, 2,
                                     Qt.AlignmentFlag.AlignBottom)

        # Add spacers
        self.controlLayout.addItem(QSpacerItem(0, 0), 0, 2, 5, 1)
        self.controlLayout.setColumnStretch(3, 1)
        # self.controlLayout.addItem(QSpacerItem(0, 0), 3, 0, 1, 2)
        self.controlLayout.setRowStretch(3, 1)

        self.dataLayout = QVBoxLayout()
        self.dataLayout.addWidget(self.table)
        self.dataLayout.addWidget(self.file.saveDataButton,
                                   alignment=(Qt.AlignmentFlag.AlignRight
                                              | Qt.AlignmentFlag.AlignBottom))

        self.generalLayout = QHBoxLayout()
        self.generalLayout.addLayout(self.controlLayout)
        self.generalLayout.addLayout(self.dataLayout)

        container = QWidget()
        container.setLayout(self.generalLayout)
        self.setCentralWidget(container)

    def closeEvent(self, event):
        print(__class__.__name__, inspect.currentframe().f_code.co_name)

        self.settings.saveRecentSettings()

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
    app = QApplication(sys.argv)
    app.setStyle(QStyleFactory.create('Fusion'))
    window = MainWindow(app)
    window.show()
    sys.exit(app.exec())
