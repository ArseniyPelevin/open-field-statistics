from datetime import datetime, timedelta
from math import dist, ceil
from statistics import fmean

import pandas as pd

class OFStatistics():
    def __init__(self, csv_df, param):       
        csv_df.columns.values[0] = "Time" 
        self.data = self.getData(csv_df, param)
        self.totalTime = round(self.data.at[self.data.index[-1], 'time'], 1)
        self.totalDistance = round(self.totalDistance, 1)
        self.totalVelocity = round(self.totalDistance / self.totalTime, 1)
        print(f'Total time: {self.totalTime}\n',
              f'Total distance: {self.totalDistance}\n',
              f'Total Velocity: {self.totalVelocity}\n',
              f'Total rearings: {self.totalRearings}', sep='')
       
    def getData(self, csv_df, params):
        data = []
        self.totalDistance = 0
        self.totalRearings = 0
        j = 0  # data[] indexing
        for i, row in csv_df.iterrows():
            # Time points when animal wasn't in the box or when only one
            # coordinate was detected won't be recorded and further processed
            if row['X1'] == 0 or row['Y1'] == 0:
                continue
            
            # Central point of animal
            x = fmean([row['X1'], row['X2']])
            y = fmean([row['Y1'], row['Y2']])
            
            if j == 0:  # Animal is detected and recorded for the first time
                # Time of the first animal detection
                timeStart = datetime.strptime(row['Time'][:-1], '%H:%M:%S.%f')
                            # Input file has 7 decimals in time instead of 6
                time = 0
                #  For not to mix types 'numpy.bool_' and 'bool'
                z = True if row['Z'] else False
                d = 0
            else:
                # Current time in input .csv file
                time = datetime.strptime(row['Time'][:-1], '%H:%M:%S.%f')
                       # Input file has 7 decimals in time instead of 6
                # Seconds since start of recording (first animal appearance)
                time = timedelta.total_seconds(time - timeStart)
                
                z = row['Z'] and not csv_df.at[i-1, 'Z']  # Rearing began here
                    
                p = [data[j-1]['x'], data[j-1]['y']]  # Previous point
                q = [x, y]  # Current point
                d = dist(p, q) * (params['boxSide'] / params['numLasers'])
                self.totalDistance += d
            data.append({'time': time, 'x': x, 'y': y, 'z': z, 'dist': d})
            j += 1
            if z:
                # Only for console verification
                self.totalRearings += 1
        data_df = pd.DataFrame(data)
        return data_df
    
    # Called from main to fill current table with data from self.data
    def table(self, zoneMap, start, end, period, statParam):
        # Default arguments (cannot use instance attributes in method definition)
        # if not start: start = 0
        # if not end: end = self.totalTime 
        
        numZones = int(zoneMap.max())
        numPeriods = ceil((end - start) / period)
        curPeriod = 1
        tableData = [[{key: 0 for key in statParam}
                      for zone in range(numZones+1)]  #  0 - whole field
                     for per in range(numPeriods+2)]  #  0 - total time
                                                      # -1 - selected time
        # Calculate zone/period statistics
        for i, row in self.data.iterrows():
            x = int(row['x'] - 0.5)
            y = int(row['y'] - 0.5)
            # Lasers are indexed 1-16 and correspond to centers of cells
            zone = int(zoneMap[y][x])
            # zoneMap is a numpy array with [row][column] indexing,
            # while x/y are horizontal/vertical axes
            
            # Some zones on zoneMap has values 0, which means they don't belong
            # to any chosen zone. Those values will be saved to tableData[][0],
            # which is reserved for whole field data. It is not a problem, as
            # it will be overwritten in the next for loop
            
            if row['time'] > (curPeriod * period + start):
                curPeriod += 1
            
            
            # Get statistics of this row
            curTime = row['time']
            time = 0
            d = 0
            rear = 0
            
            # Half the time and dist since previous time point was in this cell
            d = row['dist'] / 2
            if i != 0:
                time += (curTime - self.data.at[i-1, 'time']) / 2
                
            # Half the time and dist after current time point was in this cell   
            if i != len(self.data.index)-1:
                time += (self.data.at[i+1, 'time'] - curTime) / 2
                d += self.data.at[i+1, 'dist'] / 2
            # Assume animal doesn't disappear and reappear during observation
            
            rear = 1 if row['z'] else 0
                
            
            if row['time'] >= start and row['time'] < end:  # In selected time 
                # Add statistics to period/zone in tableData
                if zone != 0:  # Doesn't belong to any chosen zone
                    tableData[curPeriod][zone]['time'] += time
                    tableData[curPeriod][zone]['dist'] += d
                    tableData[curPeriod][zone]['rear'] += rear
                # Add statistics to period/whole field,
                # because zones may not cover it all
                tableData[curPeriod][0]['time'] += time
                tableData[curPeriod][0]['dist'] += d
                tableData[curPeriod][0]['rear'] += rear
            else:  # Not in selected time, these data won't be in period/zone
                # Add statistics to total time/zone
                if zone != 0:  # Doesn't belong to any chosen zone
                    tableData[0][zone]['time'] += time
                    tableData[0][zone]['dist'] += d
                    tableData[0][zone]['rear'] += rear
                # Add statistics to total time/whole field
                tableData[0][0]['time'] += time
                tableData[0][0]['dist'] += d
                tableData[0][0]['rear'] += rear
                    
        # Calculate zones' total statistics
        for per in range(1, numPeriods+1):
            for zone in range(0, numZones+1):  # including [0] - whole field
                for key in statParam:    
                    period_zone = tableData[per][zone][key]
                    
                    # Add period/zone to selected time/zone
                    tableData[-1][zone][key] += period_zone
                    # Add period/zone to total time/zone
                    tableData[0][zone][key] += period_zone
        
        # Calculate all velocities                      
        for per in range(0, numPeriods+2):  # Including [0] and [-1]     
            for zone in range(0, numZones+1):  # Including [0] - whole field
                if tableData[per][zone]['time'] != 0:
                    tableData[per][zone]['vel'] = (tableData[per][zone]['dist'] 
                                                 / tableData[per][zone]['time'])

        return tableData
       
    def timeIndex(self, time):        
        # Find row index of time <= desired time
        for i, row in self.data.iterrows():
            if row['time'] > time:
                ti = i - 1
                break
            elif i == self.data.index[-1]:
                ti = i

        return ti