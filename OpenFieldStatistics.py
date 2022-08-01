from datetime import datetime, timedelta

from math import dist, ceil, floor
import pandas as pd
from statistics import fmean
import sys

class OFStatistics():
    def __init__(self, df, param):       
        df.columns.values[0] = "Time" 
        self.data = self.getData(df, param)
        self.totalTime = self.calcTotalTime(df)
        self.totalDistance = self.calcTotalDistance(df)
        self.totalVelocity = self.calcVelocity(0, self.totalTime, self.totalDistance)
        self.totalRearings = self.calcRearings(df, 0, df.index[-1])
        self.totalTime = round(self.data.at[self.data.index[-1], 'time'], 1)
        self.totalDistance = round(self.totalDistance, 1)
        self.totalVelocity = round(self.totalDistance / self.totalTime, 1)
        print(f'Total time: {self.totalTime}\nTotal distance: {self.totalDistance}\nTotal Velocity: {self.totalVelocity}\nTotal rearings: {self.totalRearings}')
       
    def getData(self, df, param):
        data = []
        self.totalDistance = 0
        self.totalRearings = 0
        j = 0  # data[] indexing
        for i, row in df.iterrows():
            # Time points when animal wasn't in the box or when only one
            # coordinate was detected won't be recorded and further processed
            if row['X1'] == 0 or row['Y1'] == 0:
                continue
            
            # Central point of animal
            x = fmean([row['X1'], row['X2']])
            y = fmean([row['Y1'], row['Y2']])
            
            if i == 0 or j == 0:
                # Time of first animal detection
                timeStart = datetime.strptime(df.at[0, 'Time'][:-1], 
                                              '%H:%M:%S.%f')
                time = 0
                #  For not to mix types 'numpy.bool_' and 'bool'
                z = True if df.at[i, 'Z'] else False
                d = 0
            else:
                # Current time in input .csv file
                time = datetime.strptime(row['Time'][:-1], '%H:%M:%S.%f')
                # Seconds since start of recording (first animal appearance)
                time = timedelta.total_seconds(time - timeStart)
                
                z = row['Z'] and not df.at[i-1, 'Z']  # Rearing began here
                if z:
                    self.totalRearings += 1
                    
                p = [data[j-1]['x'], data[j-1]['y']]  # Previous point
                q = [x, y]  # Current point
                d = dist(p, q) * (param['boxSide'] / param['numLasers'])
                self.totalDistance += d
            data.append({'time': time, 'x': x, 'y': y, 'z': z, 'dist': d})
            j += 1
        data_df = pd.DataFrame(data)
        return data_df
    
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
            curTime = self.data.at[i, 'time']
            time = 0
            d = 0
            rear = 0
            
            # Half the time and dist since previous time point was in this cell
            d = self.data.at[i, 'dist'] / 2
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
       
    def timePoint(self, df, time):
        tp = self.timeStart + timedelta(seconds=time)
        
        # find closest existing time point
        for i, row in df.iterrows():
            curTime = datetime.strptime(df.at[i, 'Time'][:-1], '%H:%M:%S.%f')
            if curTime > tp:
                tp = i - 1
                break
            elif i == df.index[-1]:
                tp = i
                # Find row index prior to desired time
                
        # print(f'Timepoint of {time} = {tp}')
        return tp

    def calcTotalTime(self, df):
        self.timeStart = df.at[0, 'Time'][:-1]      
        # [:-1] because original time has 7 decimals instead of 6
        self.timeStart = datetime.strptime(self.timeStart, '%H:%M:%S.%f')
        timeEnd = df.at[df.index[-1], 'Time'][:-1]
        timeEnd = datetime.strptime(timeEnd, '%H:%M:%S.%f')
        totalTime = round(timedelta.total_seconds(timeEnd-self.timeStart), 1)
        # print(f"Total time: {totalTime} s")
        return totalTime
        
    # distance in cell units yet
    def calcTotalDistance(self, df):
        df['X'] = 0
        df['Y'] = 0
        df['dist'] = 0
        totalDistance = 0
        for i, row in df.iterrows():
            
            # calculate central point of animal
            df.at[i, 'X'] = fmean([row['X1'], row['X2']])
            df.at[i, 'Y'] = fmean([row['Y1'], row['Y2']])
            
            if i == 0: continue
            p = [df.at[i-1, 'X'], df.at[i-1, 'Y']]  # previous point
            q = [df.at[i, 'X'], df.at[i, 'Y']]  # current point
            distance = dist(p, q) * (40 / 16)
            # 40 cm - edge of OpenField box, 16 - number of cells
            df.at[i, 'dist'] = distance  # dist since last point
            totalDistance += distance
        totalDistance = round(totalDistance, 1)
                
        # print(f'Total distance: {totalDistance} cm')
        return totalDistance
    
    def calcDistance(self, df, iStart, iEnd):
        # row1 = self.timePoint(df, start)
        # row2 = self.timePoint(df, end)
        row1 = iStart
        row2 = iEnd
        distance = 0
        for i, row in df.iloc[row1:row2+1, :].iterrows():
            distance += row['dist']
        distance = round(distance, 1)
        # print(f"Selected distance: {distance} cm")
        return distance
    
    def calcVelocity(self, start, end, dist):
        velocity = dist / (end - start)
        velocity = round(velocity, 1)
        print(f"Velocity: {velocity} cm/s")
        return velocity
        
    def calcRearings(self, df, iStart, iEnd):
        # row1 = self.timePoint(df, start)
        # row2 = self.timePoint(df, end)
        row1 = iStart
        row2 = iEnd
        wasRearing = False
        rearings = 0
        for i, row in df.iloc[row1:row2+1, :].iterrows():
            if row['Z'] and not wasRearing:
                rearings += 1
                wasRearing = True
            elif not row['Z'] and wasRearing:
                wasRearing = False
        # print(f'Rearings: {rearings}')
        return rearings