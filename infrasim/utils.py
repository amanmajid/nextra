'''
    utils.py
        infrasim utils to make life easier
    

        Contents:
            - To do...

'''

#---
# Modules
#---


import os
import numpy as np
import pandas as pd
import geopandas as gpd
import warnings
import datetime
import os
import shutil

# relative imports
from .global_variables import *



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

def add_timestep_col(dataframe):
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
        nodes = gpd.read_file(path_to_nodes)
    elif '.csv' in path_to_nodes:
        nodes = pd.read_csv(path_to_nodes)
    else:
        raise ValueError('node file must be in shapefile or csv format')
    if not any(nodes.columns.str.isupper()):
        pass
    else:
        nodes = lowercase_columns(nodes)
    return nodes


def read_edge_data(path_to_edges):
    '''Read edge data
    '''
    if '.shp' in path_to_edges:
        edges = gpd.read_file(path_to_edges)
    elif '.csv' in path_to_edges:
        edges = pd.read_csv(path_to_edges)
    else:
        raise ValueError('edge file must be in shapefile or csv format')
    if not any(edges.columns.str.isupper()):
        pass
    else:
        edges = lowercase_columns(edges)
    return edges


def read_flow_data(path_to_flows,**kwargs):
    '''Read flow data
    '''
    if '.csv' in path_to_flows:
        # read
        flows = pd.read_csv(path_to_flows)
        # check cases
        if not any(flows.columns.str.isupper()):
            pass
        else:
            flows = lowercase_columns(flows)
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
            flows = flows.loc[(flows.timestep >= flows.timestep.min()) & \
                              (flows.timestep <= flows.timestep.min() + timesteps)]
        # tidy
        flows = tidy_flow_data(flows)
        # check for negative values
        if not (flows.value < 0).any().any():
            pass
        else:
            flows.loc[flows.value < 0, 'value'] = np.nan
            flows = flows.dropna(axis=0)
            warnings.warn('Flow data contains negative values... dropped')
        return flows
    else:
        raise ValueError('flow file must be in csv format')



#---
# Paths, directories, names etc.
#---

def create_dir(path):
    ''' Create dir if it doesn't exist '''
    if not os.path.exists(path):
        os.makedirs(path)


def create_model_name(base='nextra'):
    '''Returns model name with timestamp (e.g. infrasim-2020-09-21)
    '''
    return base + '_' +str(datetime.datetime.utcnow().strftime("%Y-%m-%d")).replace(' ','-').replace(':','')


def infrasim_init_directories():
    '''Initialise cache and output directories
    '''
    paths = [
            global_variables['results_directory'],
            ]

    # loop and create
    for p in paths:
        create_dir(p)


def infrasim_clean():
    '''Clean up __cache__ and model outputs
    '''
    for p in os.listdir(global_variables['results_directory']):
        shutil.rmtree( global_variables['results_directory'] + p)


def lowercase_columns(dataframe):
    '''Change the cases of all columns within dataframe
    '''
    dataframe.columns = [x.lower() for x in dataframe.columns]
    return dataframe



#---
# Algebraic Modelling System
#---

def define_sets(self):
    '''Define critical sets
    '''
    self.time_ref       = self.flows[['timestep','year']]
    self.indices        = global_variables['edge_index_variables']
    self.commodities    = self.edges.commodity.unique().tolist()
    self.node_types     = self.nodes.type.unique().tolist()
    self.technologies   = self.nodes.subtype.unique().tolist()
    self.functions      = self.nodes.function.unique().tolist()
    self.timesteps      = self.flows.timestep.unique().tolist()
    self.days           = self.flows.day.unique().tolist()
    self.months         = self.flows.month.unique().tolist()
    self.years          = self.flows.year.unique().tolist()
    return self


def add_super_source():
    '''Add super_source node to network
    '''


def add_super_sink():
    '''Add super_source node to network
    '''


def add_time_index_to_edges():
    '''Add time index to edges (i.e., i,j,k,t)
    '''