'''
    postprocess.py
        
        Postprocessing results via the NexTra results class

    @amanmajid
'''

#---
# Modules
#---

import matplotlib.pyplot as plt

# relative imports
from .utils import *



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
        self.results_edge_flows = fetch_edge_flow_results(model_run)
        self.results_storages   = fetch_storage_results(model_run)
        self.results_capacities = fetch_capacity_results(model_run)

        # map technologies and territories
        self.results_edge_flows = map_tech_and_territory(model_run,self.results_edge_flows)
    

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
        # adjust by region
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