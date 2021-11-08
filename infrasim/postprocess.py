'''
    postprocess.py
        
        Postprocessing results via the NexTra results class

    @amanmajid
'''

#---
# Modules
#---

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