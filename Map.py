import inspect
import os
import numpy as np

from PyQt6.QtWidgets import (
    QWidget, QLabel, QPushButton, QButtonGroup,
    QVBoxLayout, QHBoxLayout, QGridLayout, QStackedLayout,
    QTableWidgetItem, QRubberBand
)
from PyQt6.QtCore import (
    Qt, pyqtSlot, QPoint, QPointF, QRect, QLineF
    )
from PyQt6.QtGui import (
    QIcon, QPixmap, QImage, QPainter, QPen, QColor
)

import superqt

#TODO Expand zoneCoolors to allow more zones
from ColorStyle import Colors

class MapWidget(QLabel):
    def __init__(self, window):
        print(__name__, inspect.currentframe().f_code.co_name)

        super().__init__()

        self.window = window
        # self.time = None
        self.table = None

        # self.numLasers = self.window.params['numLasers']
        self.numLasersX = 16
        self.numLasersY = 16

        self.mapSideY = self.window.params['mapSideY']
        self.mapSideX = int(self.mapSideY *
                          self.window.params['boxSideX'] / self.window.params['boxSideY'])

        # Make MapSide divisible by numLasers
        self.mapSideX -= self.mapSideX % self.numLasersX
        self.mapSideY -= self.mapSideY % self.numLasersY

        # Graphical distance between lasers
        self.cellX = int(self.mapSideX / self.numLasersX)
        self.cellY = int(self.mapSideY / self.numLasersY)

        # Set map widget's size with a 2 px margin for border line rendering
        self.setFixedSize(self.mapSideX + 2, self.mapSideY + 2)

        # Rubber band for drag-selection
        self.rubberBand = QRubberBand(QRubberBand.Shape.Rectangle, self)

        self.zoneCoord = np.zeros((self.numLasersY, self.numLasersX), dtype=int)

        self.pathPoints = []  # Will be assigned from __main__ after loading raw data
        self.numZones = 0

        self.drawMap()
        self.defineAreaTypes()

    def drawMap(self):
        print(__name__, inspect.currentframe().f_code.co_name)

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

        self.updateMap()

        self.setStyleSheet(Colors.styleSheet(self.numZones))

    def updateMap(self):
        print(__name__, inspect.currentframe().f_code.co_name)

        ''' Add Zone and Path layers to the map widget '''

        mapPainter = QPainter(self.mapCanvas)

        # mapPainter.drawPixmap(0, 0, self.mapCanvas.width(), self.mapCanvas.height(), self.gridLayer)
        mapPainter.drawPixmap(0, 0, self.gridLayer)
        mapPainter.drawPixmap(0, 0, self.zoneLayer)
        mapPainter.drawPixmap(0, 0, self.pathLayer)
        mapPainter.end()

        self.setPixmap(self.mapCanvas)

    def updateMapZones(self):
        print(__name__, inspect.currentframe().f_code.co_name)

        ''' Update map area coloring based on zone selection '''

        self.zoneLayer.fill(Qt.transparent)

        zonePainter = QPainter(self.zoneLayer)

        # Fill cells with color
        for i in range(self.numLasersY):
            for j in range(self.numLasersX):
                zone = self.zoneCoord[i][j]
                zoneColor = QColor(*Colors.zoneColors[zone], int(0.3*255))
                zonePainter.setBrush(zoneColor)
                x = self.cellX * j
                y = self.cellY * i
                zonePainter.drawRect(x, y, self.cellX, self.cellY)

        zonePainter.end()

        self.updateMap()

    def updateMapPath(self, iStart, iEnd):
        print(__name__, inspect.currentframe().f_code.co_name)

        ''' Draw path in Selected time '''

        self.pathLayer.fill(Qt.transparent)

        pathPainter = QPainter(self.pathLayer)

        pathPainter.setPen(QPen(Qt.red, 2))
        pathPainter.drawPolyline(self.pathPoints[iStart:iEnd])

        pathPainter.end()

        self.updateMap()

    def makePath(self, data):
        print(__name__, inspect.currentframe().f_code.co_name)

        ''' Make array of path QPoints for visualization '''

        self.pathPoints = []
        for _, row in data.iterrows():
            x = row['x'] * self.cellX - self.cellX / 2
            y = row['y'] * self.cellY - self.cellY / 2
            self.pathPoints.append(QPointF(x, y))
        self.pathPoints = np.array(self.pathPoints)

    def newAreaButton(self, newBtnId, checked):
        print(__name__, inspect.currentframe().f_code.co_name)

        ''' A new area button was checked '''

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
        print(__name__, inspect.currentframe().f_code.co_name)

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
            num = self.table.columnCount()
            self.table.setColumnCount(num + 1)
            self.table.setHorizontalHeaderItem(num, header)
            # app.processEvents()
            # self.adjustSize()

        # Do not allow to add empty zone before a new area is selected
        self.addZoneBtn.setDisabled(True)

        self.table.fillTable()

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
        print(__name__, inspect.currentframe().f_code.co_name)

        nX = self.numLasersX
        nY = self.numLasersY

        # Split field vertically into two halves
        if newBtn == 'Vertical_halves':
            self.zoneCoord[:, :nX//2] = 1
            self.zoneCoord[:, nX//2:] = 2

        # Split field horizontally into two halves
        elif newBtn == 'Horizontal_halves':
            self.zoneCoord[:nY//2, :] = 1
            self.zoneCoord[nY//2:, :] = 2

        # Split field into central and peripheral zones
        elif newBtn == 'Wall':
            self.zoneCoord[:, :] = 1  # Periphery
            wall = int(np.ceil(min(nX, nY) / 4))
            self.zoneCoord[wall : -wall, wall : -wall] = 2  # Center

        self.updateMapZones()
        self.numZones = 0
        self.table.setColumnCount(1)
        self.addNewZone(numNewZones=2)

    def mapBtnToggled(self, checked, x=-1, y=-1, s=-1):
        print(__name__, inspect.currentframe().f_code.co_name)

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
            self.addZoneBtn.setEnabled(True)
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
            self.zoneCoord[[s, -s-1], s:self.numLasersX-s] = zoneValue
            self.zoneCoord[s:self.numLasersY-s, [s, -s-1]] = zoneValue

        # If all new areas were unchecked - do not allow adding empty zone
        if not checked and self.numZones + 1 not in self.zoneCoord:
            self.addZoneBtn.setEnabled(False)

        # print(self.zoneCoord)

        self.updateMapZones()

    def cellMapButtons(self):
        print(__name__, inspect.currentframe().f_code.co_name)

        ''' One cell map button, corresponds to one laser intersection '''

        self.cellMap = QWidget(self)
        self.cellMapLayout = QGridLayout(self.cellMap)
        self.cellMapLayout.setSpacing(0)
        self.cellMapLayout.setContentsMargins(0, 0, 0, 0)
        # self.cellMapLayout.setSizeConstraint(QLayout.SetMaximumSize)
        self.cellMapButtons = []

        for i in range(self.numLasersY):
            self.cellMapButtons.append([])
            for j in range(self.numLasersX):
                self.cellMapButtons[i].append(MapButton('', self))
                self.cellMapButtons[i][j].setFixedSize(self.cellX, self.cellY)
                self.cellMapButtons[i][j].setCheckable(True)
                self.cellMapLayout.addWidget(self.cellMapButtons[i][j], i, j)
                self.cellMapButtons[i][j].toggled.connect(
                    lambda checked, i=i, j=j:
                        self.mapBtnToggled(checked=checked, x=i, y=j))

        return self.cellMap

    def columnMapButtons(self):
        print(__name__, inspect.currentframe().f_code.co_name)

        ''' Map buttons are vertical columns '''

        self.columnMap = QWidget(self)
        self.columnMapLayout = QHBoxLayout(self.columnMap)
        self.columnMapLayout.setSpacing(0)
        self.columnMapLayout.setContentsMargins(0, 0, 0, 0)
        self.columnMapButtons = []

        for i in range(self.numLasersX):
            self.columnMapButtons.append(MapButton('', self))
            self.columnMapButtons[i].setFixedSize(self.cellX, self.mapSideY)
            self.columnMapButtons[i].setCheckable(True)
            self.columnMapLayout.addWidget(self.columnMapButtons[i])
            self.columnMapButtons[i].toggled.connect(
                lambda checked, i=i:
                    self.mapBtnToggled(checked=checked, y=i))

        return self.columnMap

    def rowMapButtons(self):
        print(__name__, inspect.currentframe().f_code.co_name)

        ''' Map buttons are horizontal rows '''

        self.rowMap = QWidget(self)
        self.rowMapLayout = QVBoxLayout(self.rowMap)
        self.rowMapLayout.setSpacing(0)
        self.rowMapLayout.setContentsMargins(0, 0, 0, 0)
        self.rowMapButtons = []

        for i in range(self.numLasersY):
            self.rowMapButtons.append(MapButton('', self))
            self.rowMapButtons[i].setFixedSize(self.mapSideX, self.cellY)
            self.rowMapButtons[i].setCheckable(True)
            self.rowMapLayout.addWidget(self.rowMapButtons[i])
            self.rowMapButtons[i].toggled.connect(
                lambda checked, i=i:
                    self.mapBtnToggled(checked=checked, x=i))

        return self.rowMap

    def squareMapButtons(self):
        print(__name__, inspect.currentframe().f_code.co_name)

        ''' Map buttons are concentric squares '''

        self.squareMap = QWidget(self)
        self.squareMapLayout = QGridLayout(self.squareMap)
        self.squareMapLayout.setSpacing(0)
        self.squareMapLayout.setContentsMargins(0, 0, 0, 0)
        self.squareMapButtons = []

        nX = self.numLasersX
        nY = self.numLasersY

        numSquares = int(np.ceil(min(nX, nY) / 2))

        for s in range(numSquares):
            self.squareMapButtons.append(MapButton('', self))
            self.squareMapButtons[s].setFixedSize(self.mapSideX, self.mapSideY)
            self.squareMapButtons[s].setCheckable(True)

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
            self.squareMapButtons[s].setMask(pixmap.scaled(
                self.squareMapButtons[s].size(), Qt.IgnoreAspectRatio).mask())

            self.squareMapLayout.addWidget(self.squareMapButtons[s], 0, 0)
            self.squareMapButtons[s].toggled.connect(
                lambda checked, i=s:
                    self.mapBtnToggled(checked=checked, s=i))

        return self.squareMap

    def makeAreaButtons(self):
        print(__name__, inspect.currentframe().f_code.co_name)

        ''' Create area type buttons, arranged vertically to the left of the map '''

        # numAreaBtn = len(self.areaBtnIdx)
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
            pixmapFile = os.path.join('Area_Buttons_pixmaps', f'{name}.png')
            pixmap = QPixmap(pixmapFile).scaled(button.size())

            button.setIcon(QIcon(pixmap))
            button.setIconSize(button.size())

            # Add button to QButtonGroup
            self.areaBtnGroup.addButton(button, id=idx)

            # Add button to QVBoxLayout
            self.areaTypeBtnLayout.addWidget(self.areaBtnGroup.button(idx))

        # New area type button is selected, change area type
        self.areaBtnGroup.idToggled.connect(self.newAreaButton)

        # Set Cell (id = 0) as default area type
        self.areaBtnGroup.button(0).setChecked(True)

        self.clearMapButton(size)

        self.areaTypeBtnLayout.setSpacing(size // 2)
        # Add additional spacing between custom and predefined area buttons
        self.areaTypeBtnLayout.insertSpacing(len(self.customAreas), size // 2)

        # self.areaTypeBtnLayout.setContentsMargins(0, 0, 0, 0)

        self.areaBtnLayout.addLayout(self.areaTypeBtnLayout, 0, 0)
        self.areaBtnLayout.addWidget(self.clearMapButton, 0, 1, alignment=Qt.AlignBottom)

    def clearMapButton(self, size):
        print(__name__, inspect.currentframe().f_code.co_name)

        self.clearMapButton = QPushButton()
        self.clearMapButton.setFixedSize(size, size)

        pixmapFile = os.path.join('Area_Buttons_pixmaps', 'Clear.png')
        clearBtnPixmap = QPixmap(pixmapFile).scaled(self.clearMapButton.size())
        self.clearMapButton.setIcon(QIcon(clearBtnPixmap))
        self.clearMapButton.setIconSize(self.clearMapButton.size())
        self.clearMapButton.setToolTip('Clear all zones')

        self.clearMapButton.clicked.connect(self.clearMap)

    def clearMap(self):
        print(__name__, inspect.currentframe().f_code.co_name)


        self.numZones = 0
        self.table.setColumnCount(1)
        self.table.setFixedWidth(self.table.tableWidth())

        self.zoneCoord[:, :] = 0
        self.updateMapZones()
        self.setStyleSheet(Colors.styleSheet(self.numZones))
        # self.adjustSize()

        # Loop through all map buttons in all map layouts and uncheck them
        for i in range(self.mapLayout.count()):
            layout = self.mapLayout.widget(i).layout()
            for i in range(layout.count()):
                button = layout.itemAt(i).widget()
                button.blockSignals(True)
                button.setChecked(False)
                button.blockSignals(False)

        # Set Cell (id = 0) - the default area type
        self.areaBtnGroup.button(0).setChecked(True)

    def defineAreaTypes(self):
        print(__name__, inspect.currentframe().f_code.co_name)

        '''
        Define custom and predefined areas,
        make stacked layout with map buttons of different types
        '''

        self.customAreas = ['Cell', 'Column', 'Row', 'Square']
        self.predefinedAreas = ['Vertical_halves', 'Horizontal_halves', 'Wall']
        customAreaMethods = [self.cellMapButtons, self.columnMapButtons,
                                  self.rowMapButtons, self.squareMapButtons]

        self.addZoneBtn = QPushButton('Add zone')
        self.addZoneBtn.setFixedWidth(80)
        self.addZoneBtn.setDisabled(True)
        self.addZoneBtn.clicked.connect(self.addNewZone)

        # Make dict to index through QButtonGroup and QStackedLayout
        self.areaBtnIdx = {i: k for i, k
                           in enumerate(self.customAreas + self.predefinedAreas)}

        self.mapLayout = QStackedLayout(self)

        for idx, name in self.areaBtnIdx.items():
            # Create custom area map buttons with separate methods,
            # and them to self.mapLayout - a QStackedLayout
            if name in self.customAreas:
                areaMap = customAreaMethods[idx]()
                self.mapLayout.insertWidget(idx, areaMap)

        self.makeAreaButtons()

    def mousePressEvent(self, event):
        self.startPoint = event.position().toPoint()

    def mouseMoveEvent(self, event):
        # No drag-selection in predefined area mode
        if self.currentAreaType in self.predefinedAreas:
            return

        endPoint = event.position().toPoint()
        rect = QRect(self.startPoint, endPoint).normalized()

        self.rubberBand.setGeometry(rect)
        self.rubberBand.show()

    def mouseReleaseEvent(self, event):
        # No drag-selection in predefined area mode
        if self.currentAreaType in self.predefinedAreas:
            return

        # Important to get endPoint here for click-selection case!
        endPoint = event.position().toPoint()
        rect = QRect(self.startPoint, endPoint).normalized()

        self.rubberBand.hide()

        # Iterate over all buttons of the current layout
        layout = self.mapLayout.currentWidget().layout()
        for i in range(layout.count()):
            button = layout.itemAt(i).widget()
            buttonRect = button.geometry()

            # Square buttons are not rectangles, their shape is defined by bitmap mask
            if self.currentAreaType == 'Square':
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
