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
import snkit
from shapely.geometry import Point

# relative imports
from .global_variables import *


#---
# Plotting colours
#---

technology_color_dict = {'Solar'                : 'gold', 
                         'Coal'                 : 'darkgray', 
                         'Gas'                  : 'moccasin', 
                         'Shale'                : 'chocolate', 
                         'Diesel'               : 'darkred', 
                         'Battery Charge'       : 'lightgreen', 
                         'Battery'              : 'teal', 
                         'Battery Discharge'    : 'teal', 
                         'Wind'                 : 'darkorange'}

#---
# Conversions
#---

def mw_to_gw(v):
    '''MW to GW
    '''
    return v*0.001

def kw_to_gw(v):
    '''Kilowatt to Gigawatt
    '''
    return v*0.000001


def gw_to_kw(v):
    '''Gigawatt to Kilowatt
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


def months_as_str(df,month_column='month',as_letter=False):
    '''Convert months column from int to str
    '''
    if not as_letter:
        months_dict = {1:'Jan',2:'Feb',3:'Mar',4:'Apr',5:'May',6:'Jun',
                       7:'Jul',8:'Aug',9:'Sep',10:'Oct',11:'Nov',12:'Dec'}
    else:
        months_dict = {1:'J',2:'F',3:'M',4:'A',5:'M',6:'J',
                       7:'J',8:'A',9:'S',10:'O',11:'N',12:'D'}

    return df[month_column].map(months_dict)



#---
# Nodal look-ups
#---

def get_junction_nodes(nodes):
    '''Return junction type nodes
    '''
    return nodes.loc[(nodes['type']=='junction')]


def get_storage_nodes(nodes):
    '''Return storage type nodes
    '''
    return nodes.loc[(nodes['type']=='storage')]
    

def get_source_nodes(nodes):
    '''Return source type nodes
    '''
    return nodes.loc[(nodes['type']=='source')]


def get_sink_nodes(nodes):
    '''Return sink type nodes
    '''
    return nodes.loc[(nodes['type']=='sink')]


def get_nodes_by_technology(nodes,technology):
    '''Return nodes by technology (e.g. solar, wind, biogas etc.)
    '''
    return nodes.loc[nodes.subtype==technology]


def get_timesteps_by_year(self,year):
    '''Return all timesteps (t) associated with a given year
    '''
    return self.time_ref[self.time_ref.year==year].timestep.to_list()


def get_timesteps_battery_charging(self,year):
    '''Return all timesteps (t) for battery charging times
    '''
    return self.time_ref[self.time_ref.year==year].timestep.to_list()


def get_flow_at_nodes(flows,list_of_nodes):
    '''Return flows of specific nodes 
    '''
    return flows.loc[flows.node.isin(list_of_nodes)].reset_index(drop=True)  



#---
# Edge look-ups
#---



#---
# Data type conversions
#   Transform one type (e.g. dataframe) into another (e.g. dictionary)
#---

def make_supply_dict(self):
    '''Make dictionary of supply (s) at nodes as {(n,k,t) : s}
    '''
    supply = self.flows.loc[self.flows.node.isin(get_source_nodes(self.nodes).name)]
    return supply[['node','timestep','value']].set_index(['node','timestep'])['value'].to_dict()
    

def make_demand_dict(self):
    '''Make dictionary of demand (d) at nodes as {(n,k,t) : d}
    '''
    demand = self.flows.loc[self.flows.node.isin(get_sink_nodes(self.nodes).name)]
    return demand[['node','timestep','value']].set_index(['node','timestep'])['value'].to_dict()


def make_nodal_capacity_dict(self):
    '''Make dictionary of nodes that can expand in capacity (c) as {(n,k,t): c}
    '''
    source_nodes     = get_source_nodes(self.nodes)
    storage_nodes    = get_storage_nodes(self.nodes)
    expandable_nodes = source_nodes.append(storage_nodes, ignore_index=True)
    return expandable_nodes.set_index(keys=['name','commodity']).to_dict()['capacity']


def make_edge_bound_dict(self,bound_column='maximum'):
    '''Make dictionary of lower/upper bounds (u) as {(i,j,k,t) : u}
    '''
    return self.edge_indices[self.indices+[bound_column]].set_index(keys=self.indices)[bound_column].to_dict()


def make_cost_dict(self,cost_column='cost'):
    '''Make dictionary of costs (c) as {(i,j,k,t) : c}
    '''
    return self.edge_indices[self.indices+[cost_column]].set_index(keys=self.indices)[cost_column].to_dict()


def make_capex_dict(self,capex_column='capex'):
    '''Make dictionary of capex (c) as {(n,k,t) : c}
    '''
    return self.nodes[['name','commodity','capex']].set_index(['name','commodity'])['capex'].to_dict()


def make_edge_indices(self):
    '''Make edge indices as [(i,j,k,t)] for algebraic modelling
    '''
    return self.edge_indices[self.indices].set_index(keys=self.indices).index.to_list()


def make_storage_indices(self):
    '''Make storage indices as [(n,k,t)] for algebraic modelling
    '''
    storage_nodes   = get_storage_nodes(self.nodes)
    return [(n,k,t) \
        for n in storage_nodes.name \
            for k in ['electricity'] \
                for t in self.timesteps]


def make_capacity_indices(self):
    '''Make capacity indices as [(n,k,t)] for algebraic modelling
    '''
    source_nodes = get_source_nodes(self.nodes)
    node_list    = source_nodes.name.to_list() + ['israel_gas_storage','israel_battery_storage','jordan_battery_storage','west_bank_battery_storage','gaza_battery_storage']
    return [(n,k,t) \
        for n in node_list \
            for k in ['electricity'] \
                for t in self.timesteps]
        

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

def adjust_nodal_names(nodal_names):
    '''Clean-up nodal names from 'Example Node 1' to 'example_node_1'
    '''
    return nodal_names.str.lower().str.replace(' ','_')
    

def add_timestep_col(dataframe):
    '''add a timestep column to dataframe
    '''
    if 'timestep'.casefold() in dataframe.columns:
        return dataframe
    else:
        dataframe['timestep'] = [i for i in range(1,len(dataframe)+1)]
        return dataframe


def tidy_flow_data(flows):
    '''Convert nodal flow data to tidy format
    '''
    return flows.melt(id_vars=['timestep','date','hour','day','month','year'],
                      var_name='node',
                      value_name='value')
    

def add_toplogy(nodes,edges,i='from_id',j='to_id'):
    '''Add i,j,k notation to edges
    '''
    #find nearest node to the START coordinates of the line -- and return the 'ID' attribute
    edges[i] = edges.geometry.apply(lambda geom: snkit.network.nearest(Point(geom.coords[0]), nodes)['name'])
    #find nearest node to the END coordinates of the line -- and return the 'ID' attribute
    edges[j] = edges.geometry.apply(lambda geom: snkit.network.nearest(Point(geom.coords[-1]), nodes)['name'])
    return edges



#---
# Data reading/saving
#---

def init_vars(self,scenario,energy_objective):
    '''Initialise input variables
    '''
    self.connectivity       = connectivity
    self.global_variables   = global_variables
    self.scenario           = scenario
    self.energy_objective   = energy_objective
    if not energy_objective:
        self.ss_factor      = 0
    return self


# def manage_kwargs(self,key=None,value=None):
#     '''Manage kwargs
#     '''
    # # self sufficiency factor
    # if key == 'self_sufficiency_factor':
    #     if not self.energy_objective:
    #         self.ss_factor = 0
    #     else:
    #         self.ss_factor = value
    # else:
    #     self.ss_factor = self.global_variables['self_sufficiency_factor']
    # # res factor
    # if key == 'res_factor':
    #     self.res_factor = value
    # else:
    #     self.res_factor = 1
    # # uto factor
    # if key == 'coo_res_factor':
    #     self.coo_factor = value
    # else:
    #     self.coo_factor = self.global_variables['coop_res_target_2030']
    # # model name
    # if key == 'model_name':
    #     self.__name__ = value
    # else:
    #     self.__name__       = 'nextra'
    # super source
    # if key == 'super_source':
    #     if value:
    #         self.edges = add_super_source(self.nodes,self.edges)
    #         self.super_source = value
    #     else:
    #         self.super_source = False
    # else:
    #     self.super_source = False
    # # super source
    # if key == 'super_sink':
    #     if value:
    #         self.edges = add_super_sink(self.nodes,self.edges)
    #         self.super_sink = value
    #     else:
    #         self.super_sink = False
    # else:
    #     self.super_sink = False
    # return self


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


