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
from infrasim.utils import *
from infrasim.global_variables import *
import numpy
from tqdm import tqdm

#%%
# Forecast energy demands

def time_series_forecast(flows,fields,start,end,freq='H',growth_scenario='low',exceptions=None):
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
            datetime frequency

        *exceptions* : list
            Columns to neglect with respect to growth rate

    Returns:
    --------

        *new_flows* : New flow data with forecast

    '''

    new_flows = pd.DataFrame({'date' : pd.date_range(start=start, end=end, freq=freq)})
    new_flows['day'] = new_flows.date.dt.day
    new_flows['month'] = new_flows.date.dt.month
    new_flows['year'] = new_flows.date.dt.year

    if 'hour' in flows.columns.tolist():
        new_flows['hour'] = new_flows.date.dt.hour

    # define growth rates
    growth_rate_dict = { #isr,jor,pal
                        'low'       : [0.028,0.030,0.050],
                        'medium'    : [0.030,0.040,0.055],
                        'high'      : [0.035,0.050,0.060],
                        }

    # loop over each column
    for f in fields:
        new_flows[f] = float(0)
        # loop over each row
        for i in tqdm(range(0,len(new_flows)),desc=f):

            try:
                baseline_value = flows.loc[(flows.hour==new_flows.at[i,'hour']) & \
                                           (flows.day==new_flows.at[i,'day'])   & \
                                           (flows.month==new_flows.at[i,'month']),f].values[0]
            except:
                # Add mask value for leap year
                baseline_value = numpy.nan

            # Exceptions
            if f.__contains__('jordan'):
                growth_rate = growth_rate_dict[growth_scenario][1] #global_variables['jordan_demand_growth_rate'] 
            elif f.__contains__('israel'):
                growth_rate = growth_rate_dict[growth_scenario][0] #global_variables['israel_demand_growth_rate']
            elif f.__contains__('west_bank'):
                growth_rate = growth_rate_dict[growth_scenario][2] #global_variables['palestine_demand_growth_rate']
            elif f.__contains__('gaza'):
                growth_rate = growth_rate_dict[growth_scenario][2] #global_variables['palestine_demand_growth_rate']
            # calculate
            new_flows.at[i,f] = baseline_value * ( (1+growth_rate)**(new_flows.at[i,'year']-flows.iloc[-1]['year']) )

    return new_flows

# read historical
flows = pd.read_csv('../data/_raw/flows/raw_flows.csv')

# define start and end
start       = '1/1/2018'
end         = '12/1/2031'
# define fields to forecast and exceptions
fields      = ['israel_energy_demand',
               'jordan_energy_demand',
               'west_bank_energy_demand',
               'gaza_energy_demand',
               'israel_wind',
               'israel_solar',
               'jordan_wind',
               'jordan_solar',
               'west_bank_wind',
               'west_bank_solar',
               'gaza_wind',
               'gaza_solar']

# read renewables ninja data
basepath = '../data/_raw/renewable_ninja/'

# load
data = []
for f in os.listdir(basepath):
    if '.csv' in f:
        d = pd.read_csv(basepath+f,skiprows=3)
        d['region'] = f.split('.')[0].split('_')[0]
        d['type'] = f.split('.')[0].split('_')[1]
        data.append(d)
data = pd.concat(data,ignore_index=True)

# format datetime
data['time'] = pd.to_datetime(data['time'])
data['hour'] = data['time'].dt.hour 
data['day'] = data['time'].dt.day
data['month'] = data['time'].dt.month

# reindex
data = data[['hour','day','month','region','type','electricity']]

# run
for g in ['low','medium','high']:
    print('Running: ' + g)
    new_flows   = time_series_forecast(flows,fields,start,end,freq='H',growth_scenario=g,exceptions=None)
    # save
    new_flows.to_csv('../data/nextra/nodal_flows/processed_flows_' + g + '.csv',index=False)
    ##########
    # get an index of 2030
    new_flows= new_flows.loc[new_flows.year==2030].reset_index(drop=True)
    ##########
    # merge with res ninja data
    print('merging with renewable ninja data...')
    for c in new_flows.columns:
        print('Processing: ' + c)
        if 'wind' in c or 'solar' in c:
            for i in new_flows[c].index:
                idx = data.loc[(data.hour == new_flows.loc[i,'hour']) & \
                               (data.day == new_flows.loc[i,'day']) & \
                               (data.month == new_flows.loc[i,'month']) ]
                            
                val = idx.loc[ (idx.region.str.contains(c.split('_')[0])) & \
                               (idx.type.str.contains(c.split('_')[-1])), 'electricity'].iloc[0]
                
                
                new_flows.loc[i,c] = val
    print('done')
    # save
    new_flows.to_csv('../data/nextra/nodal_flows/processed_flows_2030_' + g + '.csv',index=False)