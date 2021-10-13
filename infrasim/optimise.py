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
        
        # clean nodal names
        self.nodes.name = adjust_nodal_names(self.nodes.name)

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
        self.arc_indicies = make_edge_indices(self)
        self.arcFlows     = self.model.addVars(self.arc_indicies,name="arcflow")

        #---
        # storage volumes
        storage_indices     = make_storage_indices(self)
        self.storage_volume = self.model.addVars(storage_indices,lb=0,name="storage_volume")

        #---
        # capacity at each node
        capacity_indices      = make_capacity_indices(self)  
        self.capacity_indices = self.model.addVars(capacity_indices,lb=0,name="capacity_indices")

        #---
        # capacity variation at each node
            # do we want to exclude gas storages here????
        self.capacity_change = self.model.addVars(capacity_indices,lb=-10000,name="capacity_change")
        
        
        
        #======================================================================
        # OBJECTIVE FUNCTION
        #======================================================================

        #---
        # Minimise cost of flow + capex

        # create cost/capex dict
        self.cost_dict  = make_cost_dict(self)
        self.capex_dict = make_capex_dict(self)

        #---
        # SET OBJECTIVES

        # (1) Cost of flow -> min.
        self.model.setObjectiveN(
            gp.quicksum(self.arcFlows[i,j,k,t] * self.cost_dict[i,j,k,t]
                        for i,j,k,t in self.arcFlows),0,weight=1)

        # (2) Capacity of nodes -> min.
        self.model.setObjectiveN(
            gp.quicksum(self.capacity_indices[n,k,t] * self.capex_dict[n,k]
                        for n,k,t in self.capacity_indices),0,weight=1)

        # #---
        # # Maximise storage
        # self.model.setObjectiveN( gp.quicksum(self.storage_volume[n,k,t]
        #                                       for n,k,t in self.storage_volume),1,weight=-1)
        
        
        
        #======================================================================
        # CONSTRAINTS
        #======================================================================


        #------------------
        # SUPER NODES
        #------------------

        if not self.super_source:
            pass
        else:
            # constrain
            self.model.addConstrs(
                (self.arcFlows.sum('super_source','*',k,t)  <= self.global_variables['super_source_maximum']
                    for t in self.timesteps
                        for k in self.commodities),'super_source_supply')

        if not self.super_sink:
            pass
        else:
            # constrain
            self.model.addConstrs(
                (self.arcFlows.sum('*','super_sink',k,t)  >= 0
                     for t in self.timesteps
                         for k in self.commodities),'super_sink_demand')
        
        
        
        #----------------------------------------------------------------------
        # ARC FLOW BOUNDS
        #----------------------------------------------------------------------

        upper_bound = make_edge_bound_dict(self,bound_column='maximum')
        lower_bound = make_edge_bound_dict(self,bound_column='minimum')
        
        # Flows must be below upper bounds
        self.model.addConstrs(
            (self.arcFlows[i,j,k,t] <= upper_bound[i,j,k,t]
                 for i,j,k,t in self.arcFlows),'upper_bound')

        # Flows must be above lower bounds
        self.model.addConstrs(
            (lower_bound[i,j,k,t] <= self.arcFlows[i,j,k,t]
                 for i,j,k,t in self.arcFlows),'lower_bound')



        #----------------------------------------------------------------------
        # CAPACITY CHANGES
        #----------------------------------------------------------------------
        
        # get initial capacities as dict
        expandable_nodes = make_nodal_capacity_dict(self)
        
        # capacity changes
        for y in self.years:
            timesteps_by_year = get_timesteps_by_year(self,y)
            timestep_1 = self.time_ref[self.time_ref.year==y].timestep.min()
            if y==2019:
                # capacity at t=1 as defined in nodal file
                self.model.addConstrs((
                    self.capacity_indices[n,k,t] \
                        == expandable_nodes[n,k]
                            for n,k,t in self.capacity_indices if t==1),'init_cap')
                # capacity at t>1
                self.model.addConstrs((
                    self.capacity_indices[n,k,t] == \
                        self.capacity_indices[n,k,t-1] + self.capacity_change[n,k,t]
                            for n,k,t in self.capacity_indices if t>1),'cap_after_init')
                # no change in capacity in 2019
                self.model.addConstrs((
                    self.capacity_change[n,k,t] == 0
                        for n,k,t in self.capacity_indices
                            if t in timesteps_by_year),'cap_changes')
            else:
                # capacity at t>1
                self.model.addConstrs((
                    self.capacity_indices[n,k,t] == \
                        self.capacity_indices[n,k,t-1] + self.capacity_change[n,k,t]
                            for n,k,t in self.capacity_indices if t>timestep_1),'cap_after_init')
                # one change per year
                self.model.addConstrs((
                    self.capacity_change[n,k,t] == 0
                        for n,k,t in self.capacity_indices if t>timestep_1),'cap_changes')


    def run(self,pprint=True,write=True):
        '''Function to solve GurobiPy model
        '''





    def debug(self,output_path='../outputs/__cache__/'):
        '''Compute model Irreducible Inconsistent Subsystem (IIS) to help deal with infeasibilies
        '''
        self.model.computeIIS()
        self.model.write(output_path+'debug_report.ilp')