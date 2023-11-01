import sys
from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtCore import Qt
import pandas as pd
import numpy as np
import inspect
import os
import csv

from PyQt6.QtWidgets import (QFileDialog,
    QTableView, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QStyleFactory
    )
from PyQt6.QtCore import (
    Qt, QSize, QEvent, QPointF, QAbstractTableModel
    )

from superqt import QRangeSlider

# from ColorStyle import Delegate #!!!


class TableModel(QtCore.QAbstractTableModel):

    def __init__(self, data):
        print(__name__, inspect.currentframe().f_code.co_name)

        super(TableModel, self).__init__()

        self._data = data

    def data(self, index, role):
        # print(__name__, inspect.currentframe().f_code.co_name)

        if role == Qt.DisplayRole:
            value = self._data.iloc[index.row(), index.column()]
            return str(np.round(value, 1))

    def rowCount(self, index):
        # print(__name__, inspect.currentframe().f_code.co_name)

        return self._data.shape[0]

    def columnCount(self, index):
        # print(__name__, inspect.currentframe().f_code.co_name)

        return self._data.shape[1]

    def headerData(self, section, orientation, role):
        # print(__name__, inspect.currentframe().f_code.co_name)

        # Section is the index of the column/row.
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                return str(self._data.columns[section])

            if orientation == Qt.Vertical:
                return f'{self._data.index[section][0]}, {self._data.index[section][1]}'

    def updateData(self, data):
        print(__name__, inspect.currentframe().f_code.co_name)

        self.layoutAboutToBeChanged.emit()
        self._data = data
        self.layoutChanged.emit()


class TableView(QTableView):
    def __init__(self, window, app):
        print(__name__, inspect.currentframe().f_code.co_name)

        super().__init__()

        self.window = window
        self.app = app
        self.data = self.window.stat.data

        self.model = TableModel(self.data)
        self.setModel(self.model)

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



        # Set table headers
        self.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)

        # # Let Delegate control table coloring
        # self.setItemDelegate(Delegate(self, self.window)) #!!!
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

        self.show()
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
        self.app.processEvents() #???
        self.window.adjustSize()

        try:
            timeParams = (self.window.params['startSelected'],
                          self.window.params['endSelected'],
                          self.window.params['period'])
            data = self.window.stat.get_data(timeParams)
            self.window.table.model.updateData(data)
        except AttributeError:  # If .csv has not yet been opened
            return

    def saveData(self):
        pass
