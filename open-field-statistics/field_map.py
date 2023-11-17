import os
import inspect
import numpy as np
import pandas as pd

from PyQt6.QtWidgets import (
    QWidget, QLabel, QPushButton, QComboBox,
    QButtonGroup, QVBoxLayout, QHBoxLayout, QGridLayout, QStackedLayout,
    QRubberBand
)
from PyQt6.QtCore import (
    Qt, pyqtSlot, QPoint, QPointF, QRect, QLineF, QSignalBlocker
    )
from PyQt6.QtGui import (
    QIcon, QPixmap, QImage, QPainter, QPen, QColor, QPolygonF
)
from PyQt6 import sip

import superqt

from color_style import ColorStyle


class MapWidget(QLabel):
    def __init__(self, window):
        print(__class__.__name__, inspect.currentframe().f_code.co_name)

        super().__init__()

        self.window = window
        self.params = self.window.settings.params
        self.zoneCoord = np.zeros((self.params['numLasersY'],
                                   self.params['numLasersX']),
                                  dtype=int)

        self.pathPoints = []  # Will be assigned from __main__ after loading raw data

        self.defineAreaTypes()
        self.createAreaButtons()
        self.loadMap()
        self.setMapLayout()

        # Rubber band for drag-selection
        self.rubberBand = QRubberBand(QRubberBand.Shape.Rectangle, self)

    def setMapLayout(self):
        print(__class__.__name__, inspect.currentframe().f_code.co_name)

        # self.mapControlLayout = QGridLayout()

        self.addZoneBtn = QPushButton('Add zone')
        self.addZoneBtn.setFixedWidth(80)
        self.addZoneBtn.setDisabled(True)
        self.addZoneBtn.clicked.connect(self.addNewZone)

        self.mapMode = 'total'
        self.mapModeBox = QComboBox()
        self.mapModeBox.addItems(['Total movements', 'Ambulatory movements'])
        self.mapModeBox.setCurrentText('Total movements')
        self.mapModeBox.currentTextChanged.connect(self.changeMapMode)

        # Load map widgets to mapControlLayout
        # self.mapControlLayout.addWidget(self.addZoneBtn, 0, 1, 1, 1,
        #                              Qt.AlignmentFlag.AlignRight)
        # self.mapControlLayout.addLayout(self.areaBtnLayout, 1, 0, 1, 1,
        #                              Qt.AlignmentFlag.AlignLeft)
        # self.mapControlLayout.addWidget(self, 1, 1, 1, 1,
        #                              Qt.AlignmentFlag.AlignLeft)
        # self.mapControlLayout.addWidget(self.mapModeBox, 2, 1, 1, 1,
        #                          Qt.AlignmentFlag.AlignRight)

    def changeMapMode(self, text):
        print(__class__.__name__, inspect.currentframe().f_code.co_name)

        if text == 'Total movements':
            self.mapMode = 'total'
        elif text == 'Ambulatory movements':
            self.mapMode = 'ambulatory'

        self.updateMapPath(
            self.window.time.timeParams['startSelected'],
            self.window.time.timeParams['endSelected'])

    def loadMap(self):
        print(__class__.__name__, inspect.currentframe().f_code.co_name)

        ''' Create map and its parameters based on new loaded parameters '''

        self.numLasersX = self.params['numLasersX']
        self.numLasersY = self.params['numLasersY']

        self.mapSideY = 320 #TODO:??? Make it depend on window size
        self.mapSideX = int(self.mapSideY *
                            self.params['boxSideX'] /
                            self.params['boxSideY'])

        # Make MapSide divisible by numLasers
        self.mapSideX -= self.mapSideX % self.numLasersX
        self.mapSideY -= self.mapSideY % self.numLasersY

        # Graphical distance between lasers
        self.cellX = int(self.mapSideX / self.numLasersX)
        self.cellY = int(self.mapSideY / self.numLasersY)

        # Set map widget's size with a 2 px margin for border line rendering
        self.setFixedSize(self.mapSideX + 2, self.mapSideY + 2)

        zones = np.unique(self.zoneCoord)
        zones = zones[zones > 0]
        self.numZones = len(zones)
        # Holds newly selected zone values before adding them
        # to global zoneCoord with the 'Add zone" button
        self.bufferZoneCoord = np.zeros((self.params['numLasersY'],
                                         self.params['numLasersX']),
                                        dtype=int)

        self.drawMap()
        self.window.adjustSize()

        self.createMapButtons()

    def drawMap(self):
        print(__class__.__name__, inspect.currentframe().f_code.co_name)

        ''' Create empty map '''

        self.mapCanvas = QPixmap(self.mapSideX + 2, self.mapSideY + 2)

        # Define separate layers for grid, zone colors and path
        self.gridLayer = QPixmap(self.mapSideX + 2, self.mapSideY + 2)

        self.zoneLayer = QPixmap(self.mapSideX, self.mapSideY)
        self.pathLayer = QPixmap(self.mapSideX, self.mapSideY)

        self.gridLayer.fill()
        self.zoneLayer.fill(Qt.transparent)
        self.pathLayer.fill(Qt.transparent)

        gridPainter = QPainter(self.gridLayer)

        # Draw grid
        for x in range(self.numLasersX + 1):
            step = self.cellX * x
            gridPainter.drawLine(QLineF(step, 0, step, self.mapSideY))
        for y in range(self.numLasersY + 1):
            step = self.cellY * y
            gridPainter.drawLine(QLineF(0, step, self.mapSideX, step))

        gridPainter.end()

        self.updateMapZones()

        self.setStyleSheet(ColorStyle.mapStyleSheet(self.numZones))

    def updateMap(self):
        print(__class__.__name__, inspect.currentframe().f_code.co_name)

        ''' Add Zone and Path layers to the map widget '''

        mapPainter = QPainter(self.mapCanvas)

        mapPainter.drawPixmap(0, 0, self.gridLayer)
        mapPainter.drawPixmap(0, 0, self.zoneLayer)
        mapPainter.drawPixmap(0, 0, self.pathLayer)
        mapPainter.end()

        self.setPixmap(self.mapCanvas)

    def updateMapZones(self):
        print(__class__.__name__, inspect.currentframe().f_code.co_name)

        ''' Update map area coloring based on zone selection '''

        # Display global zoneCoord...
        zoneCoord = self.zoneCoord.copy()
        # ...updated with newly selected areas that are not yet saved
        hasValues = np.where(self.bufferZoneCoord)
        zoneCoord[hasValues] = self.bufferZoneCoord[hasValues]

        self.zoneLayer.fill(Qt.transparent)

        zonePainter = QPainter(self.zoneLayer)

        # Fill cells with color
        for i in range(self.numLasersY):
            for j in range(self.numLasersX):
                zone = zoneCoord[i][j]
                zoneColor = QColor(*ColorStyle.zoneColors[zone], int(0.3*255))
                zonePainter.setBrush(zoneColor)
                x = self.cellX * j
                y = self.cellY * i
                zonePainter.drawRect(x, y, self.cellX, self.cellY)

        zonePainter.end()

        self.updateMap()

    def updateMapPath(self, start, end):
        print(__class__.__name__, inspect.currentframe().f_code.co_name)

        ''' Draw path in Selected time '''

        start = pd.to_timedelta(start, unit='s')
        end = pd.to_timedelta(end, unit='s')

        self.pathLayer.fill(Qt.transparent)

        pathPainter = QPainter(self.pathLayer)

        pathPainter.setPen(QPen(Qt.red, 2))
        pathPainter.drawPolyline(self.makePath(self.window.stat.df[start:end]))

        pathPainter.end()

        self.updateMap()

    def makePath(self, df):
        print(__class__.__name__, inspect.currentframe().f_code.co_name)

        ''' Make array of path QPoints for visualization '''

        if self.mapMode == 'total':
            ax = {'x': 'x', 'y': 'y'}
        elif self.mapMode == 'ambulatory':
            ax = {'x': 'x_amb', 'y': 'y_amb'}


        size = df.shape[0]
        polyline = QPolygonF([QPointF(0, 0)] * size)
        buffer = polyline.data()
        buffer.setsize(2 * 8 * size)
        memory = np.frombuffer(buffer, np.float64)
        memory[:] = (pd
                     .concat([df[ax['x']] * self.cellX,
                              df[ax['y']] * self.cellY],
                             axis=1
                             )
                     .to_numpy().flatten()
                     )

        return polyline

    def newAreaButton(self, newBtnId, checked):
        print(__class__.__name__, inspect.currentframe().f_code.co_name)

        ''' A new area button was checked '''

        # Prevent this method from execution after unchecking an area type button
        if not checked:
            return

        self.currentAreaType = self.areaBtnIdx[newBtnId]

        # User can define custom zone
        if self.currentAreaType in self.customAreas:
            # Show hidden map buttons after predefined area mode
            self.mapLayout.currentWidget().show()
            # Activate map buttons according to the current custom area type
            self.mapLayout.setCurrentIndex(newBtnId)

        # Zones are predefined
        else:
            # Hide custom area map buttons when in predefined area mode
            self.mapLayout.currentWidget().hide()
            # Define the predefined areas according to the chosen one
            self.fillPredefinedZones(self.currentAreaType)

    @pyqtSlot()
    def addNewZone(self, numNewZones=1):
        print(__class__.__name__, inspect.currentframe().f_code.co_name)

        '''
        Add a new zone to map and table from two sources:
            - user-defined area with map buttons:
                numNewZones=1
            - predefined areas:
                numNewZones = 2 or 3
        '''

        # Save newly selected areas to global zoneCoord
        hasValues = np.where(self.bufferZoneCoord)
        self.zoneCoord[hasValues] = self.bufferZoneCoord[hasValues]
        # Clear selected area buffer
        self.bufferZoneCoord[...] = 0

        for i in range(numNewZones):
            self.numZones += 1

        # Uncheck all map buttons, update table
        self.updateZoneNumber()

        # Maximum 10 zones
        if self.numZones >= 10:
            # Disable map buttons
            self.mapLayout.currentWidget().hide()
            return

    def updateZoneNumber(self):
        print(__class__.__name__, inspect.currentframe().f_code.co_name)

        ''' Uncheck all map buttons, disable 'New zone' button, update table '''

        # Do not allow to add empty zone before a new area is selected
        self.addZoneBtn.setDisabled(True)

        # Loop through all map buttons in all map layouts and uncheck them
        for i in range(self.mapLayout.count()):
            layout = self.mapLayout.widget(i).layout()
            for j in range(layout.count()):
                button = layout.itemAt(j).widget()
                # Uncheck them quietly
                with QSignalBlocker(button):
                    button.setChecked(False)

        self.setStyleSheet(ColorStyle.mapStyleSheet(self.numZones))
        self.window.table.fillTable()

    def fillPredefinedZones(self, newBtn):
        print(__class__.__name__, inspect.currentframe().f_code.co_name)

        nX = self.numLasersX
        nY = self.numLasersY

        numNewZones = 2  # For halves or center/periphery

        # Split field vertically into two halves
        if newBtn == 'vertical_halves':
            self.zoneCoord[:, :nX//2] = 1
            self.zoneCoord[:, nX//2:] = 2

        # Split field horizontally into two halves
        elif newBtn == 'horizontal_halves':
            self.zoneCoord[:nY//2, :] = 1
            self.zoneCoord[nY//2:, :] = 2

        # Split field into central and peripheral zones
        elif newBtn == 'wall':
            self.zoneCoord[:, :] = 2  # Walls
            wall = int(np.ceil(min(nX, nY) / 4))
            self.zoneCoord[wall : -wall, wall : -wall] = 1  # Center

        elif newBtn == 'wall_corners':
            self.zoneCoord[:, :] = 3  # Corners
            wall = int(np.ceil(min(nX, nY) / 4))
            self.zoneCoord[wall : -wall, :] = 2  # Walls
            self.zoneCoord[:, wall : -wall] = 2
            self.zoneCoord[wall : -wall, wall : -wall] = 1  # Center
            numNewZones = 3

        self.updateMapZones()
        self.numZones = 0
        self.addNewZone(numNewZones=numNewZones)

    def mapBtnToggled(self, checked, x=-1, y=-1, s=-1):
        print(__class__.__name__, inspect.currentframe().f_code.co_name)

        '''
        Actions when a map button was checked (add area for a new zone).
        Signals are defined in each area type method
        '''

        # Maximum 10 zones
        if self.numZones >= 10:
            return

        buttonType = self.areaBtnIdx[self.areaBtnGroup.checkedId()]

        # Assign area coordinates to the index of the next zone
        zoneValue = self.numZones + 1
        # Allow to add a new zone after some area was selected
        self.addZoneBtn.setEnabled(True)

        # Assign the area checked with a custom button to the new zone
        if buttonType == 'cell':
            self.bufferZoneCoord[x][y] = zoneValue
        elif buttonType == 'column':
            self.bufferZoneCoord[:,y] = zoneValue
        elif buttonType == 'row':
            self.bufferZoneCoord[x,:] = zoneValue
        elif buttonType == 'square':
            self.bufferZoneCoord[[s, -s-1], s:self.numLasersX-s] = zoneValue
            self.bufferZoneCoord[s:self.numLasersY-s, [s, -s-1]] = zoneValue

        self.updateMapZones()

    def defineAreaTypes(self):
        print(__class__.__name__, inspect.currentframe().f_code.co_name)

        '''
        Define custom and predefined areas,
        make stacked layout with map buttons of different types
        '''

        self.customAreas = ['cell', 'column', 'row', 'square']
        self.predefinedAreas = ['vertical_halves', 'horizontal_halves',
                                'wall', 'wall_corners']
        self.customAreaMethods = [self.defineCellMapButtons,
                                  self.defineColumnMapButtons,
                                  self.defineRowMapButtons,
                                  self.defineSquareMapButtons]

        # Make dict to index through QButtonGroup and QStackedLayout
        self.areaBtnIdx = {i: k for i, k
                           in enumerate(self.customAreas + self.predefinedAreas)}

    def createMapButtons(self):
        print(__class__.__name__, inspect.currentframe().f_code.co_name)

        self.mapLayout = QStackedLayout(self)

        for idx, name in self.areaBtnIdx.items():
            # Create custom area map buttons with separate methods,
            # and add them to self.mapLayout - a QStackedLayout
            if name in self.customAreas:
                areaMap = self.customAreaMethods[idx]()
                self.mapLayout.insertWidget(idx, areaMap)

        # Set cell (id = 0) as default area type
        self.areaBtnGroup.button(0).setChecked(True)

    def defineCellMapButtons(self):
        print(__class__.__name__, inspect.currentframe().f_code.co_name)

        ''' One cell map button, corresponds to one laser intersection '''

        cellMap = QWidget(self)
        cellMapLayout = QGridLayout(cellMap)
        cellMapLayout.setSpacing(0)
        cellMapLayout.setContentsMargins(0, 0, 0, 0)
        # cellMapLayout.setSizeConstraint(QLayout.SetMaximumSize)
        cellMapButtons = []

        for i in range(self.numLasersY):
            cellMapButtons.append([])
            for j in range(self.numLasersX):
                cellMapButtons[i].append(MapButton('', self))
                cellMapButtons[i][j].setFixedSize(self.cellX, self.cellY)
                cellMapButtons[i][j].setCheckable(True)
                cellMapLayout.addWidget(cellMapButtons[i][j], i, j)
                cellMapButtons[i][j].toggled.connect(
                    lambda checked, i=i, j=j:
                        self.mapBtnToggled(checked=checked, x=i, y=j))

        return cellMap

    def defineColumnMapButtons(self):
        print(__class__.__name__, inspect.currentframe().f_code.co_name)

        ''' Map buttons are vertical columns '''

        columnMap = QWidget(self)
        columnMapLayout = QHBoxLayout(columnMap)
        columnMapLayout.setSpacing(0)
        columnMapLayout.setContentsMargins(0, 0, 0, 0)
        columnMapButtons = []

        for i in range(self.numLasersX):
            columnMapButtons.append(MapButton('', self))
            columnMapButtons[i].setFixedSize(self.cellX, self.mapSideY)
            columnMapButtons[i].setCheckable(True)
            columnMapLayout.addWidget(columnMapButtons[i])
            columnMapButtons[i].toggled.connect(
                lambda checked, i=i:
                    self.mapBtnToggled(checked=checked, y=i))

        return columnMap

    def defineRowMapButtons(self):
        print(__class__.__name__, inspect.currentframe().f_code.co_name)

        ''' Map buttons are horizontal rows '''

        rowMap = QWidget(self)
        rowMapLayout = QVBoxLayout(rowMap)
        rowMapLayout.setSpacing(0)
        rowMapLayout.setContentsMargins(0, 0, 0, 0)
        rowMapButtons = []

        for i in range(self.numLasersY):
            rowMapButtons.append(MapButton('', self))
            rowMapButtons[i].setFixedSize(self.mapSideX, self.cellY)
            rowMapButtons[i].setCheckable(True)
            rowMapLayout.addWidget(rowMapButtons[i])
            rowMapButtons[i].toggled.connect(
                lambda checked, i=i:
                    self.mapBtnToggled(checked=checked, x=i))

        return rowMap

    def defineSquareMapButtons(self):
        print(__class__.__name__, inspect.currentframe().f_code.co_name)

        ''' Map buttons are concentric squares '''

        squareMap = QWidget(self)
        squareMapLayout = QGridLayout(squareMap)
        squareMapLayout.setSpacing(0)
        squareMapLayout.setContentsMargins(0, 0, 0, 0)
        squareMapButtons = []

        nX = self.numLasersX
        nY = self.numLasersY

        numSquares = int(np.ceil(min(nX, nY) / 2))

        for s in range(numSquares):
            squareMapButtons.append(MapButton('', self))
            squareMapButtons[s].setFixedSize(self.mapSideX, self.mapSideY)
            squareMapButtons[s].setCheckable(True)

            # Make bitmap for the button's mask
            bitmap = np.zeros((nY, nX), dtype=np.uint8)
            bitmap[[s, -s-1], s:nX-s] = 1
            bitmap[s:nY-s, [s, -s-1]] = 1
            # Make 32-aligned to convert to QImage
            bitmap = np.pad(bitmap, ((0, 0), (0, (4 - bitmap.shape[1] % 4) % 4)),
                            mode='constant', constant_values=0)
            # Convert to QPixmap through QImage
            image = QImage(bitmap, nX, nY, QImage.Format.Format_Alpha8)
            pixmap = QPixmap(image)

            # Apply mask
            squareMapButtons[s].setMask(pixmap.scaled(
                squareMapButtons[s].size(), Qt.IgnoreAspectRatio).mask())

            squareMapLayout.addWidget(squareMapButtons[s], 0, 0)
            squareMapButtons[s].toggled.connect(
                lambda checked, i=s:
                    self.mapBtnToggled(checked=checked, s=i))

        return squareMap

    def defineClearMapButton(self, size):
        print(__class__.__name__, inspect.currentframe().f_code.co_name)

        self.clearMapButton = QPushButton()
        self.clearMapButton.setFixedSize(size, size)

        pixmapFile = os.path.join('button_pixmaps', 'clear.png')
        clearBtnPixmap = QPixmap(pixmapFile).scaled(self.clearMapButton.size())
        self.clearMapButton.setIcon(QIcon(clearBtnPixmap))
        self.clearMapButton.setIconSize(self.clearMapButton.size())
        self.clearMapButton.setToolTip('Clear all zones')

        self.clearMapButton.clicked.connect(self.clearMap)

    def clearMap(self):
        print(__class__.__name__, inspect.currentframe().f_code.co_name)

        self.numZones = 0

        # Deselect all map areas from global zoneCoord...
        self.zoneCoord[:, :] = 0
        # ...and from buffer for newly selected areas
        self.bufferZoneCoord = np.zeros((self.params['numLasersY'],
                                         self.params['numLasersX']),
                                        dtype=int)
        self.updateMapZones()

        # Uncheck all map buttons, update table
        self.updateZoneNumber()

        # Set cell (id = 0) as the default area type
        self.areaBtnGroup.button(0).setChecked(True)

    def deleteMapButtons(self):
        print(__class__.__name__, inspect.currentframe().f_code.co_name)

        ''' Delete all map button objects by deleting their parent widgets '''

        # Change size of zoneCoord and fill it with zeros in-place
        self.zoneCoord.resize((self.params['numLasersY'],
                               self.params['numLasersX']),
                              refcheck=False)
        self.zoneCoord[:, :] = np.zeros((self.params['numLasersY'],
                                         self.params['numLasersX']),
                                        dtype=int)

        # Delete map buttons
        while self.mapLayout.count():
            item = self.mapLayout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
            else:
                self.deleteLayout(item.layout())
        sip.delete(self.mapLayout)

    def createAreaButtons(self):
        print(__class__.__name__, inspect.currentframe().f_code.co_name)

        ''' Create area type buttons, arranged vertically to the left of the map '''

        # numAreaBtn = len(self.areaBtnIdx)  #TODO:??? Depend on window size
        # size = int(self.mapSideY / (numAreaBtn * 1.5))
        size = 30

        self.areaBtnGroup = QButtonGroup()
        self.areaTypeBtnLayout = QVBoxLayout()
        self.clearBtnLayout = QGridLayout()
        self.areaBtnLayout = QGridLayout()

        for idx, name in self.areaBtnIdx.items():
            # Make current button
            button = QPushButton()
            button.setFixedSize(size, size)
            button.setCheckable(True)

            #TODO Add sys._MEIPASS here to package into one file
            pixmapFile = os.path.join('button_pixmaps', f'{name}.png')
            pixmap = QPixmap(pixmapFile).scaled(button.size())

            button.setIcon(QIcon(pixmap))
            button.setIconSize(button.size())

            # Add button to QButtonGroup
            self.areaBtnGroup.addButton(button, id=idx)

            # Add button to QVBoxLayout
            self.areaTypeBtnLayout.addWidget(self.areaBtnGroup.button(idx))

        # New area type button is selected, change area type
        self.areaBtnGroup.idToggled.connect(self.newAreaButton)

        self.defineClearMapButton(size)

        self.areaTypeBtnLayout.setSpacing(size // 2)
        # Add additional spacing between custom and predefined area buttons
        self.areaTypeBtnLayout.insertSpacing(len(self.customAreas), size // 2)

        self.areaBtnLayout.addLayout(self.areaTypeBtnLayout, 0, 0)
        self.areaBtnLayout.addWidget(self.clearMapButton, 0, 1, alignment=Qt.AlignBottom)

    def mousePressEvent(self, event):
        # Starting position of drag-select rubber band
        self.startPoint = event.position().toPoint()

    def mouseMoveEvent(self, event):
        # No drag-selection in predefined area mode
        if self.currentAreaType in self.predefinedAreas:
            return

        # Current end position of drag-select rubber band
        endPoint = event.position().toPoint()
        rect = QRect(self.startPoint, endPoint).normalized()

        self.rubberBand.setGeometry(rect)
        self.rubberBand.show()

    def mouseReleaseEvent(self, event):
        # No drag-selection in predefined area mode
        if self.currentAreaType in self.predefinedAreas:
            return

        # Important to also get endPoint here for click-selection case!
        endPoint = event.position().toPoint()
        rect = QRect(self.startPoint, endPoint).normalized()

        self.rubberBand.hide()

        # Iterate over all buttons of the current layout
        layout = self.mapLayout.currentWidget().layout()
        for i in range(layout.count()):
            button = layout.itemAt(i).widget()
            buttonRect = button.geometry()

            # Square buttons are not rectangles, their shape is defined by bitmap mask
            if self.currentAreaType == 'square':
                buttonRegion = button.mask()

                # Iterate over all pixels within the selected rect
                for x in range(rect.left(), rect.right() + 1):
                    for y in range(rect.top(), rect.bottom() + 1):

                        pixel = QPoint(x, y)
                        # Pixel is within button region AND selected rect
                        if buttonRegion.contains(pixel) and rect.contains(pixel):
                            button.setChecked(True)

            # Any other (rectangular) button type
            else:
                if rect.intersects(buttonRect):
                    button.setChecked(True)

class MapButton(QPushButton):
    def __init__(self, text, parent):
        super().__init__(text, parent)

    def mousePressEvent(self, event):
          # Ignore the event and pass it to the parent widget
          self.setChecked(True)
          event.ignore()