def flows_integrity_check(flows):
    '''Check integrity of flow data
    '''
    # check for negatives
    if not (flows.value < 0).any().any():
            pass
    else:
        flows.loc[flows.value < 0, 'value'] = np.nan
        flows = flows.dropna(axis=0)
        warnings.warn('Flow data contains negative values... dropped')
    # check hour column
    if not 'hour'.casefold() in flows.columns:
        pass
    else:
        if flows['hour'.casefold()].max() == 23:
            flows['hour'.casefold()] = flows['hour'.casefold()] + 1
    return flows


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
                              (flows.timestep <= flows.timestep.min() + kwargs.get("timesteps"))]
        # tidy
        flows = tidy_flow_data(flows)
        # check for negative values
        flows = flows_integrity_check(flows)
        return flows
    else:
        raise ValueError('flow file must be in csv format')


def fetch_edge_flow_results(model_run):
    '''Get edge flow results from model run
    '''
    arcFlows                = model_run.model.getAttr('x', model_run.arcFlows)
    keys                    = pd.DataFrame(arcFlows.keys(),columns=['from_id','to_id','commodity','timestep'])
    vals                    = pd.DataFrame(arcFlows.items(),columns=['key','value'])
    results_arcflows        = pd.concat([keys,vals],axis=1)
    results_arcflows        = model_run.flows[['hour','day','month','year','timestep']].merge(results_arcflows, on='timestep')
    results_arcflows        = results_arcflows[['from_id','to_id','commodity',
                                                'hour','day','month','year','timestep','value']]
    results_arcflows        = results_arcflows.drop_duplicates()
    return results_arcflows


