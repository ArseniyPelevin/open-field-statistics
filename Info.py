import numpy as np
import math as m
import inspect

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QFileDialog, QToolTip,
    QLabel, QLineEdit, QPushButton, QButtonGroup, QSpacerItem,
    QVBoxLayout, QHBoxLayout, QGridLayout, QStackedLayout,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QStyleFactory,
    QDialog, QDialogButtonBox
)
from PyQt6.QtCore import (
    Qt, QSize, pyqtSlot, QEvent, QPointF, QVariantAnimation, QRegularExpression
    )
from PyQt6.QtGui import (
    QFontMetrics, QIcon,
    QPen, QPixmap, QPainter, QColor, QPalette, QRegularExpressionValidator
)

from superqt import QRangeSlider


class Info(QDialog):
    def __init__(self, window):
        print(__name__, inspect.currentframe().f_code.co_name)

        super().__init__(window)

        self.window = window
        self.setWindowTitle('Info')

        information = '''
Description of this application.
Copyright (c) 2023 Arseniy Pelevin
'''

        self.layout = QVBoxLayout()
        message = QLabel(information)
        self.layout.addWidget(message)
        self.setLayout(self.layout)

        self.exec()
