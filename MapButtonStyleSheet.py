
zoneColors = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (100, 0, 100), 
              (255, 255, 255)]  # Blanck, when max number of zones 4 is reached
color = [', '.join(map(str, color)) for color in zoneColors]

def styleSheet(zone): 
    styleSheet = f'''
        QPushButton {{
            border: 0px;
            background-color: transparent;   
        }}
        
        QPushButton:hover {{
            background-color: rgba({color[zone]}, 0.1);
        }}
        
        QPushButton[zone0="true"] {{
            background-color: rgba({color[0]}, 0.3);
        }}
        
        QPushButton[zone1="true"] {{
            background-color: rgba({color[1]}, 0.3);
        }}
        
        QPushButton[zone2="true"] {{
            background-color: rgba({color[2]}, 0.3);
        }}
        
        QPushButton[zone3="true"] {{
            background-color: rgba({color[3]}, 0.3);
        }}
        
        QPushButton:pressed {{
            background-color: rgba({color[zone]}, 0.3);
        }}
        
        # QPushButton:checked {{
        #     background-color: rgba({color}, 0.3);
        # }}
        '''
    return styleSheet 