from datetime import datetime, timedelta
from math import dist, ceil
from statistics import fmean

import pandas as pd

class DataProcessing():
    def __init__(self, csv_df, params):

        # Account for missing 'Time' header in the raw data table
        csv_df.columns.values[0] = 'Time'

        self.data = self.getData(csv_df, params)
        self.totalTime = round(self.data.at[self.data.index[-1], 'time'], 1)
        self.totalDistance = round(self.totalDistance, 1)
        self.totalVelocity = round(self.totalDistance / self.totalTime, 1)

    def getData(self, csv_df, params):
        data = []
        self.totalDistance = 0
        self.totalRearings = 0
        j = 0  # data[] indexing, differs from csv_df indexing (see the next comment)
        for i, row in csv_df.iterrows():
            # Time points when animal was not in the box or when only one
            # coordinate was detected will not be recorded and further processed
            if row['X1'] == 0 or row['Y1'] == 0:
                continue
            # X1 and X2 are either both 0 or none, so no need to check both.
            # Same for Y1 and Y2

            # Central point of the animal
            x = fmean([row['X1'], row['X2']])
            y = fmean([row['Y1'], row['Y2']])

            # Change from original bottom-left coordinates to numpy and qt top-left
            y = params['numLasersY'] - y + 1

            # Rearing
            z = True if row['Z'] else False   # 'numpy.bool_' to 'bool'

            if j == 0:  # Animal is detected and recorded for the first time
                # timeStart - time of the first animal detection
                try:
                    timeStart = datetime.strptime(row['Time'], '%H:%M:%S.%f')
                except ValueError:
                    # Input file has 7 decimals in time instead of 6
                    timeStart = datetime.strptime(row['Time'][:-1], '%H:%M:%S.%f')
                time = 0
                d = 0
            else:
                # Current time in input .csv file
                try:
                    time = datetime.strptime(row['Time'], '%H:%M:%S.%f')
                except ValueError:
                    # Input file has 7 decimals in time instead of 6
                    time = datetime.strptime(row['Time'][:-1], '%H:%M:%S.%f')

                # Seconds since start of recording (first animal appearance)
                time = timedelta.total_seconds(time - timeStart)
                       # timedelta.total_secinds returns float, hence mcs accuracy

                p = [data[j-1]['x'], data[j-1]['y']]  # Previous point
                q = [x, y]  # Current point
                #!!! Account for uneven field sizes
                # laserSpaceX = params['boxSideX'] / params['numLasersX']
                # laserSpaceY = params['boxSideY'] / params['numLasersY']
                d = dist(p, q) * (params['boxSide'] / params['numLasers'])
                self.totalDistance += d
            data.append({'time': time, 'x': x, 'y': y, 'z': z, 'dist': d})
            j += 1

        data_df = pd.DataFrame(data)

        return data_df

    # Called from main to fill current table with data from self.data
    def table(self, zoneMap, start, end, period, statParam):

        numZones = int(zoneMap.max())
        numPeriods = ceil((end - start) / period)
        curPeriod = 1
        tableData = [[{key: 0 for key in statParam}
                      for zone in range(numZones+1)]  #  0 - whole field
                     for per in range(numPeriods+2)]  #  0 - total time
                                                      # -1 - selected time
        # Calculate zone/period statistics
        for i, row in self.data.iterrows():
            # Lasers are indexed 1-16 and correspond to centers of cells
            x = int(row['x'] - 0.5)
            y = int(row['y'] - 0.5)

            # zoneMap is a numpy array with [row][column] indexing,
            # while x/y are horizontal/vertical axes
            zone = int(zoneMap[y][x])

            # Some zones on zoneMap have values 0, which means they don't belong
            # to any chosen zone. Those values will be saved to tableData[][0],
            # which is reserved for whole field data. It is not a problem, as
            # it will be overwritten in the next for loop

            # Start next period
            if row['time'] > (curPeriod * period + start):
                curPeriod += 1

            # Get statistics of this row
            curTime = row['time']
            time = 0
            d = 0
            rear = 0
            rearTime = 0

            # Rearing began here
            if i != 0:
                rear = int(row['z'] and not self.data.at[i-1, 'z'])
            else:
                rear = int(row['z'])

            # Half the time and dist since previous time point was in this cell
            d = row['dist'] / 2
            if i != 0:
                time += (t := (curTime - self.data.at[i-1, 'time']) / 2)
                if row['z']:
                    rearTime += t

            # Half the time and dist after current time point was in this cell
            if i != len(self.data.index)-1:
                time += (t := (self.data.at[i+1, 'time'] - curTime) / 2)
                if row['z']:
                    rearTime += t
                d += self.data.at[i+1, 'dist'] / 2
            # Assume animal does not disappear and reappear during observation


            if row['time'] >= start and row['time'] < end:  # In selected time
                # Add statistics to period/zone in tableData
                if zone != 0:  # Does not belong to any chosen zone
                    tableData[curPeriod][zone]['time'] += time
                    tableData[curPeriod][zone]['dist'] += d
                    tableData[curPeriod][zone]['rear'] += rear
                    tableData[curPeriod][zone]['rearTime'] += rearTime
                # Add statistics to period/whole field,
                # because zones may not cover it all
                tableData[curPeriod][0]['time'] += time
                tableData[curPeriod][0]['dist'] += d
                tableData[curPeriod][0]['rear'] += rear
                tableData[curPeriod][0]['rearTime'] += rearTime
            else:  # Not in selected time, these data will not be in period/zone
                # Add statistics to total time/zone
                if zone != 0:  # Does not belong to any chosen zone
                    tableData[0][zone]['time'] += time
                    tableData[0][zone]['dist'] += d
                    tableData[0][zone]['rear'] += rear
                    tableData[0][zone]['rearTime'] += rearTime
                # Add statistics to total time/whole field
                tableData[0][0]['time'] += time
                tableData[0][0]['dist'] += d
                tableData[0][0]['rear'] += rear
                tableData[0][0]['rearTime'] += rearTime

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
        # Find row index of time <= target time
        for i, row in self.data.iterrows():
            if row['time'] > time:
                ti = i - 1
                break
            elif i == self.data.index[-1]:
                ti = i

        return ti
