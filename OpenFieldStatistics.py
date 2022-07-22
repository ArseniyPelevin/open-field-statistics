from datetime import datetime, timedelta

from math import dist
from statistics import fmean

class OFStatistics():
    def __init__(self, df):
        df.columns.values[0] = "Time"      
        self.totalTime = self.calcTotalTime(df)
        self.totalDistance = self.calcTotalDistance(df)
        self.totalVelocity = self.calcVelocity(0, self.totalTime, self.totalDistance)
        self.totalRearings = self.calcRearings(df, 0, df.index[-1])
        
        #test
        #self.timePoint(df, 11)
        
#        print(df.to_string())
       # print(df)
       
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
        print(f"Total time: {totalTime} s")
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
            p = [df.at[i-1, 'X'], df.at[i-1, 'Y']]   # previous point
            q = [df.at[i, 'X'], df.at[i, 'Y']]       # current point
            distance = dist(p, q) * (40 / 16)
            # 40 cm - edge of OpenField box, 16 - number of cells
            df.at[i, 'dist'] = distance                  # dist since last point
            totalDistance += distance
        totalDistance = round(totalDistance, 1)
                
        print(f'Total distance: {totalDistance} cm')
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
        print(f"Selected distance: {distance} cm")
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
        print(f'Rearings: {rearings}')
        return rearings