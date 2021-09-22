'''
    optimise.py
        
        Capacity planning model for Israel, Jordan, and the Palestinian Authority

    @amanmajid
'''

#---
# Modules
#---

import gurobipy as gp

# relative imports
from .utils import *



#---
# NexTra class
#---

class nextra():


    def __init__(self,path_to_nodes,path_to_edges,path_to_flows,**kwargs):
        
        '''
        
        Parameters
        ----------
        path_to_nodes : str
            DESCRIPTION.
        path_to_edges : str
            DESCRIPTION.
        path_to_flows : str
            DESCRIPTION.
        **kwargs : TYPE
            DESCRIPTION.

        Returns
        -------
        None.

        '''
    
        # read node
        self.nodes = read_node_data(path_to_nodes)

        # read edge data
        self.edges = read_edge_data(path_to_edges)

        # read flow data
        self.flows = read_flow_data(path_to_flows,
                                    year=kwargs.get("year", False),
                                    timesteps=kwargs.get("timesteps", False))

        # define sets
        self = define_sets(self)

        # define gurobi model
        self.model = gp.Model( create_model_name(base=kwargs.get('model_name', 'nextra')) )

        # init dir for outputs
        self.results_dir = global_variables['results_directory'] + self.model.ModelName
        create_dir(self.results_dir)


    def build(self):
        '''Build optimisation model using GurobiPy
        '''



    def run(self,pprint=True,write=True):
        '''Function to solve GurobiPy model
        '''



    def debug(self,output_path='../outputs/__cache__/'):
        '''Compute model Irreducible Inconsistent Subsystem (IIS) to help deal with infeasibilies
        '''
        self.model.computeIIS()
        self.model.write(output_path+'debug_report.ilp')