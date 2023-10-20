import pandas as pd
import numpy as np
import inspect


class DataProcessing_pandas():
    def __init__(self, params, zoneCoord):
        print(__name__, inspect.currentframe().f_code.co_name)

        self.params = params
        self.zoneCoord = zoneCoord

        self.read()  # !!! temp

    def read(self, file='C:\OpenField\Rat_1.csv'):
        print(__name__, inspect.currentframe().f_code.co_name)

        df = pd.read_csv(file,
                         sep=None,   # Uses 'csv.Sniffer' for decimal separator,
                         # needs python engine
                         engine='python',
                         # engine='c',  # Needs specified decimal separator
                         parse_dates=[0], date_format='%H:%M:%S.%f',
                         names=['time', 'x1', 'x2', 'y1', 'y2', 'z'], header=0,
                         index_col=0
                         )
        self.df = self.process_raw_data(df)


# %%

    def process_raw_data(self, df):
        print(__name__, inspect.currentframe().f_code.co_name)

        # Exclude rows with any of four coordinates missing
#TODO Let user define this behavior in Settings (Start of recording/First beam break)
        df = df.loc[(df.loc[:, 'x1':'y2'] != 0).all(axis=1)]

        # Absolute timestamps to timedeltas since start
        df.index -= df.index[0]

        # Resample to 0.1 s
        df = (df
              .resample('100ms', origin='start')
              .agg({'x1': 'mean', 'x2': 'mean',
                    'y1': 'mean', 'y2': 'mean',
                    'z': 'any'})
              .ffill()
              )

        # Central point of the animal
        df['x'] = df[['x1', 'x2']].mean(axis=1)
        df['y'] = df[['y1', 'y2']].mean(axis=1)

        # Change from original bottom-left coordinates to numpy and qt top-left
        df['y'] = self.params['numLasersY'] - df['y'] + 1

        # Lasers are indexed 1-16 and correspond to centers of cells
        # Change to Euclidean coordinates
        df['x'] -= 0.5
        df['y'] -= 0.5

        # Distance by each axis
        df['dx'] = df['x'].diff()
        df['dy'] = df['y'].diff()

        # Convert to real world distance in cm
        df['dx'] *= self.params['boxSideX'] / self.params['numLasersX']
        df['dy'] *= self.params['boxSideY'] / self.params['numLasersY']

        # Distance travelled since previous timestamp
        df['dist'] = np.hypot(df['dx'], df['dy'])

        # Start of rearing
        df['dz'] = df['z'].diff()
        df['dz'] = df[['z', 'dz']].all(axis=1)

        df = df.rename_axis(columns='stats')

        return df

    def pivot_zone_wise(self, df, index):
        print(__name__, inspect.currentframe().f_code.co_name)
        df = (df
              .rename(columns={'x': 'time', 'dz': 'z_num', 'z': 'z_time'})
              .pivot_table(
                  index=index,
                  columns='zone',
                  values=['time', 'dist', 'z_num', 'z_time'],
                  aggfunc={'time': 'count', 'dist': 'sum',
                           'z_num': 'sum', 'z_time': 'sum'}
              )
              )
        return df

    # %%

    def get_data(self, df):
        print(__name__, inspect.currentframe().f_code.co_name)



        # %% #!!! temp
        start = 246.8  # seconds
        end = 911  # seconds
        period = 300  # seconds

        #%%

#TODO mention this behavior in documentation
        # Make periods' index in the format 'period_start—period_end'
        # Periods are relative to the start of Selected_time interval,
        # not the start of Total_time of recording.
        # End of the last period corresponds to the end of Selected_time
        selected = np.round(end - start, 1)
        periods = zip(np.arange(0, selected, period),
                      np.append(np.arange(period, selected, period),
                                selected))
        periods_index = []
        for left, right in periods:
            periods_index.append(f'{left}—{right}')

        start = pd.to_timedelta(start, unit='s')
        end = pd.to_timedelta(end, unit='s')
        period = pd.to_timedelta(period, unit='s')

        # List of zones. Starts from 1 to exclude non-selected cells with zone=0
        zones = [*range(1, self.zoneCoord.max() + 1)]

        # Define zone of each timestamp
        df['zone'] = self.zoneCoord[df['y'].astype(int), df['x'].astype(int)]

        grouper = pd.Grouper(level='time',
                             freq=period,
                             origin='start')
        # Aggregate data for each period/zone (within Selected_time)
        data = (df
                .loc[start:end]
                .pipe(self.pivot_zone_wise, grouper)
                .set_axis(periods_index, axis='index')
                )
        # Aggregate data outside of selected_time
        data.loc['_not_selected'] = (pd
                                     .concat([df.loc[:start], df.loc[end:]])
                                     .pipe(self.pivot_zone_wise, None)
                                     .unstack().swaplevel()
                                     )

        data = (pd

                # Add 'Selected_time', 'Total_time'
                .concat([data,
                         pd.Series(data[data.index != '_not_selected'].sum(),
                                   name='Selected_time').to_frame().T,
                         pd.Series(data.sum(),
                                   name='Total_time').to_frame().T
                         ])
                .stack(level='stats', future_stack=True)

#TODO mention this behavior in documentation
                # Add 'Whole_field' (including non-selected area)
                .assign(Whole_field=lambda data_: data_.sum(axis=1))
                .unstack().stack(level='zone', future_stack=True)

                # Convert time from 100 ms to 1 s
                .assign(time=lambda data_: data_.time * 0.1)
                .assign(z_time=lambda data_: data_.z_time * 0.1)

                # Calculate velocity
                .assign(vel=lambda data_: data_.dist / data_.time)

                # Round to 1 decimal, fill NA with 0
                .astype(float)
                .round(decimals=1)
                .fillna(0)
                .unstack().stack(level=0, future_stack=True)

                # Reorder and rename index values for final output
                .reindex(columns=['Whole_field'] + zones,
                         index=pd.MultiIndex.from_product([
                             ['Total_time', 'Selected_time'] + periods_index,
                             ['time', 'dist', 'vel', 'z_num', 'z_time']])
                         )
                .rename(index={'time': 'Time (s)',
                               'dist': 'Distance (cm)',
                               'vel': 'Velocity (cm/s)',
                               'z_num': 'Rearings number',
                               'z_time': 'Rearings time (s)'},
                        level=1)
                )

        return data


# %%
def temp_args():
    params = {'numLasersX': 16,
              'numLasersY': 16,
              'boxSideX': 40,      # Physical dimensions of the filed, cm
              'boxSideY': 40,
              'mapSideY': 320,     # px, mapSideX is calculated
              # from box sides ratio
              'numStatParam': 5,   # Time, distance, velocity,
              # rearings number, rearings time
              # For temporal compatibility. To be deleted later #!!!
              'numLasers': 16,
              'boxSide': 40}
    zoneCoord = np.zeros((16, 16))
    zoneCoord[:, :] = 3  # Corners
    wall = 4
    zoneCoord[wall: -wall, :] = 2  # Walls
    zoneCoord[:, wall: -wall] = 2
    zoneCoord[wall: -wall, wall: -wall] = 1  # Center
    # zoneCoord[:2] = 0
    zoneCoord = zoneCoord.astype(int)
    return params, zoneCoord


def save(data, file=r'Trials\Test_pandas_output_2.csv'):
    print(__name__, inspect.currentframe().f_code.co_name)

    with open(file, 'w+', newline='') as output:
        data.to_csv(output, sep=';', decimal='.')


stat = DataProcessing_pandas(*temp_args())
data = stat.get_data(stat.df)
save(data)


# stats = ['dt', 'dist', 'z_num', 'z']
# %%
