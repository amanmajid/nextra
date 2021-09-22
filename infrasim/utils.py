'''
    utils.py
        infrasim utils to make life easier
    

        Contents:
            - Unit conversions
            - Data reading/saving

'''

#---
# Modules
#---


import os
import numpy as np
import pandas as pd
import geopandas as gpd
import warnings

#---
# Conversions
#---

def kwh_to_gwh(v):
    '''Kilowatt hours to Gigawatt hours
    '''
    return v*0.000001


def gwh_to_kwh(v):
    '''Gigawatt hours to Kilowatt hours
    '''
    return v/0.000001


def cmd_to_mld(v):
    '''Cubic meters per day to megalitres per day
    '''
    return v/0.001


def mld_to_cmd(v):
    '''Megalitres per day to cubic meters per day
    '''
    return v*0.001


def lps_to_cmps(v):
    '''Litres per second to cubic meters per second
    '''
    return v*0.001


def seconds_to_hours(v):
    '''Convert seconds to hours
    '''
    return v*3600



#---
# Nodal look-ups
#---


#---
# Edge look-ups
#---


#---
# Data type conversions
#   Transform one type (e.g. dataframe) into another (e.g. dictionary)
#---

def edge_indices_to_dict(self,varname):
    '''Convert variable x to a dict with edge indicies (e.g. [i,j,k,t,x])
    '''
    return self.edge_indices[self.indices+[varname]].set_index(keys=self.indices)[varname].to_dict()


def flows_to_dict(flows):
    '''Convert flow data to dict in format [node,time,value]
    '''
    return flows[['node','timestep','value']].set_index(keys=['node','timestep']).to_dict()['value']



#---
# Data cleaning
#---

def add_timestep_col(dataframe)
    '''add a timestep column to dataframe
    '''
    if 'timestep' in dataframe.columns:
        return dataframe
    else:
        dataframe['timestep'] = [i for i in range(1,len(dataframe)+1)]
        return dataframe


def tidy_flow_data(flows):
    '''Convert nodal flow data to tidy format
    '''
    return flows.melt(id_vars=['timestep','date','hour','day','month','year'],
                      var_name='node',
                      value_name='value'
                      )
    


#---
# Data reading/saving
#---

def read_node_data(path_to_nodes):
    '''Read nodal data
    '''
    if '.shp' in path_to_nodes:
        return gpd.read_file(path_to_nodes)
    elif '.csv' in path_to_nodes:
        return pd.read_csv(path_to_nodes)
    else:
        raise ValueError('node file must be in shapefile or csv format')


def read_edge_data(path_to_edges)
    '''Read edge data
    '''
    if '.shp' in path_to_edges:
        return gpd.read_file(path_to_edges)
    elif '.csv' in path_to_edges:
        return pd.read_csv(path_to_edges)
    else:
        raise ValueError('edge file must be in shapefile or csv format')


def read_flow_data(path_to_flows,**kwargs):
    '''Read flow data
    '''
    if '.csv' in path_to_flows:
        # read
        flows = pd.read_csv(path_to_flows)
        # add timestep column
        flows = add_timestep_col(flows)
        # index by year
        if not kwargs.get("year", False):
            pass
        else:
            flows = flows.loc[(flows.Year == years_restriction)]
        # restrict timesteps
        if not kwargs.get("timesteps", False):
            pass
        else:
            flows = flows.loc[(flows.Timestep >= flows.Timestep.min()) & \
                              (flows.Timestep <= flows.Timestep.min() + timesteps)]
        # tidy
        flows = tidy_flow_data(flows)
        # check for negative values
        if not (flows < 0).any().any():
            pass
        else:
            flows.loc[flows.value < 0, 'value'] = np.nan
            flows = flows.dropna(axis=0)
            warnings.warn('Flow data contains negative values... dropped')
        return flows
    else:
        raise ValueError('flow file must be in csv format')