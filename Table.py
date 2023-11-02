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
from PyQt6.QtGui import QColor

from superqt import QRangeSlider

from ColorStyle import ColorStyle


class TableModel(QtCore.QAbstractTableModel):

    def __init__(self, data, window):
        print(__name__, inspect.currentframe().f_code.co_name)

        super(TableModel, self).__init__()

        self._data = data
        self.window = window

    def data(self, index, role):
        # print(__name__, inspect.currentframe().f_code.co_name)

        numStatParam = len(self.window.params['statParams'])

        if role == Qt.DisplayRole:
            value = self._data.iloc[index.row(), index.column()]
            return str(value)

        if role == Qt.ItemDataRole.BackgroundRole:
            color = (255, 255, 255)  # Default white
            # Overlap of colored zone and gray even block
            if index.column() != 0 and (index.row() // numStatParam) % 2 == 1:
                color = ColorStyle.zoneColorsGray[index.column()]
            # Colored zone
            elif index.column() != 0:
                color = (*ColorStyle.zoneColors[index.column()], 80)
            # Gray even block
            elif (index.row() // numStatParam) % 2 == 1:
                color = (200, 200, 200, 120)
            return QColor(*color)

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
        self.data = self.window.stat.dummy_data

        self.model = TableModel(self.data, window)
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
        # self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        # Set table headers
        self.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)

        self.setStyleSheet(ColorStyle.tableStyleSheet)

        # self.show()
        self.setFixedWidth(self.tableWidth())
        self.adjustSize()


    def tableWidth(self):
        print(__name__, inspect.currentframe().f_code.co_name)

        # self.app.processEvents()
        # self.app.processEvents()
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
        print(__name__, inspect.currentframe().f_code.co_name, inspect.currentframe().f_back.f_code.co_name)

        ''' Fill table with statistics '''

        data = self.window.stat.get_data()
        self.window.table.model.updateData(data)

        if self.window.map.numZones < 5:
            # Adjust table width to contents
            self.setFixedWidth(self.tableWidth())

            # Adjust window width to table
            # self.show()
            self.app.processEvents() #???
            self.window.adjustSize()

    def saveData(self):
        pass
