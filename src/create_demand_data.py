#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""

    Create flow data

Created on Wed Aug 19 14:14:46 2020

@author: aman
"""

#%%

import sys
sys.path.append('../')
import pandas as pd
from infrasim.submodels import *
from infrasim.params import *
import numpy

#%%
# Forecast energy demands

def time_series_forecast(flows,fields,start,end,freq='H',exceptions=None):
    '''
    Time series forecasting model

    Arguments:
    ----------

        *flows* : dataframe
            Data containing baseline flows. Must in INFRASIM format with
            date, hour, day, month, and year.

        *fields* : list
            Columns to forecast from flows data

        *start* : str
            Start date in MM/DD/YYYY format

        *end* : str
            End date in MM/DD/YYYY format

        *freq* : str, default daily ('D')
            Datetime frequency

        *exceptions* : list
            Columns to neglect with respect to growth rate

    Returns:
    --------

        *new_flows* : New flow data with forecast

    '''

    new_flows = pd.DataFrame({'Date' : pd.date_range(start=start, end=end, freq=freq)})
    new_flows['Day'] = new_flows.Date.dt.day
    new_flows['Month'] = new_flows.Date.dt.month
    new_flows['Year'] = new_flows.Date.dt.year

    if 'Hour' in flows.columns.tolist():
        new_flows['Hour'] = new_flows.Date.dt.hour

    # loop over each column
    for f in fields:
        new_flows[f] = float(0)
        # loop over each row
        for i in tqdm(range(0,len(new_flows))):

            try:
                baseline_value = flows.loc[(flows.Hour==new_flows.at[i,'Hour']) & \
                                           (flows.Day==new_flows.at[i,'Day'])   & \
                                           (flows.Month==new_flows.at[i,'Month']),f].values[0]
            except:
                # Add mask value for leap year
                baseline_value = numpy.nan

            # Exceptions
            if f in exceptions:
                new_flows.at[i,f] = baseline_value
            else:
                # get demand growth
                if f.__contains__('Jordan'):
                    growth_rate = variables['jordan_demand_growth_rate']
                elif f.__contains__('Israel'):
                    growth_rate = variables['israel_demand_growth_rate']
                elif f.__contains__('West Bank'):
                    growth_rate = variables['palestine_demand_growth_rate']
                elif f.__contains__('Gaza'):
                    growth_rate = variables['palestine_demand_growth_rate']
                # calculate
                new_flows.at[i,f] = baseline_value * ( (1+growth_rate)**(new_flows.at[i,'Year']-flows.iloc[-1]['Year']) )

    return new_flows

# read historical
flows = pd.read_csv('../data/csv/raw_flows.csv')

# define start and end
start       = '1/1/2018'
end         = '12/1/2030'
# define fields to forecast and exceptions
fields      = ['Israel energy demand',
               'Jordan energy demand',
               'West Bank energy demand',
               'Gaza energy demand',
               'Israel wind',
               'Israel solar',
               'Jordan wind',
               'Jordan solar',
               'West Bank wind',
               'West Bank solar',
               'Gaza wind',
               'Gaza solar']

exceptions  = ['Israel wind',
               'Israel solar',
               'Jordan wind',
               'Jordan solar',
               'West Bank wind',
               'West Bank solar',
               'Gaza wind',
               'Gaza solar']

# run
new_flows   = time_series_forecast(flows,fields,start,end,freq='H',exceptions=exceptions)
# add timestep
new_flows['Timestep'] = new_flows.index + 1
# save
new_flows.to_csv('../data/csv/processed_flows.csv')
