import inspect
import os
import csv

from PyQt6.QtWidgets import (QFileDialog,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QStyleFactory
    )
from PyQt6.QtCore import (
    Qt, QSize, QEvent, QPointF
    )

from superqt import QRangeSlider

from ColorStyle import Delegate


class TableWidget(QTableWidget):
    def __init__(self, window, app, rows, columns):
        print(__name__, inspect.currentframe().f_code.co_name)

        super().__init__(rows, columns)
        self.window = window
        self.app = app
        self.time = self.window.time
        self.map = self.window.map

        self.numStatParam = rows
        self.statParam = self.window.statParam
        self.verticalHeaders = ['Time (s)', 'Distance (cm)', 'Velocity (cm/s)',
                                'Rearings number', 'Rearings time (s)']
        self.setTable()

    def setTable(self):
        print(__name__, inspect.currentframe().f_code.co_name)

        # Forbid user to touch anything in the table
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.setFocusPolicy(Qt.NoFocus)
        self.setSelectionMode(QAbstractItemView.NoSelection)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Fixed)
        self.verticalHeader().setSectionResizeMode(QHeaderView.Fixed)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        # Let Delegate control table coloring
        self.setItemDelegate(Delegate(self, self.window))

        # Set table headers
        self.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        headersTotal = [f'Total time, {x}' for x in self.verticalHeaders]
        self.setVerticalHeaderLabels(headersTotal)
        self.setHorizontalHeaderLabels(['Whole field'])

        self.setStyleSheet('''
                                QTableView {
                                    gridline-color: black;
                                }

                                QHeaderView::section {
                                    padding: 4px;
                                    border-style: none;
                                    border-bottom: 1px solid black;
                                    border-right: 1px solid black;
                                }

                                QHeaderView::section:horizontal {
                                    border-top: 1px solid black;
                                }

                                QHeaderView::section:vertical {
                                    border-left: 1px solid black;
                                }

                                QHeaderView::background-color:gray {
                                    background-color: 200, 200, 200, 0,5;
                                }

                                QTableWidget QTableCornerButton::section {
                                    border: 1px solid black;
                                }''')

        # self.show()
        self.setFixedWidth(self.tableWidth())
        self.adjustSize()


    def tableWidth(self):
        print(__name__, inspect.currentframe().f_code.co_name)

        self.app.processEvents()
        self.app.processEvents()
        tableWidth = self.verticalHeader().width() + \
                     self.horizontalHeader().length() + \
                     self.frameWidth() * 2
        if self.verticalScrollBar().isVisible():
            tableWidth += self.verticalScrollBar().width()

        return tableWidth

    # def tableHeight(self):
    #     print(__name__, inspect.currentframe().f_code.co_name)
    #     tableHeight = self.verticalHeader().length() + \
    #                   self.horizontalHeader().height() + \
    #                   self.frameWidth() * 2
    #     return tableHeight

    def fillTable(self):
        print(__name__, inspect.currentframe().f_code.co_name)

        ''' Fill table with statistics '''

        # Adjust table width to contents
        self.setFixedWidth(self.tableWidth())
        # Adjust window width to table
        # app.processEvents()
        # self.adjustSize()

        # try: #!!!
        #     self.tableData = self.window.stat.table(self.map.zoneCoord, self.time.startSelected,
        #                                 self.time.endSelected, self.time.period,
        #                                 self.statParam)
        # except AttributeError:  # If .csv has not yet been opened
        #     return
        self.tableData = self.window.stat.table(self.map.zoneCoord, self.time.startSelected,
                                    self.time.endSelected, self.time.period,
                                    self.statParam)

        s = self.time.hasSelectedStat
        n = self.numStatParam

        # Fill Total time statistics
        for zone in range(self.map.numZones+1):
            for k in range(n):
                key = self.statParam[k]
                val = round(self.tableData[0][zone][key], 1)
                item = QTableWidgetItem(str(val))
                self.setItem(k, zone, item)

        # Fill Selected time statistics
        if self.time.hasSelectedStat:
            for zone in range(self.map.numZones+1):
                for k in range(n):
                    key = self.statParam[k]
                    val = round(self.tableData[-1][zone][key], 1)
                    item = QTableWidgetItem(str(val))
                    self.setItem(n+k, zone, item)

        # Fill Periods statistics
        if self.time.numPeriods != 0:
            for per in range(1, self.time.numPeriods+1):
                for zone in range(self.map.numZones+1):
                    for k in range(n):
                        key = self.statParam[k]
                        val = round(self.tableData[per][zone][key], 1)
                        item = QTableWidgetItem(str(val))
                        self.setItem(n*(per+s) + k, zone, item)


    def saveData(self):
        print(__name__, inspect.currentframe().f_code.co_name)

        ''' Save table with statistics to a new .csv file '''

        self.outputFile, _filter = QFileDialog.getSaveFileName(self.window, 'Save statistics',
                          os.path.splitext(self.window.inputFileName)[0]+'_statistics.csv')

        with open(self.outputFile, 'w+', newline='') as output:
            writer = csv.writer(output, delimiter=';')

            # Set CSV delimiter
            writer.writerow(['sep=;'])

            n = self.numStatParam

            # Write horizontal header
            writer.writerow(['', '', 'Whole field']
                            + [f'Zone {x+1}' for x in range(self.map.numZones)])

            # Write Total time statistics
            for k in range(n):
                key = self.statParam[k]
                writer.writerow(['Total time', f'{self.verticalHeaders[k]}']
                                + [round(self.tableData[0][zone][key], 1)
                                 for zone in range(self.map.numZones+1)])

            # Write Selected time statistics
            if self.time.hasSelectedStat:
                for k in range(n):
                        key = self.statParam[k]
                        writer.writerow([
                    f'Selected time {self.time.startSelected}-{self.time.endSelected} s',
                    f'{self.verticalHeaders[k]}']
                    + [round(self.tableData[-1][zone][key], 1)
                       for zone in range(self.map.numZones+1)])

            # Write Periods statistics
            if self.time.numPeriods != 0:
                for per in range(self.time.numPeriods):
                    for k in range(n):
                        key = self.statParam[k]
                        start = self.time.periodTimes[per][0]
                        end = self.time.periodTimes[per][1]
                        writer.writerow([f'{start}-{end} s',
                                         f'{self.verticalHeaders[k]}']
                                        + [round(self.tableData[per+1][zone][key], 1)
                                           for zone in range(self.map.numZones+1)])
