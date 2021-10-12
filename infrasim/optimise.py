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


    def __init__(self,path_to_nodes,path_to_edges,path_to_flows,scenario,energy_objective,**kwargs):
        
        '''
        
        Parameters
        ----------
        path_to_nodes : str
            Path to nodal data.
        path_to_edges : str
            Path to edge data.
        path_to_flows : str
            Path to flow data.
        scenario : str
            Define scenario to run.
        energy_objective : bool, True/False
            Parameter to observe or ignore renewable energy targets.

        Returns
        -------
        None.

        '''
        
        # init vars
        self = init_vars(self,scenario,energy_objective)
    
        # read node
        self.nodes = read_node_data(path_to_nodes)

        # read edge data
        self.edges = read_edge_data(path_to_edges)
        
        # add topology to edges
        self.edges = add_toplogy(self.nodes,self.edges)

        # read flow data
        self.flows = read_flow_data(path_to_flows,
                                    year=kwargs.get("year", False),
                                    timesteps=kwargs.get("timesteps", False))
        
        # handle kwargs
        if not kwargs:
            self = manage_kwargs(self)
        else:
            for key,value in kwargs.items():
                self = manage_kwargs(self,key,value)
        
        # adjust scenario
        self = adjust_for_scenario(self,scenario)

        # define sets
        self = define_sets(self)
        
        # add time index to edge data
        self = add_time_index_to_edges(self)

        # define gurobi model
        self.model = gp.Model( create_model_name( self.__name__ ) )

        # init dir for outputs
        self.results_dir = self.global_variables['results_directory'] + self.model.ModelName
        create_dir(self.results_dir)


    def build(self):
        '''Build optimisation model using GurobiPy
        '''
        
        #======================================================================
        # DECISION VARIABLES
        #======================================================================

        #---
        # arcflows
        self.arc_indicies = edge_indices_to_dict(self,varname='index')
        self.arcFlows     = self.model.addVars(arc_indicies,name="arcflow")

        #---
        # storage volumes
        storage_nodes         = utils.get_nodes(nodes=self.nodes,index_column='Type',lookup='storage')

        storage_indices       = [(n, storage_nodes.loc[storage_nodes.Name==n,'Commodity'].values[0], t)
                                 for n in storage_nodes.Name
                                 for t in self.timesteps]

        self.storage_volume   = self.model.addVars(storage_indices,lb=0,name="storage_volume")

        #---
        # capacity at each node
        source_nodes     = utils.get_nodes(nodes=self.nodes,index_column='Type',lookup='source')
        node_list        = source_nodes.Name.to_list() + ['israel_gas_storage']

        capacity_indices = [(n,k,t)
                            for n in node_list
                            for k in self.nodes.loc[self.nodes.Name==n,'Commodity']
                            for t in self.timesteps]

        self.capacity_indices = self.model.addVars(capacity_indices,lb=0,name="capacity_indices")

        #---
        # capacity variation at each node
        capacity_indices = [(n,k,t)
                            for n in node_list
                            for k in self.nodes.loc[self.nodes.Name==n,'Commodity']
                            for t in self.timesteps]

        self.capacity_change = self.model.addVars(capacity_indices,lb=-10000,name="capacity_change")



    def run(self,pprint=True,write=True):
        '''Function to solve GurobiPy model
        '''



    def debug(self,output_path='../outputs/__cache__/'):
        '''Compute model Irreducible Inconsistent Subsystem (IIS) to help deal with infeasibilies
        '''
        self.model.computeIIS()
        self.model.write(output_path+'debug_report.ilp')