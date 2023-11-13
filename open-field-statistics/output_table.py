import inspect

from PyQt6.QtWidgets import QTableView, QHeaderView, QAbstractItemView
from PyQt6.QtCore import Qt, QAbstractTableModel
from PyQt6.QtGui import QColor

from superqt import QRangeSlider

from color_style import ColorStyle


class TableModel(QAbstractTableModel):

    def __init__(self, data, window):
        print(__class__.__name__, inspect.currentframe().f_code.co_name)

        super(TableModel, self).__init__()

        self._data = data
        self.window = window

    def data(self, index, role):

        numStatParam = len(self.window.settings.params['statParams'])

        if role == Qt.DisplayRole:
            value = self._data.iloc[index.row(), index.column()]
            return str(value)

        if role == Qt.ItemDataRole.BackgroundRole:
            color = (255, 255, 255)  # Default white
            zone = self._data.columns[index.column()]
            # Overlap of colored zone and gray even block
            if index.column() != 0 and (index.row() // numStatParam) % 2 == 1:
                color = ColorStyle.zoneColorsGray[zone]
            # Colored zone
            elif index.column() != 0:
                color = (*ColorStyle.zoneColors[zone], 80)
            # Gray even block
            elif (index.row() // numStatParam) % 2 == 1:
                color = (200, 200, 200, 120)
            return QColor(*color)

    def rowCount(self, index):
        return self._data.shape[0]

    def columnCount(self, index):
        return self._data.shape[1]

    def headerData(self, section, orientation, role):

        # Section is the index of the column/row.
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                zone = self._data.columns[section]
                # In table header display 'Zone n' instead of just 'n'
                if zone != 'Whole_field':
                    zone = f'Zone {zone}'
                return zone

            if orientation == Qt.Vertical:
                # Makeshift for multi header
                return f'{self._data.index[section][0]}, {self._data.index[section][1]}'

    def updateData(self, data):
        print(__class__.__name__, inspect.currentframe().f_code.co_name)

        self.layoutAboutToBeChanged.emit()
        self._data = data
        self.layoutChanged.emit()


class TableView(QTableView):
    def __init__(self, window, app):
        print(__class__.__name__, inspect.currentframe().f_code.co_name)

        super().__init__()

        self.window = window
        self.app = app

        data = self.window.stat.dummy_data
        data = self.renameStatisticsHeaders(data)
        self.model = TableModel(data, window)
        self.setModel(self.model)

        self.setTable()

    def setTable(self):
        print(__class__.__name__, inspect.currentframe().f_code.co_name)

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
        print(__class__.__name__, inspect.currentframe().f_code.co_name)

        self.app.processEvents()
        self.app.processEvents()
        tableWidth = self.verticalHeader().width() + \
                      self.horizontalHeader().length() + \
                      self.frameWidth() * 2
        if self.verticalScrollBar().isVisible():
            tableWidth += self.verticalScrollBar().width()

        return tableWidth

    # def tableHeight(self):
    #     print(__class__.__name__, inspect.currentframe().f_code.co_name)
    #     tableHeight = self.verticalHeader().length() + \
    #                   self.horizontalHeader().height() + \
    #                   self.frameWidth() * 2
    #     return tableHeight

    def renameStatisticsHeaders(self, data):
        print(__class__.__name__, inspect.currentframe().f_code.co_name)

        return (data
                .rename(index={'time': 'Time (s)',
                               'dist': 'Distance (cm)',
                               'velocity': 'Velocity (cm/s)',
                               'rearing_n': 'Rearings number',
                               'rearing_time': 'Rearings time (s)'},
                        )
                )

    def fillTable(self):
        print(__class__.__name__, inspect.currentframe().f_code.co_name, inspect.currentframe().f_back.f_code.co_name)

        ''' Fill table with statistics '''

        data = self.window.stat.get_data()
        data = self.renameStatisticsHeaders(data)
        self.model.updateData(data)

        if self.window.map.numZones < 5:
            # Adjust table width to contents
            self.setFixedWidth(self.tableWidth())

            # Adjust window width to table
            # self.show()
            self.app.processEvents() #???
            self.window.adjustSize()
