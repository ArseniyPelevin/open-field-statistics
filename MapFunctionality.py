import inspect
import os
import numpy as np

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QFileDialog, QToolTip,
    QLabel, QLineEdit, QPushButton, QButtonGroup, QSpacerItem,
    QVBoxLayout, QHBoxLayout, QGridLayout, QStackedLayout,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QStyleFactory
)
from PyQt6.QtCore import (
    Qt, QSize, pyqtSlot, QPointF
    )
from PyQt6.QtGui import (
    QIcon,
    QPen, QPixmap, QPainter, QColor, QPalette
)

import superqt


#TODO Expand zoneCoolors to allow more zones
from ColorStyle import Colors, Delegate

class MapWidget(QLabel):
    def __init__(self, window, params):
        super().__init__()

        self.window = window
        self.params = params

        self.numLasers = self.params['numLasers']
        self.mapSide = self.params['mapSide']
        self.cell = int(self.mapSide / self.numLasers)

        self.zoneCoord = np.zeros((self.numLasers, self.numLasers), dtype=int)

        self.pathPoints = []  # Will be assigned from __main__ after loading row data
        self.numZones = 0

        self.drawMap()
        self.defineAreaTypes()

    def drawMap(self):
        print(inspect.currentframe().f_code.co_name)

        ''' Create empty map '''

        self.mapCanvas = QPixmap(self.mapSide + 1, self.mapSide + 1)

        # Define separate layers for grid, zone colors and path
        self.gridLayer = QPixmap(self.mapSide + 1, self.mapSide + 1)
        self.zoneLayer = QPixmap(self.mapSide + 1, self.mapSide + 1)
        self.pathLayer = QPixmap(self.mapSide + 1, self.mapSide + 1)

        self.gridLayer.fill()
        self.zoneLayer.fill(Qt.transparent)
        self.pathLayer.fill(Qt.transparent)

        gridPainter = QPainter(self.gridLayer)

        # Draw grid
        for i in range(self.numLasers + 1): #TODO add second loop for rectangle field
            step = self.cell * i
            gridPainter.drawLine(0, step, self.mapSide, step)
            gridPainter.drawLine(step, 0, step, self.mapSide)

        gridPainter.end()

        self.updateMap()

        self.setStyleSheet(Colors.styleSheet(self.numZones))

    def updateMap(self):
        print(inspect.currentframe().f_code.co_name)

        ''' Add Zone and Path layers to the map widget '''

        mapPainter = QPainter(self.mapCanvas)

        mapPainter.drawPixmap(0, 0, self.gridLayer)
        mapPainter.drawPixmap(0, 0, self.zoneLayer)
        mapPainter.drawPixmap(0, 0, self.pathLayer)

        mapPainter.end()

        self.setPixmap(self.mapCanvas)

    def updateMapZones(self):
        print(inspect.currentframe().f_code.co_name)

        ''' Update map area coloring based on zone selection '''

        self.zoneLayer.fill(Qt.transparent)

        zonePainter = QPainter(self.zoneLayer)

        # Fill cells with color
        for i in range(self.numLasers):
            for j in range(self.numLasers):
                zone = self.zoneCoord[i][j]
                zoneColor = QColor(*Colors.zoneColors[zone], int(0.3*255))
                zonePainter.setBrush(zoneColor)
                x = self.cell * j
                y = self.cell * i
                zonePainter.drawRect(x, y, self.cell, self.cell)

        zonePainter.end()

        self.updateMap()

    def updateMapPath(self, iStart, iEnd):
        print(inspect.currentframe().f_code.co_name)

        ''' Draw path in Selected time '''

        self.pathLayer.fill(Qt.transparent)

        pathPainter = QPainter(self.pathLayer)

        pathPainter.setPen(QPen(Qt.red, 2))
        pathPainter.drawPolyline(self.pathPoints[iStart:iEnd])

        pathPainter.end()

        self.updateMap()

    def makePath(self, data):
        print(inspect.currentframe().f_code.co_name)

        ''' Make array of path QPoints for visualization '''

        self.pathPoints = []
        for _, row in data.iterrows():
            x = int(row['x'] * self.cell - self.cell / 2)
            y = int(row['y'] * self.cell - self.cell / 2)
            self.pathPoints.append(QPointF(x, y))
        self.pathPoints = np.array(self.pathPoints)

    def newAreaButton(self, newBtnId, checked):
        print(inspect.currentframe().f_code.co_name)

        ''' A new area button was checked '''

        newBtn = self.areaBtnIdx[newBtnId]

        # User can define custom zone
        if newBtn in self.customAreas:
            # Show hidden map buttons after predefined area mode
            self.mapLayout.currentWidget().show()
            # Activate map buttons according to the current custom area type
            self.mapLayout.setCurrentIndex(newBtnId)

        # Zones are predefined
        else:
            # Hide custom area map buttons when in predefined area mode
            self.mapLayout.currentWidget().hide()
            # Define the predefined areas according to the chosen one
            self.fillPredefinedZones(newBtn)

    @pyqtSlot()
    def addNewZone(self, numNewZones=1):
        print(inspect.currentframe().f_code.co_name)

        '''
        Add a new zone to map and table from two sources:
            - user-defined area with map buttons:
                fillTable=True, numNewZones=1
            - two predefined areas:
                fillTable=False, numNewZones=2
        '''

        for i in range(numNewZones):

            #TODO To make more zones delete it
            if self.numZones == 4:                 # Maximum 4 zones
                return
            self.numZones += 1

            # Add new table column
            header = QTableWidgetItem(f'Zone {self.numZones}')
            num = self.window.table.columnCount()
            self.window.table.setColumnCount(num + 1)
            self.window.table.setHorizontalHeaderItem(num, header)
            # app.processEvents()
            # self.adjustSize()

        # Do not allow to add empty zone before a new area is selected
        self.window.addZoneBtn.setDisabled(True)

        self.window.fillTable()

        # Loop through all map buttons in all map layouts and uncheck them
        for i in range(self.mapLayout.count()):
            layout = self.mapLayout.widget(i).layout()
            for i in range(layout.count()):
                button = layout.itemAt(i).widget()
                button.blockSignals(True)
                button.setChecked(False)
                button.blockSignals(False)

        self.setStyleSheet(Colors.styleSheet(self.numZones))
        # self.adjustSize()

    def fillPredefinedZones(self, newBtn):
        print(inspect.currentframe().f_code.co_name)

        n = self.numLasers

        # Split field vertically into two halves
        if newBtn == 'Vertical_halves':
            self.zoneCoord[:, :n//2] = 1
            self.zoneCoord[:, n//2:] = 2

        # Split field horizontally into two halves
        elif newBtn == 'Horizontal_halves':
            self.zoneCoord[:n//2, :] = 1
            self.zoneCoord[n//2:, :] = 2

        # Split field into central and peripheral zones
        elif newBtn == 'Wall':
            self.zoneCoord[:, :] = 1
            self.zoneCoord[n//4 : 3*n//4, n//4 : 3*n//4] = 2

        self.updateMapZones()
        self.numZones = 0
        self.window.table.setColumnCount(1)
        self.addNewZone(numNewZones=2)

    def mapBtnToggled(self, checked, x=-1, y=-1, s=-1):
        print(inspect.currentframe().f_code.co_name)

        '''
        Actions when a map button was checked (add area for a new zone).
        Signals are defined in each area type method
        '''

        buttonType = self.areaBtnIdx[self.areaBtnGroup.checkedId()]
        #TODO To make more zones delete it
        if self.numZones == 4:
            return

        if checked:
            # Assign area coordinated to the index of the next zone
            zoneValue = self.numZones + 1
            # Allow to add a new zone after some area was selected
            self.window.addZoneBtn.setEnabled(True)
        else:
            # Exclude unchecked area from any zone
            zoneValue = 0

        # Assign the area checked with a custom button to the new zone
        if buttonType == 'Cell':
            self.zoneCoord[x][y] = zoneValue
        elif buttonType == 'Column':
            self.zoneCoord[:,y] = zoneValue
        elif buttonType == 'Row':
            self.zoneCoord[x,:] = zoneValue
        elif buttonType == 'Square':
            self.zoneCoord[[s, -s-1], s:self.numLasers-s] = zoneValue
            self.zoneCoord[s:self.numLasers-s, [s, -s-1]] = zoneValue

        # If all new areas were unchecked - do not allow adding empty zone
        if not checked and self.numZones + 1 not in self.zoneCoord:
            self.window.addZoneBtn.setEnabled(False)

        self.updateMapZones()

    def cellMapButtons(self):
        print(inspect.currentframe().f_code.co_name)

        ''' One cell map button, corresponds to one laser intersection '''

        self.cellMap = QWidget(self)
        self.cellMapLayout = QGridLayout(self.cellMap)
        self.cellMapLayout.setSpacing(0)
        self.cellMapLayout.setContentsMargins(0, 0, 0, 0)
        self.cellMapButtons = []

        for i in range(self.numLasers):
            self.cellMapButtons.append([])
            for j in range(self.numLasers):
                self.cellMapButtons[i].append(QPushButton('', self))
                self.cellMapButtons[i][j].setFixedSize(self.cell, self.cell)
                self.cellMapButtons[i][j].setCheckable(True)
                self.cellMapLayout.addWidget(self.cellMapButtons[i][j], i, j)
                self.cellMapButtons[i][j].toggled.connect(
                    lambda checked, i=i, j=j:
                        self.mapBtnToggled(checked=checked, x=i, y=j))

        return self.cellMap

    def columnMapButtons(self):
        print(inspect.currentframe().f_code.co_name)

        ''' Map buttons are vertical columns '''

        self.columnMap = QWidget(self)
        self.columnMapLayout = QHBoxLayout(self.columnMap)
        self.columnMapLayout.setSpacing(0)
        self.columnMapLayout.setContentsMargins(0, 0, 0, 0)
        self.columnMapButtons = []

        for i in range(self.numLasers):
            self.columnMapButtons.append(QPushButton('', self))
            self.columnMapButtons[i].setFixedSize(self.cell, self.mapSide)
            self.columnMapButtons[i].setCheckable(True)
            self.columnMapLayout.addWidget(self.columnMapButtons[i])
            self.columnMapButtons[i].toggled.connect(
                lambda checked, i=i:
                    self.mapBtnToggled(checked=checked, y=i))

        return self.columnMap

    def rowMapButtons(self):
        print(inspect.currentframe().f_code.co_name)

        ''' Map buttons are horizontal rows '''

        self.rowMap = QWidget(self)
        self.rowMapLayout = QVBoxLayout(self.rowMap)
        self.rowMapLayout.setSpacing(0)
        self.rowMapLayout.setContentsMargins(0, 0, 0, 0)
        self.rowMapButtons = []

        for i in range(self.numLasers):
            self.rowMapButtons.append(QPushButton('', self))
            self.rowMapButtons[i].setFixedSize(self.mapSide, self.cell)
            self.rowMapButtons[i].setCheckable(True)
            self.rowMapLayout.addWidget(self.rowMapButtons[i])
            self.rowMapButtons[i].toggled.connect(
                lambda checked, i=i:
                    self.mapBtnToggled(checked=checked, x=i))

        return self.rowMap

    def squareMapButtons(self):
        print(inspect.currentframe().f_code.co_name)

        ''' Map buttons are concentric squares '''

        self.squareMap = QWidget(self)
        self.squareMapLayout = QGridLayout(self.squareMap)
        self.squareMapLayout.setSpacing(0)
        self.squareMapLayout.setContentsMargins(0, 0, 0, 0)
        self.squareMapButtons = []

        for i in range(8):
            self.squareMapButtons.append(QPushButton('', self))
            self.squareMapButtons[i].setFixedSize(self.mapSide, self.mapSide)
            self.squareMapButtons[i].setCheckable(True)

            #TODO Add sys._MEIPASS here to package into one file
            pixmap = QPixmap(os.path.join('Area_pixmaps', f'{i+1}.png'))
            self.squareMapButtons[i].setMask(pixmap.scaled(self.squareMapButtons[i].size(),
                                                    Qt.IgnoreAspectRatio).mask())
            self.squareMapLayout.addWidget(self.squareMapButtons[i], 0, 0)
            self.squareMapButtons[i].toggled.connect(
                lambda checked, i=i:
                    self.mapBtnToggled(checked=checked, s=i))

        return self.squareMap

    def makeAreaButtons(self):
        print(inspect.currentframe().f_code.co_name)

        ''' Create area type buttons, arranged vertically to the left of the map '''

        numAreaBtn = len(self.areaBtnIdx)
        size = int(self.mapSide / (numAreaBtn * 1.5))

        self.areaBtnGroup = QButtonGroup()
        self.areaBtnLayout = QVBoxLayout()

        for idx, name in self.areaBtnIdx.items():
            # Make current button
            button = QPushButton()
            # Add button to QButtonGroup
            self.areaBtnGroup.addButton(button, id=idx)

            #TODO Add sys._MEIPASS here to package into one file
            pixmap = QPixmap(os.path.join('Area_Buttons_pixmaps', f'{name}.png'))

            # Set button's parameters
            self.areaBtnGroup.button(idx).setIcon(QIcon(pixmap))
            self.areaBtnGroup.button(idx).setIconSize(QSize(size, size))
            self.areaBtnGroup.button(idx).setFixedSize(size, size)
            self.areaBtnGroup.button(idx).setCheckable(True)

            # Set Cell as the default area type
            if name == 'Cell':
                self.areaBtnGroup.button(idx).setChecked(True)

            # Add button to QVBoxLayout
            self.areaBtnLayout.addWidget(self.areaBtnGroup.button(idx))

        self.areaBtnLayout.setSpacing(size // 2)
        # Add additional spacing between custom and predefined area buttons
        self.areaBtnLayout.insertSpacing(len(self.customAreas), size // 2)

        # self.areaBtnLayout.setContentsMargins(0, 0, 30, 0)

    def defineAreaTypes(self):
        print(inspect.currentframe().f_code.co_name)

        '''
        Define custom and predefined areas,
        make stacked layout with map buttons of different types
        '''

        self.customAreas = ['Cell', 'Column', 'Row', 'Square']
        self.predefinedAreas = ['Vertical_halves', 'Horizontal_halves', 'Wall']
        customAreaMethods = [self.cellMapButtons, self.columnMapButtons,
                                  self.rowMapButtons, self.squareMapButtons]

        # Make dict to index through QButtonGroup and QStackedLayout
        self.areaBtnIdx = {i: k for i, k
                           in enumerate(self.customAreas + self.predefinedAreas)}

        self.mapLayout = QStackedLayout()

        for idx, name in self.areaBtnIdx.items():
            # Create custom area map buttons with separate methods,
            # and them to self.mapLayout - a QStackedLayout
            if name in self.customAreas:
                areaMap = customAreaMethods[idx]()
                self.mapLayout.insertWidget(idx, areaMap)

        self.makeAreaButtons()
