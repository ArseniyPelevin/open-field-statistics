import pandas as pd
import numpy as np

zoneCoord = np.zeros((16, 16))
zoneCoord[:, :] = 3  # Corners
wall = 4
zoneCoord[wall : -wall, :] = 2  # Walls
zoneCoord[:, wall : -wall] = 2
zoneCoord[wall : -wall, wall : -wall] = 1  # Center
zoneCoord = zoneCoord.astype(int)

params = {'numLasersX': 16,
            'numLasersY': 16,
            'boxSideX': 40,      # Physical dimensions of the filed, cm
            'boxSideY': 40,
            'mapSideY': 320,     # px, mapSideX is calculated
                                 # from box sides ratio
            'numStatParam': 5,   # Time, distance, velocity,
                                 # rearings number, rearings time
            # For temporal compatibility. To be deleted later
            'numLasers': 16,
            'boxSide': 40}

stats = ['dt', 'd', 'dz', 'z_time']

#%%
start = 246.8 # seconds
end = 911 # seconds
selected = end - start
period = 5 * 60 # seconds
periods = zip(np.arange(0, selected, period), np.append(np.arange(period, selected, period), selected))
index = []
for left, right in periods:
    index.append(f'{left}—{right}')

start = pd.to_timedelta(start, unit='s')
end = pd.to_timedelta(end, unit='s')
period = pd.to_timedelta(period, unit='s')

#%%

file = r'C:\OpenField\Rat_1.csv'
df = pd.read_csv(file,
                  sep=None,  # Uses 'csv.Sniffer', needs python engine
                  # engine='c',  # Needs specified separator
                  engine='python',
                  parse_dates=[0], date_format='%H:%M:%S.%f',
                  names=['time', 'x1', 'x2', 'y1', 'y2', 'z'], header=0)


#%%

total_start = df.loc[0, 'time']


df['dt'] = df['time'].diff()

df = df.loc[(df.loc[:, 'x1':'y2'] != 0).all(axis = 1)]
df['x'] = df[['x1', 'x2']].mean(axis = 1)
df['y'] = df[['y1', 'y2']].mean(axis = 1)


df['y'] = params['numLasersY'] - df['y'] + 1

df['x'] -= 0.5
df['y'] -= 0.5

df['dx'] = df['x'].diff()
df['dy'] = df['y'].diff()

df['dx'] *= params['boxSideX'] / params['numLasersX']
df['dy'] *= params['boxSideY'] / params['numLasersY']

df['d'] = np.hypot(df['dx'], df['dy'])

df['dz'] = df['z'].diff()
df['dz'] = df[['z', 'dz']].all(axis = 1)

df['z_time'] = df['dt'].loc[df['z']]

df['zone'] = zoneCoord[df['y'].astype(int), df['x'].astype(int)]
df = df.set_index('time')


#%%

grouper = pd.Grouper(level='time',
                     freq=period,
                     origin='start')

start += total_start
end += total_start

data = df.loc[start:end].pivot_table(
                      index=grouper,
                      columns='zone',
                      values=stats,
                      aggfunc='sum')


data.index = index
zones = data['d'].columns.to_list()


total_time = df.pivot_table(
                      columns='zone',
                       values=stats,
                      aggfunc='sum').stack()


selected_time = data.sum()

data.loc['Total_time'] = total_time
data.loc['Selected_time'] = selected_time

data.columns = data.columns.set_names('stats', level=0)

whole_field = data.T.groupby('stats').sum().T.infer_objects()


whole_field.columns = pd.MultiIndex.from_product([whole_field.columns.to_list(),
                                                  ['Whole_field']])
data = data.join(whole_field)



#%%


data.loc(axis=1)[['dt', 'z_time']] = (data.loc(axis=1)[['dt', 'z_time']]
                                      .apply(lambda x: x.dt.total_seconds()))

vel = data['d'] / data['dt']
vel.columns = pd.MultiIndex.from_product([['vel'],
                                          vel.columns.to_list()])
data = data.join(vel)
stats.insert(2, 'vel')



data = data.astype(float).round(decimals=1)



data = data.stack(0, future_stack=True)

data = data.reindex(columns=['Whole_field'] + zones,
                    index=pd.MultiIndex.from_product([
                        ['Total_time', 'Selected_time'] + index, stats]))
# new_index = pd.MultiIndex.from_product([['Total_time', 'Selected_time'] + index,
#                                         stats])
# data = data.reindex(
#     labels=['Total_time', 'Selected_time'] + index, axis=0, level=0)
# data = data.reindex(labels=stats, axis=0, level=1)
# data = data.reindex(index=new_index)
data = data.rename(index={'dt': 'Time (s)',
                          'd': 'Distance (cm)',
                          'vel': 'Velocity (cm/s)',
                          'dz': 'Rearings number',
                          'z_time': 'Rearings time (s)'},
                   level=1)

data = data.fillna(0)

#%%

print(data.to_string())

outputFile = r'Trials\Test_pandas_output.csv'

with open(outputFile, 'w+', newline='') as output:
    data.to_csv(output, sep=';', decimal='.')
