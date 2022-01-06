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
        # pivot table
        idx = idx.pivot_table(columns='technology',index='hour',values='value')
        # plot
        idx.plot.area(ax=kwargs.get("ax", None),
                    cmap=kwargs.get("cmap", 'YlGnBu'),
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