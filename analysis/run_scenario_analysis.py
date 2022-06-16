import os
import seaborn as sns
import matplotlib.pyplot as plt
import pickle 
import time

import warnings
warnings.filterwarnings('ignore')

import sys
sys.path.append('../')

from infrasim.optimise import *
from infrasim.utils import *


# save
def save_object(obj, filename):
    with open(filename, 'wb') as outp:  # Overwrites any existing file.
        pickle.dump(obj, outp, pickle.HIGHEST_PROTOCOL)


#File paths
nodes = '../data/nextra/spatial/network/nodes.shp'
edges = '../data/nextra/spatial/network/edges.shp'
flows = '../data/nextra/nodal_flows/processed_flows_2030_low.csv'


# Params
timesteps=None#24*15
super_source=False
pprint=False
save_figures=True
super_sink=False
super_source=False
curtailment=True

infrasim_init_directories()

scenarios = {'BAS' : False,
             'BAU' : True,
             'NCO' : True,
             #'EAG' : True,
             'COO' : True,
             #'UTO' : True,
            }

results = {}
for s in scenarios:
    start_time = time.time()
    model_run = nextra(nodes,edges,flows,
                       scenario=s,
                       energy_objective=scenarios[s],
                       timesteps=timesteps,
                       super_source=super_source,
                       super_sink=super_sink,
                       curtailment=curtailment,
                       #res_factor=99,
                       #model_name='meow',
                      )

    model_run.build()
    model_run.run(pprint=pprint)
    try:
        model_results = model_run.get_results()
        # add scenarios to results
        if s == 'BAU' and scenarios[s] == False:
            s = 'BAS'
        model_results.results_capacities['scenario']       = s
        model_results.results_storages['scenario']         = s
        model_results.results_edge_flows['scenario']       = s
        model_results.results_capacity_change['scenario']  = s
        model_results.results_costs['scenario']            = s
        # append results
        results[s] = model_results
        # get time
        hours,minutes,seconds = time_elapsed(start_time)
        print('> Completed: ' + s + ' in ' + '%dh:%dm:%ds' %(hours,minutes,seconds))
    except:
        print('> FAILED! ' + s)


save_object(results, '../outputs/results/model_run_results.pkl')

print('> Done.')