def fetch_storage_results(model_run):
    '''Get storages results from model run
    '''
    storage_volumes              = model_run.model.getAttr('x', model_run.storage_volume)
    keys                         = pd.DataFrame(storage_volumes.keys(),columns=['node','commodity','timestep'])
    vals                         = pd.DataFrame(storage_volumes.items(),columns=['key','value'])
    results_storage_volumes      = pd.concat([keys,vals],axis=1)
    results_storage_volumes      = model_run.flows[['hour','day','month','year','timestep']].merge(results_storage_volumes, on='timestep')
    results_storage_volumes      = results_storage_volumes[['node','commodity','hour','day','month','year','timestep','value']]
    results_storage_volumes      = results_storage_volumes.drop_duplicates()
    return results_storage_volumes


def fetch_capacity_results(model_run):
    '''Get capacity indices results from model run
    '''
    capacity_indices                = model_run.model.getAttr('x', model_run.capacity_indices)
    keys                            = pd.DataFrame(capacity_indices.keys(),columns=['node','commodity','timestep'])
    vals                            = pd.DataFrame(capacity_indices.items(),columns=['key','value'])
    results_capacity_indices        = pd.concat([keys,vals],axis=1)
    results_capacity_indices        = results_capacity_indices[['node','commodity','timestep','value']]
    # map attributes
    results_capacity_indices        = map_attributes(model_run,results_capacity_indices,on='node')
    return results_capacity_indices



#---
# Postprocessing
#---

def map_attributes(model_run,results_dataframe,on='from_id'):
    '''Map raw node attributes to map onto results dataframe
    '''
    # get cols to map
    df_to_map = model_run.nodes[['name','subtype','territory']]
    # remove demand, junction and egypt generation (generic)
    df_to_map = df_to_map[~df_to_map.subtype.isin(['demand','junction','generic'])].reset_index(drop=True)
    # capitalise first letters
    df_to_map.subtype = df_to_map.subtype.str.title()
    # rename cols
    df_to_map[on]           = df_to_map['name']
    df_to_map['technology'] = df_to_map['subtype']
    df_to_map['territory']  = df_to_map['territory']
    # adjust technologies
    df_to_map.loc[df_to_map.technology.str.contains('Ccgt'),'technology'] = 'Gas'
    df_to_map.loc[df_to_map.technology.str.contains('Natural Gas'),'technology'] = 'Gas'
    # reindex dataframe
    df_to_map = df_to_map[[on,'technology','territory']]
    return results_dataframe.merge(df_to_map,on=on)



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
    self.indices        = self.global_variables['edge_index_variables']
    self.commodities    = self.edges.commodity.unique().tolist()
    self.node_types     = self.nodes.type.unique().tolist()
    self.technologies   = self.nodes.subtype.unique().tolist()
    self.functions      = self.nodes.function.unique().tolist()
    self.timesteps      = self.flows.timestep.unique().tolist()
    self.days           = self.flows.day.unique().tolist()
    self.months         = self.flows.month.unique().tolist()
    self.years          = self.flows.year.unique().tolist()
    return self


