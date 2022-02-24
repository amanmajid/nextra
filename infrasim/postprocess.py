'''
    postprocess.py
        
        Postprocessing results via the NexTra results class

    @amanmajid
'''

#---
# Modules
#---

import random
import seaborn as sns
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import warnings

import plotly.io as pio
import plotly.graph_objs as go
from plotly.offline import download_plotlyjs, init_notebook_mode, plot, iplot


init_notebook_mode(connected=True)

# relative imports
from .utils import *
from .global_variables import *



#---
# Results class
#---

class nextra_postprocess():


    def __init__(self,model_run):
        '''Init class
        '''

        # init raw vars
        self.nodes = model_run.nodes
        self.edges = model_run.edges
        self.flows = model_run.flows

        # init results
        self.results_edge_flows             = fetch_edge_flow_results(model_run)
        self.results_storages               = fetch_storage_results(model_run)
        self.results_capacities             = fetch_capacity_results(model_run)
        self.results_capacity_change        = self.get_capacity_change()
        self.results_costs                  = self.compute_costs()

        # remove gas storage from results
        self.results_edge_flows             = self.drop_node_from_edge_flows(node_to_remove='israel_gas_storage')


    def get_regional_capacity(self,territory):
        '''Return capacity for a given territory
        '''
        caps = self.results_capacities[self.results_capacities.territory==territory]
        caps = caps.reset_index(drop=True)
        return caps.groupby(by=['node','technology']).max().reset_index()
    

    def get_regional_capacity_change(self,territory):
        '''Return capacity for a given territory
        '''
        caps = self.results_capacity_change[self.results_capacity_change.territory==territory]
        caps = caps.reset_index(drop=True)
        return caps.groupby(by=['node','technology']).max().reset_index()


    def generate_random_colour():
        '''Return random hex colour
        '''
        return "%06x" % random.randint(0, 0xFFFFFF)
    

    def get_capacities(self,timestep=1):
        '''Return capacities from results at a given timestep
        '''
        return self.results_capacities.loc[self.results_capacities.timestep==timestep][['node','value','technology','territory']]
    

    def get_baseline_capacities(self):
        '''Return 2020 capacities
        '''
        starting_caps = self.nodes[['name','capacity']]
        starting_caps['node'] = starting_caps.name
        return starting_caps[['node','capacity']].copy()


    def get_capacity_change(self):
        '''Return change in capacity between first and final timestep
        '''
        # get starting capacities
        starting_capacity = self.get_baseline_capacities().set_index('node')['capacity'].to_dict()
        # get final capacities
        final_capacity = self.get_capacities(timestep=self.results_capacities.timestep.max()).reset_index(drop=True).copy()
        # compute difference
        final_capacity['starting_capacity'] = final_capacity.node.map(starting_capacity)
        final_capacity['final_capacity']    = final_capacity['value']
        final_capacity['capacity_change']   = final_capacity['final_capacity'] - final_capacity['starting_capacity']
        return final_capacity[['node','capacity_change','technology','territory']]


    def compute_costs(self,discount_rate=0.68,ignore_negatives=True):
        '''Calculate costs (opex,capex,totex) of plans
        '''
        capacities = self.results_capacity_change.copy()
        # ignore negative values
        if not ignore_negatives:
            pass
        else:
            capacities.loc[capacities.capacity_change < 0, 'capacity_change'] = 0
        # map costs
        capacities['capex'] = capacities.capacity_change * capacities.technology.map(capex) * 10**3 * discount_rate     # $ = MW * (1000 kW/MW) $/kW * discount_rate
        capacities['opex']  = capacities.capacity_change * capacities.technology.map(opex) * 10**3                      # $/yr = MW * (1000 kW/MW) $/kW-year 
        capacities['totex'] = capacities['opex'] + capacities['capex']
        return capacities


    def plot_hourly_profile(self,day,month,year=2030,territory=None,**kwargs):
        '''Plot hourly profile of energy supply for a given day
        '''
        # index for day
        idx = self.results_edge_flows.loc[(self.results_edge_flows.day == day) & \
                                        (self.results_edge_flows.month == month) & \
                                        (self.results_edge_flows.year == year)].reset_index(drop=True)
        # groupby hour
        idx = idx.groupby(by=['from_id','hour']).sum().reset_index()
        # drop generation nodes
        idx = idx.loc[~idx.from_id.str.contains('generation')].reset_index(drop=True)
        # map tech and territory
        idx = map_attributes(self,idx)
        if territory is None:
            # sum across all regions
            idx = idx.groupby(by=['technology','hour']).sum().reset_index()
        else:
            # index by territory
            idx = idx.loc[idx.territory.isin([territory])].reset_index(drop=True)
        # reindex
        idx = idx[['hour','value','technology']]
        # battery charging/discharging
        idx.loc[(idx.value <= 0) & (idx.technology == 'Battery'),'technology'] = 'Battery Discharge'
        idx.loc[(idx.value > 0) & (idx.technology == 'Battery'),'technology'] = 'Battery Charge'
        # pivot table
        idx = idx.pivot_table(columns='technology',index='hour',values='value')
        # plot
        idx.plot.area(ax=kwargs.get("ax", None),
                      #cmap=kwargs.get("cmap", 'YlGnBu'),
                      color=[technology_color_dict.get(x, '#333333') for x in idx.columns],
                      linewidth=kwargs.get("linewidth", 0),
                      alpha=kwargs.get("alpha", 1),)
    

    def plot_flows_heatmap(self,var,**kwargs):
        '''Plot a heatmap from flows data (x: month, y: hour, z: var)
        '''
        # get flows
        idx = self.flows.copy()
        # index var
        idx = idx.loc[idx.node == var].reset_index(drop=True)
        # reindex df
        idx = idx[['month','hour','value']]
        # pivot table
        idx = idx.pivot_table(columns='month',values='value',index='hour',aggfunc=kwargs.get('aggfunc',np.mean))
        # plot
        tmp_ax = sns.heatmap(idx,
                            linewidth=kwargs.get('linewidth',0),
                            cmap=kwargs.get('cmap','YlGnBu'),
                            ax=kwargs.get('ax',None))
        # frame
        for _, spine in tmp_ax.spines.items():
            spine.set_visible(True)
    

    def plot_flows_sankey(self,**kwargs):
        '''Plot a sankey diagram visualising flows
        '''
        # get edge flows
        flows = self.results_edge_flows.copy()
        # remove israel_gas_storage_node
        if 'israel_gas_storage' in flows.from_id.unique():
            flows.loc[flows.from_id=='israel_gas_storage','from_id'] = 'israel_natural_gas'
            flows.loc[flows.to_id=='israel_gas_storage','to_id'] = 'israel_generation'
            flows = flows.groupby(by=['from_id','to_id','commodity','hour','day','month','year','timestep','scenario']).min().reset_index()
            warnings.warn('israel_gas_storage removed')
        # sum across all timesteps
        flows = flows.groupby(by=['from_id','to_id']).sum().reset_index(drop=False)
        # Make nodes 
        count=0
        nodal_dict={}
        nodes=[ ['ID', 'Label', 'Color'] ]
        all_nodes = list(flows.from_id.unique()) + list(flows.to_id.unique())
        for i in range(0,len(all_nodes)):
            nodes.append( [i,all_nodes[i],"%06x" % random.randint(0, 0xFFFFFF)] )
            nodal_dict[all_nodes[i]] = i

        # Make links
        flows['Source']     = flows.from_id.map(nodal_dict)
        flows['Target']     = flows.to_id.map(nodal_dict)
        flows['Value']      = flows.value
        flows['Link Color'] = 'rgba(127, 194, 65, 0.2)'
            #reindex
        flows = flows[['Source','Target','Value','Link Color']]
        count=0
        links=[ ['Source','Target','Value','Link Color'], ]
        for i in flows.index:
            links.append( [ flows.loc[i,'Source'],
                            flows.loc[i,'Target'],
                            flows.loc[i,'Value'],
                            flows.loc[i,'Link Color'] ] )
        
        #######
        # PLOT
        # Retrieve headers and build dataframes
        nodes_headers = nodes.pop(0)
        links_headers = links.pop(0)
        df_nodes = pd.DataFrame(nodes, columns = nodes_headers)
        df_links = pd.DataFrame(links, columns = links_headers)

        # Sankey plot setup
        data_trace = dict(
            type='sankey',
            domain = dict(
            x =  [0,1],
            y =  [0,1]
            ),
            orientation = "h",
            valueformat = ".0f",
            node = dict(
            pad = 10,
            # thickness = 30,
            line = dict(
                color = "black",
                width = 0
            ),
            label =  df_nodes['Label'].dropna(axis=0, how='any'),
            color = df_nodes['Color']
            ),
            link = dict(
            source = df_links['Source'].dropna(axis=0, how='any'),
            target = df_links['Target'].dropna(axis=0, how='any'),
            value = df_links['Value'].dropna(axis=0, how='any'),
            color = df_links['Link Color'].dropna(axis=0, how='any'),
        )
        )

        layout = dict(
                title = kwargs.get('title','Sankey'),
            height = kwargs.get('height',720),
            font = dict(
            size = kwargs.get('fontsize',12),),)

        fig = dict(data=[data_trace], layout=layout)
        iplot(fig,validate=False)


    def drop_node_from_edge_flows(self,node_to_remove):
        '''Function to drop junction from edge flow results
        '''
        df = self.results_edge_flows.copy()
        # get new i,j
        new_i = df[df.to_id == node_to_remove].from_id.unique()[0]
        new_j = df[df.from_id == node_to_remove].to_id.unique()[0]
        # change i
        df.loc[df.from_id == node_to_remove,'from_id'] = new_i
        # change j
        df.loc[df.to_id == node_to_remove,'to_id'] = new_j
        # drop
        size_before = df.shape[0]
        df = df.groupby(by=['from_id','to_id','commodity','hour','day','month','year']).mean().reset_index()
        size_after = df.shape[0]
        # print size difference
        # print('Removed ' + str(size_before - size_after) + ' rows')
        return df

    
    def plot_battery_charge(self,node,days=10,month=6,year=2030):
        '''Plot battery charge and discharge
        '''
    

    def plot_solar_capacity_factor(self,node='all',ax=None,color='teal'):
        '''Plot daily average capacity factors
        '''
        s = self.results_edge_flows.copy()
        c = self.get_capacities().copy()

        if node == 'all':
            s = s.loc[s.from_id.str.contains('solar')]
            c = c.loc[c.node.str.contains('solar')]
        else:
            s = s.loc[s.from_id==node]
            c = c.loc[c.node==node]

        # sum across timesteps
        s = s.groupby(by=['timestep','hour','day','month','year']).sum().reset_index()    
        c = c.value.sum()

        # compute capacity factors
        s['cf'] = s['value'].divide(c) * 100

        # compute capacity factors monthly mean
        s = s.groupby(by=['day','month']).mean().reset_index()

        # overwrite timestep
        s['timestep'] = s.index + 1
        
        if not ax:
            f,ax = plt.subplots(nrows=1,ncols=1,figsize=(8,4))
            
        sns.lineplot(x='timestep',y='cf',data=s,label=node,ax=ax,color=color)
        # plot mean
        ax.axhline(y=s.cf.mean(), color='black', linestyle='--')
    

    def plot_wind_capacity_factor(self,node='all',ax=None,color='teal'):
        '''Plot daily average capacity factors
        '''
        s = self.results_edge_flows.copy()
        c = self.get_capacities().copy()

        if node == 'all':
            s = s.loc[s.from_id.str.contains('wind')]
            c = c.loc[c.node.str.contains('wind')]
        else:
            s = s.loc[s.from_id==node]
            c = c.loc[c.node==node]

        # sum across timesteps
        s = s.groupby(by=['timestep','hour','day','month','year']).sum().reset_index()    
        c = c.value.sum()

        # compute capacity factors
        s['cf'] = s['value'].divide(c) * 100

        # compute capacity factors monthly mean
        s = s.groupby(by=['day','month']).mean().reset_index()

        # overwrite timestep
        s['timestep'] = s.index + 1
        
        if not ax:
            f,ax = plt.subplots(nrows=1,ncols=1,figsize=(8,4))
            
        sns.lineplot(x='timestep',y='cf',data=s,label=node,ax=ax,color=color)
        # plot mean
        ax.axhline(y=s.cf.mean(), color='black', linestyle='--')

    
    def plot_battery_storage_volume(self,node='all',days=1,month=6,year=2030,ax=None,color='teal'):
        '''Plot battery storage volumes as a time series
        '''
        t = self.results_storages.copy()
        c = self.results_capacities.copy()

        if node == 'all':
            t = t.loc[t.node.str.contains('battery')].reset_index(drop=True)
            c = c[c.node.str.contains('storage')].value.sum()
        else:
            t = t.loc[t.node==node].reset_index(drop=True)
            c = c[c.node==node].value.max()
        # index by time
        t = t.loc[(t.month==month) & (t.year==year) & (t.day<=days)].reset_index(drop=True)
        # calculate SOC
        t['soc'] = t.value.divide(c) * 100
        # plot
        if not ax:
            f,ax = plt.subplots(nrows=1,ncols=1,figsize=(8,4))
        sns.lineplot(x='timestep',y='soc',data=t,color='teal',ax=ax)
        ax.axhline(y=100,color='black',linestyle='--')
        ax.set_ylabel('SOC [%]')

    
    def plot_supply_curve(self,region='israel',days=1,month=6,year=2030,ax=None,blend_curtailment=True):
        '''Plot supply and demand curves for a given region
        '''
        flows = self.results_edge_flows.copy()
        # tag curtailed
        flows.loc[flows.to_id.str.contains('curtail'),'from_id'] = \
        flows.loc[flows.to_id.str.contains('curtail'),'from_id'] + '_curtailed'
        if not blend_curtailment:
            pass
        else:
            flows.loc[flows.to_id.str.contains('curtail'),'from_id'] = region + '_' + 'curtailed'
        # identify battery charge/discharge
        flows['state'] = ''
        flows['prefix'] = flows['from_id'].str.split('_',expand=True)[0]
        flows.loc[flows.prefix=='west','prefix'] = 'west_bank'
        # tag discharge
        flows.loc[(flows.from_id.str.contains('battery')),'state'] = \
            flows.loc[(flows.from_id.str.contains('battery')),'prefix'] + '_' + 'battery_discharge'
        # tag discharge
        flows.loc[(flows.to_id.str.contains('battery')),'state'] = \
            flows.loc[(flows.to_id.str.contains('battery')),'prefix'] + '_' + 'battery_charge'
        # change from_id for battery nodes
        flows.loc[flows.state!='','from_id'] = flows.loc[flows.state!='','state']
        # sum flows for each node at each timestep
        flows = flows.groupby(by=['from_id','timestep','hour','day','month','year','scenario']).sum().reset_index()
        # drop generation
        flows = flows[~flows.from_id.str.contains('generation')].reset_index(drop=True)
        # index flows
        flows = flows.loc[(flows.from_id.str.contains(region))].reset_index(drop=True)
        # index by time
        flows = flows.loc[(flows.month==month) \
                        & (flows.year==year) \
                        & (flows.day<=days)].reset_index(drop=True)
        # remove technologies with zero capacity
        zero_caps = flows.groupby(by='from_id').sum().reset_index()
        zero_caps = zero_caps.loc[zero_caps.value == 0, 'from_id'].to_list()
        flows = flows.loc[~flows.from_id.isin(zero_caps)].reset_index(drop=True)

        # make curtailed flows negative
        flows.loc[flows.from_id.str.contains('curtail'),'value'] = \
            -flows.loc[flows.from_id.str.contains('curtail'),'value']
        # make battery charge negative
        flows.loc[flows.from_id.str.contains('battery_charge'),'value'] = \
            -flows.loc[flows.from_id.str.contains('battery_charge'),'value']
        # get demand curve
        demand = self.flows.copy()
        demand = demand[demand.node.str.contains('demand')].reset_index(drop=True)
        demand = demand.loc[demand.node.str.contains(region)].reset_index(drop=True)
        # index by time
        demand = demand.loc[(demand.month==month) \
                            & (demand.year==year) \
                            & (demand.day<=days)].reset_index(drop=True)
        # pivot table
        idx = flows.pivot_table(columns='from_id',index='timestep',values='value')
        dem = demand.pivot_table(columns='node',index='timestep',values='value')

        # plot
        if not ax:
            f,ax = plt.subplots(figsize=(20,8),nrows=1,ncols=1)

        dem.plot.line(ax=ax,
                    linewidth=2,
                    color='navy',
                    marker='o',
                    alpha=1)

        idx.plot.area(ax=ax,
                    stacked=True,
                    linewidth=1,
                    color=[supply_color_dict.get(x, '#333333') for x in idx.columns],
                    alpha=0.7)