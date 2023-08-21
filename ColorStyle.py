import numpy as np
from PyQt6.QtWidgets import QStyledItemDelegate
from PyQt6.QtGui import QColor, QPalette
from PyQt6.QtCore import Qt

class Colors():
    zoneColors = [(255, 255, 255),
                  (255, 0, 0), (0, 255, 0), (0, 0, 255), (100, 0, 100),
                  (255, 255, 255)]  # Blanck, when max number of zones 4 is reached
    color = [', '.join(map(str, color)) for color in zoneColors]

    @classmethod
    def styleSheet(cls, zone):
        styleSheet = (f'''
            QPushButton {{
                border: 0px;
                background-color: transparent;
            }}

            QPushButton:hover {{
                background-color: rgba({cls.color[zone+1]}, 0.1);
            }}

            QPushButton:pressed {{
                background-color: rgba({cls.color[zone+1]}, 0.3);
            }}
            ''')

        return styleSheet


class Delegate(QStyledItemDelegate):
    def __init__ (self, parent, window):
        super ().__init__ (parent)
        self.window = window

    def paint(self, painter, option, index):
        super().paint(painter, option, index)

        # Overlap of colored zone and gray even block
        if index.column() != 0 and \
           (index.row() // self.window.numStatParam) % 2 == 1:
            color = self.overlap(np.array([120, 120, 120, 120]),  # gray
                                 np.array([*Colors.zoneColors[index.column()], 80]))
        # Colored zone
        elif index.column() != 0:
            color = (*Colors.zoneColors[index.column()], 80)

        # Gray even block
        elif (index.row() // self.window.numStatParam) % 2 == 1:
                color = (200, 200, 200, 120)

        try:
            index.model().setData(index, QColor(*color),
                                  Qt.BackgroundColorRole)
            option.palette.setColor(QPalette.Base,
                                    index.data(Qt.BackgroundColorRole))
        except UnboundLocalError:  # A white cell, no color was set
            pass

    def overlap(self, bg, fg):
        bga = bg[3] / 255
        fga = fg[3] / 255
        bg = bg[:3] / 255
        fg = fg[:3] / 255
        a = 1 - (1 - bga) * (1 - fga)
        color = fg * fga / a + bg * bga * (1 - fga) / a
        return map(int, [*(color * 255), a * 255])