def add_super_source(nodes,edges,from_id='from_id'):
    '''Add super_source node to network
    '''
    new_edges = []
    for commodity in edges.commodity.unique():
        tmp_edges = pd.DataFrame({'from_id'     : 'super_source',
                                  'to_id'       : nodes.name.unique(),
                                  'commodity'   : commodity,
                                  'cost'        : global_variables['super_source_maximum'],
                                  'minimum'     : 0,
                                  'maximum'     : global_variables['super_source_maximum']
                                  })
        new_edges.append(tmp_edges)
    new_edges = pd.concat(new_edges,ignore_index=True)
    return edges.append(new_edges, ignore_index=True)


def add_super_sink(nodes,edges):
    '''Add super_sink node to network
    '''
    new_edges = []
    for commodity in edges.commodity.unique():
        tmp_edges = pd.DataFrame({'from_id'     : nodes.name.unique(),
                                  'to_id'       : 'super_sink',
                                  'commodity'   : commodity,
                                  'cost'        : global_variables['super_source_maximum'],
                                  'minimum'     : 0,
                                  'maximum'     : global_variables['super_source_maximum']
                                  })
        new_edges.append(tmp_edges)
    new_edges = pd.concat(new_edges,ignore_index=True)
    return edges.append(new_edges, ignore_index=True)


def map_timesteps_to_date(flows,mappable):
    ''' Function to map dates to timesteps '''
    # get time reference table
    id_vars = ['date','hour','day','month','year','timestep']
    time_ref = flows[id_vars].groupby(by='timestep').max().reset_index()
    # perform merge
    mapped = pd.merge(mappable,time_ref,on='timestep',how='right')
    return mapped
        

def add_time_index_to_edges(self):
    '''Add time index to edges (i.e., i,j,k,t)
    '''
    # Number of timesteps
    timesteps = self.flows.timestep.max()
    # add time
    self.edges['timestep'] = 1
    #repeat for each timestep
    new_edges = self.edges.append( [self.edges]*(timesteps-1) )
    #create time indices in loop
    tt = []
    for i in range(0,timesteps):
        t = self.edges.timestep.to_numpy() + i
        tt.append(t)
    tt = np.concatenate(tt,axis=0)
    #add time to pandas datafram
    new_edges['timestep'] = tt
    # reset index
    new_edges = new_edges.reset_index(drop=True)
    # add dates
    new_edges = map_timesteps_to_date(self.flows,new_edges)
    # reorder
    col_order = ['from_id','to_id','commodity','timestep',
                 'date','hour','day','month','year',
                 'cost','minimum','maximum','capex']
    self.edge_indices = new_edges[col_order]
    return self



#---
# Scenarios
#---

