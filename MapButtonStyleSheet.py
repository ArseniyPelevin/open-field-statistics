
zoneColors = [(255, 255, 255),
              (255, 0, 0), (0, 255, 0), (0, 0, 255), (100, 0, 100),
              (255, 255, 255)]  # Blanck, when max number of zones 4 is reached
color = [', '.join(map(str, color)) for color in zoneColors]

def styleSheet(zone):
    styleSheet = (f'''
        QPushButton {{
            border: 0px;
            background-color: transparent;
        }}

        QPushButton:hover {{
            background-color: rgba({color[zone+1]}, 0.1);
        }}

        QPushButton:pressed {{
            background-color: rgba({color[zone+1]}, 0.3);
        }}
        ''')

    return styleSheet
