import os
import seaborn as sns
import matplotlib.pyplot as plt
import pickle 
import pickle
import matplotlib as mpl

import warnings
warnings.filterwarnings('ignore')

import sys
sys.path.append('../')

from infrasim.optimise import *
from infrasim.utils import *


def merge_capacity_data(results_dict):
    '''Returns a dataframe with merged capacity data based on a dictionary containing a set of results class
    '''
    # init blank df
    capacities = pd.DataFrame()
    # loop results 
    for k in results_dict.keys():
        df = results_dict[k].results_capacities
        capacities = capacities.append(df,ignore_index=True)
    return capacities


#File paths
nodes = '../data/nextra/spatial/network/nodes.shp'
edges = '../data/nextra/spatial/network/edges.shp'
flows = '../data/nextra/nodal_flows/processed_flows_2030.csv'

# Params
timesteps=None#7000
super_source=False
pprint=True
save_figures=True

infrasim_init_directories()

ss_factors = [i/100 for i in np.arange(0,101,10).tolist()]

results = {}
for s in ss_factors:
    print(f'> Running self-sufficiency factor: {s}')
    model_run = nextra(nodes,edges,flows,
                       scenario='COO',
                       energy_objective=True,
                       timesteps=timesteps,
                       self_sufficiency_factor=s)

    model_run.build()
    model_run.run(pprint=False)
    try:
        model_results = model_run.get_results()
        # add scenarios to results
        if s == 'BAU' and scenarios[s] == False:
            s = 'BAS'
        model_results.results_capacities['self_sufficiency_factor']       = s
        model_results.results_storages['self_sufficiency_factor']         = s
        model_results.results_edge_flows['self_sufficiency_factor']       = s
        model_results.results_capacity_change['self_sufficiency_factor']  = s
        model_results.results_costs['self_sufficiency_factor']            = s
        # append results
        results[ 'COO_' + str(s) ] = model_results
    except:
        print('> FAILED! ' + str(s))

capacities = merge_capacity_data(results)
capacities = capacities.groupby(by=['territory','self_sufficiency_factor','node']).max().reset_index()
capacities = capacities.loc[capacities.territory.isin(['Gaza','West Bank'])].reset_index(drop=True)
capacities = capacities.groupby(by=['territory','self_sufficiency_factor']).sum().reset_index()
capacities = capacities[['territory','self_sufficiency_factor','value']]
capacities.to_csv('../outputs/results/sensitivity_coop_sufficiency.csv',index=False)
print('done')