def update_connectivity(self,scenario,**kwargs):
    ''' Update connectivity based on scenario
    '''
    if self.scenario == 'BAU' or self.scenario == 'BAS':
        # Business as usual
        # Jordan ->
        self.connectivity['jordan_to_westbank']     = 99999
        self.connectivity['jordan_to_israel']       = 0
        #Israel ->
        self.connectivity['israel_to_westbank']     = 99999
        self.connectivity['israel_to_jordan']       = 0
        self.connectivity['israel_to_gaza']         = 99999
        #West Bank ->
        self.connectivity['westbank_to_israel']     = 0
        self.connectivity['westbank_to_jordan']     = 0
        #Egypt ->
        self.connectivity['egypt_to_gaza']          = 27

    elif self.scenario == 'NCO':
        # No cooperation: each state acts as an individual entity
        # Jordan ->
        self.connectivity['jordan_to_westbank']     = 0
        self.connectivity['jordan_to_israel']       = 0
        #Israel ->
        self.connectivity['israel_to_westbank']     = 0
        self.connectivity['israel_to_jordan']       = 0
        self.connectivity['israel_to_gaza']         = 0
        #West Bank ->
        self.connectivity['westbank_to_israel']     = 0
        self.connectivity['westbank_to_jordan']     = 0
        #Egypt ->
        self.connectivity['egypt_to_gaza']          = 0

    elif self.scenario == 'EAG':
        # Extended arab grid: palestine turns to jordan; israel an energy island
        # Jordan ->
        self.connectivity['jordan_to_westbank']     = 99999
        self.connectivity['jordan_to_israel']       = 0
        #Israel ->
        self.connectivity['israel_to_westbank']     = 0
        self.connectivity['israel_to_jordan']       = 0
        self.connectivity['israel_to_gaza']         = 0
        #West Bank ->
        self.connectivity['westbank_to_israel']     = 0
        self.connectivity['westbank_to_jordan']     = 0
        #Egypt ->
        self.connectivity['egypt_to_gaza']          = 27

    elif self.scenario == 'COO':
        # Cooperation between each state
        # --        
        # Jordan ->
        self.connectivity['jordan_to_westbank']     = 99999
        self.connectivity['jordan_to_israel']       = kwargs.get("jordan_to_israel", 99999)
        #Israel ->
        self.connectivity['israel_to_westbank']     = 99999
        self.connectivity['israel_to_jordan']       = 99999
        self.connectivity['israel_to_gaza']         = 99999
        #West Bank ->
        self.connectivity['westbank_to_israel']     = 0
        self.connectivity['westbank_to_jordan']     = 0
        #Egypt ->
        self.connectivity['egypt_to_gaza']          = 27
    
    elif self.scenario == 'UTO':
        # Cooperation between each state
        # --        
        # Jordan ->
        self.connectivity['jordan_to_westbank']     = 99999
        self.connectivity['jordan_to_israel']       = kwargs.get("jordan_to_israel", 99999)
        #Israel ->
        self.connectivity['israel_to_westbank']     = 99999
        self.connectivity['israel_to_jordan']       = 99999
        self.connectivity['israel_to_gaza']         = 99999
        #West Bank ->
        self.connectivity['westbank_to_israel']     = 0
        self.connectivity['westbank_to_jordan']     = 0
        #Egypt ->
        self.connectivity['egypt_to_gaza']          = 99999
    return self


def update_for_scenario(self,connectivity_dict):
    '''Update edges dataframe to match scenario
    '''
    # Jordan --> Israel, West Bank
    self.edges.loc[(self.edges.from_id.isin(['jordan_generation'])) \
              & (self.edges.to_id.isin(['west_bank_energy_demand'])),'maximum']     = connectivity_dict['jordan_to_westbank']
    self.edges.loc[(self.edges.from_id.isin(['jordan_generation'])) \
              & (self.edges.to_id.isin(['israel_energy_demand'])),'maximum']        = connectivity_dict['jordan_to_israel']

    # Israel --> West Bank, Gaza, Jordan
    self.edges.loc[(self.edges.from_id.isin(['israel_generation'])) \
              & (self.edges.to_id.isin(['west_bank_energy_demand'])),'maximum']     = connectivity_dict['israel_to_westbank']
    self.edges.loc[(self.edges.from_id.isin(['israel_generation'])) \
              & (self.edges.to_id.isin(['gaza_energy_demand'])),'maximum']          = connectivity_dict['israel_to_gaza']
    self.edges.loc[(self.edges.from_id.isin(['israel_generation'])) \
              & (self.edges.to_id.isin(['jordan_energy_demand'])),'maximum']        = connectivity_dict['israel_to_jordan']

    # Egypt --> Gaza
    self.edges.loc[(self.edges.from_id.isin(['egypt_generation'])) \
              & (self.edges.to_id.isin(['gaza_energy_demand'])),'maximum']          = connectivity_dict['egypt_to_gaza']

    # West Bank --> Israel, Jordan
    self.edges.loc[(self.edges.from_id.isin(['west_bank_generation'])) \
              & (self.edges.to_id.isin(['israel_energy_demand'])),'maximum']        = connectivity_dict['westbank_to_israel']
    self.edges.loc[(self.edges.from_id.isin(['west_bank_generation'])) \
              & (self.edges.to_id.isin(['jordan_energy_demand'])),'maximum']        = connectivity_dict['westbank_to_jordan']
    
    return self