import numpy as np
import pandas as pd
import inspect


class DataProcessing():
    def __init__(self, window):
        print(__class__.__name__, inspect.currentframe().f_code.co_name)

        self.window = window
        self.params = window.settings.params
        self.zoneCoord = window.map.zoneCoord
        self.timeParams = window.time.timeParams

        self.has_file = False
        self.zones = np.array([])  # List of existing zone numbers
        self.dummy_data = self.make_dummy_data()

    def make_dummy_data(self):
        print(__class__.__name__, inspect.currentframe().f_code.co_name)

        ''' Make empty data to display table before any file was loaded '''

        return (pd
            .DataFrame(
                data=np.full(shape=(len(self.params['statParams']),
                                    len(self.zones) + 1),  # Whole_field + zones
                             fill_value=''),
                index=pd.MultiIndex.from_product([['Total_time'],
                                                  self.params['statParams']]),
                columns=(['Whole_field'] + self.zones.tolist())
                )
            )

    def checkDataToField(self, df):
        print(__class__.__name__, inspect.currentframe().f_code.co_name)

        ''' Read loaded .csv file with raw data and save as pandas dataframe '''

        # Check that loaded data fit current numLasers parameters
        max_x = df[['x1', 'x2']].max(axis=None)
        max_y = df[['y1', 'y2']].max(axis=None)
        if max_x <= self.params['numLasersX']:
            max_x = 0
        if max_y <= self.params['numLasersY']:
            max_y = 0

        return max_x, max_y

    def process_raw_data(self, df):
        print(__class__.__name__, inspect.currentframe().f_code.co_name)

        ''' Preprocess raw data independent of time and zone parameters '''

        # Exclude rows with any of four coordinates missing
#TODO mention this behavior in documentation
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
        df['x'] = df['x'] - 0.5
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

        self.df = df

    def pivot_zone_wise(self, df, index):
        print(__class__.__name__, inspect.currentframe().f_code.co_name)

        df = (df
              .rename(columns={'x': 'time', 'dz': 'rearing_n', 'z': 'rearing_time'})
              .pivot_table(
                  index=index,
                  columns='zone',
                  values=['time', 'dist', 'rearing_n', 'rearing_time'],
                  aggfunc={'time': 'count', 'dist': 'sum',
                           'rearing_n': 'sum', 'rearing_time': 'sum'}
              )
              )

        # Account for occasional one 0.1 s line leftover
        if ('time' in df.columns
                and df.loc[df.index[-1], 'time'].sum() == 1):
            df = df.drop(index=df.index[-1])

        return df

    def get_data(self):
        print(__class__.__name__, inspect.currentframe().f_code.co_name)

        # List of existing zones (some could have been fully deselected)
        self.zones = np.unique(self.zoneCoord)
        self.zones = self.zones[self.zones > 0]

        # Without loaded file return an empty table
        if not self.window.file.hasDataFile:
            return self.make_dummy_data()

        start = self.timeParams['startSelected']
        end = self.timeParams['endSelected']
        period = self.timeParams['period']

#TODO mention this behavior in documentation
        # Make periods' index in the format 'period_start—period_end'
        # Periods are relative to the start of Selected_time interval,
        # not the start of Total_time of recording.
        # End of the last period corresponds to the end of Selected_time
        total_time = self.df.index[-1].total_seconds()
        selected_time = np.round(end - start, 1)
        periods = zip(np.arange(0, selected_time, period),
                      np.append(np.arange(period, selected_time, period),
                                selected_time))
        periods_index = []
        for left, right in periods:
            periods_index.append(f'{left}—{right}')

        start = pd.to_timedelta(start, unit='s')
        end = pd.to_timedelta(end, unit='s')
        period = pd.to_timedelta(period, unit='s')

        # Define zone of each timestamp
        self.df['zone'] = self.zoneCoord[self.df['y'].astype(int),
                                         self.df['x'].astype(int)]

        grouper = pd.Grouper(level='time',
                             freq=period,
                             origin='start',
                             closed='left'
                             )

        # Aggregate data for each period/zone (within Selected_time)
        data = (self.df
                .loc[start:end]
                .pipe(self.pivot_zone_wise, grouper)
                .set_axis(periods_index, axis='index')
                )

        # Aggregate data outside of selected_time
        data.loc['_not_selected'] = (pd
                                     .concat([self.df.loc[:start-'0.1s'],
                                              self.df.loc[end+'0.1s':]])
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
                .assign(rearing_time=lambda data_: data_.rearing_time * 0.1)

                # Calculate velocity
                .assign(velocity=lambda data_: data_.dist / data_.time)
                .unstack().stack(level=0, future_stack=True)

                # Reorder and rename index values for final output
                .reindex(columns=['Whole_field'] + self.zones.tolist(),
                         index=pd.MultiIndex.from_product([
                             ['Total_time', 'Selected_time'] + periods_index,
                             self.params['statParams']])
                         )

                # Round to 1 decimal, fill NA with 0
                .astype(float)
                .round(decimals=1)
                .fillna(0)
                )

        # Do not show single period which is no less than selected_time
        if abs(selected_time - period.total_seconds()) < 0.5:
            data = data.loc[['Total_time', 'Selected_time']]
        # Do not show selected_time if it is no less than total_time
        if abs(total_time - selected_time) < 0.5:
            data = data.drop(index='Selected_time', level=0)

        self.data = data
        return data
