import numpy as np

from PyQt6.QtWidgets import QStyledItemDelegate
from PyQt6.QtGui import QColor, QPalette
from PyQt6.QtCore import Qt

import superqt

class ColorStyle():
    def overlap(bg, fg):
        bga = 120 / 255  # Empirical alpha values
        fga = 80 / 255
        bg = bg / 255
        fg = fg / 255
        a = 1 - (1 - bga) * (1 - fga)
        color = fg * fga / a + bg * bga * (1 - fga) / a
        color = np.hstack((color,
                           np.full((color.shape[0], 1), a)))
        color = (color * 255).astype(int).tolist()
        return color

    zoneColors = [(255, 255, 255),  # Zone 0 (not selected)
                  (255, 0, 0), (0, 255, 0), (0, 0, 255),  # Zones 1-3
                   (255, 128, 32), (240, 50, 230), (64, 255, 255),  # Zones 4-6
                   (255, 255, 0), (128, 0, 128), (128, 128, 128),  # Zones 7-9
                   (170, 110, 40)]  # Zone 10

    zoneColorsGray = overlap(np.array([120, 120, 120]),  # gray
                             np.array(zoneColors))

    color = [', '.join(map(str, color)) for color in zoneColors]

    tableStyleSheet = ('''
        QTableView {
            gridline-color: black;
        }

        QTableView QTableCornerButton::section {
            border: 1px solid black;
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
        }''')

    @classmethod
    def mapStyleSheet(cls, zone):
        styleSheet = (f'''
            QPushButton {{
                border: 0px;
                background-color: transparent;
            }}

            QPushButton:hover:!checked {{
                background-color: rgba({cls.color[zone+1]}, 0.1);
            }}
            ''')

        return styleSheet
