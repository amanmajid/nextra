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
from .postprocess import nextra_postprocess


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

        # add costs to nodes and edges
        self = append_cost_to_network_data(self)

        # read flow data
        self.flows = read_flow_data(path_to_flows,
                                    year=kwargs.get("year", False),
                                    timesteps=kwargs.get("timesteps", False))
        
        # clean nodal names in flow file
        self.flows.node = adjust_nodal_names(self.flows.node)
        
        # handle kwargs
        self.res_factor = kwargs.get('res_factor',1)
        self.coo_factor = kwargs.get('coo_res_factor',self.global_variables['coop_res_target_2030'])
        self.ss_factor  = kwargs.get('self_sufficiency_factor',self.global_variables['self_sufficiency_factor'])
        self.__name__   = kwargs.get('model_name','nextra')
        
        if not kwargs.get('super_source',False):
            self.super_source = False
        else:
            self.super_source = True
            self.edges = add_super_source(self.nodes,self.edges)
        if not kwargs.get('super_sink',False):
            self.super_sink = False
        else:
            self.super_sink = True
            self.edges = add_super_sink(self.nodes,self.edges)
        if not kwargs.get('curtailment',True):
            self.curtailment = False
        else:
            self.curtailment = True
            self.edges = add_curtailment_sink(self.nodes,self.edges)
        
        # if not kwargs:
        #     self = manage_kwargs(self)
        # else:
        #     for key,value in kwargs.items():
        #         self = manage_kwargs(self,key,value)
        
        # adjust scenario
        flow_max = 10**9
        # current grid capacities (https://openknowledge.worldbank.org/handle/10986/28468)
        egypt_to_gaza           = 27     # MW
        jordan_to_westbank      = 100    # MW

        if self.scenario == 'BAU' or self.scenario == 'BAS':
            # Business as usual
            # Jordan ->
            self.connectivity['jordan_to_westbank']     = kwargs.get("jordan_to_westbank", flow_max)
            self.connectivity['jordan_to_israel']       = 0
            #Israel ->
            self.connectivity['israel_to_westbank']     = kwargs.get("israel_to_westbank", flow_max)
            self.connectivity['israel_to_jordan']       = 0
            self.connectivity['israel_to_gaza']         = kwargs.get("israel_to_gaza", flow_max)
            #West Bank ->
            self.connectivity['westbank_to_israel']     = 0
            self.connectivity['westbank_to_jordan']     = 0
            #Egypt ->
            self.connectivity['egypt_to_gaza']          = kwargs.get("egypt_to_gaza", egypt_to_gaza)
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
            self.connectivity['jordan_to_westbank']     = kwargs.get("jordan_to_westbank", flow_max)
            self.connectivity['jordan_to_israel']       = 0
            #Israel ->
            self.connectivity['israel_to_westbank']     = 0
            self.connectivity['israel_to_jordan']       = 0
            self.connectivity['israel_to_gaza']         = 0
            #West Bank ->
            self.connectivity['westbank_to_israel']     = 0
            self.connectivity['westbank_to_jordan']     = kwargs.get("westbank_to_jordan", flow_max)
            #Egypt ->
            self.connectivity['egypt_to_gaza']          = kwargs.get("egypt_to_gaza", egypt_to_gaza)
        elif self.scenario == 'COO' or self.scenario == 'UTO':
            # Cooperation between each state
            # --        
            # Jordan ->
            self.connectivity['jordan_to_westbank']     = kwargs.get("jordan_to_westbank", flow_max)
            self.connectivity['jordan_to_israel']       = kwargs.get("jordan_to_israel", flow_max)
            #Israel ->
            self.connectivity['israel_to_westbank']     = kwargs.get("israel_to_westbank", flow_max)
            self.connectivity['israel_to_jordan']       = kwargs.get("israel_to_jordan", flow_max)
            self.connectivity['israel_to_gaza']         = kwargs.get("israel_to_gaza", flow_max)
            #West Bank ->
            self.connectivity['westbank_to_israel']     = kwargs.get("westbank_to_israel", flow_max)
            self.connectivity['westbank_to_jordan']     = kwargs.get("westbank_to_jordan", flow_max)
            #Egypt ->
            self.connectivity['egypt_to_gaza']          = kwargs.get("egypt_to_gaza", egypt_to_gaza)

        self = update_for_scenario(self,self.connectivity)

        # define sets
        self = define_sets(self)
        
        # add time index to edge data
        self = add_time_index_to_edges(self)

        # define gurobi model
        self.model = gp.Model( create_model_name( self.__name__ ) )

        # init dir for outputs
        self.results_dir = self.global_variables['results_directory'] + self.model.ModelName
        create_dir(self.results_dir)

        # wind and solar price factors for sensitivity mode
        self.solar_price_factor = kwargs.get('solar_price_factor',1)
        self.wind_price_factor  = kwargs.get('wind_price_factor',1)


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

        # solar and wind factors
        if self.solar_price_factor != 1:
            for k in self.capex_dict.keys():
                if 'solar' in k[0]:
                    self.capex_dict[k] = self.capex_dict[k] * self.solar_price_factor

        if self.wind_price_factor != 1:
            for k in self.capex_dict.keys():
                if 'wind' in k[0]:
                    self.capex_dict[k] = self.capex_dict[k] * self.wind_price_factor


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
        
        if not self.curtailment:
            pass
        else:
            # constrain
            self.model.addConstrs(
                (self.arcFlows.sum('*','res_curtailment_sink',k,t)  >= 0
                     for t in self.timesteps
                         for k in self.commodities),'res_curtailment')
        
        
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
        

        
        #----------------------------------------------------------------------
        # ENERGY DEMAND
        #----------------------------------------------------------------------
        
        # get demand nodes
        sink_nodes = get_sink_nodes(self.nodes).name.to_list()
        # get demand dict
        demand_dict = make_demand_dict(self)

        # constrain
        self.model.addConstrs(
            (self.arcFlows.sum('*',j,'electricity',t) \
                 == demand_dict[j,t] * self.global_variables['peak_demand_factor'] \
                     for t in self.timesteps 
                         for j in sink_nodes),'energy_demand')
        
            
            
        #----------------------------------------------------------------------
        # ENERGY SUPPLY
        #----------------------------------------------------------------------
        
        #---
        # Constrain supply below capacity
        
        # get energy supply nodes
        source_nodes = get_source_nodes(self.nodes).name.to_list()
        # get rid of solar and wind
        source_nodes = [i for i in source_nodes if 'solar' not in i]
        source_nodes = [i for i in source_nodes if 'wind' not in i]
        # get supply dict
        supply_dict  = make_supply_dict(self)

        # constrain
        self.model.addConstrs(
            (self.arcFlows.sum(i,'*',k,t)  <= self.capacity_indices[i,k,t] \
                 for t in self.timesteps \
                     for k in ['electricity'] \
                         for i in source_nodes),'electricity_supply')
        
        #---
        # Baseload supplies
        
        # define function for baseload constraint
        def baseload_supply(technology,ramping_rate):
            '''Constraint supply from baseload technologies by capacity and ramp rate
            '''
            if technology in self.technologies:
                
                # index nodes by technology
                idx_nodes = get_nodes_by_technology(self.nodes,technology=technology).name.to_list()
                
                # constrain supply
                self.model.addConstrs(
                    (self.arcFlows.sum(i,'*',k,t) 
                        <= global_variables['loss_factor_seasonal'] * \
                                global_variables['loss_factor_maintenance_thermo'] * \
                                    global_variables['reserve_capacity_factor'] * \
                                        global_variables['loss_factor_transmission'] * \
                                            self.capacity_indices[i,k,t] \
                                                for t in self.timesteps \
                                                    for k in ['electricity'] \
                                                        for i in idx_nodes),technology+'_baseload')

                # constrain ramping rate
                if 'hour' in self.flows.columns:
                    # case if positive change
                    self.model.addConstrs(
                        (self.arcFlows.sum(i,'*',k,t) - \
                            self.arcFlows.sum(i,'*',k,t-1) <= ramping_rate \
                                for t in self.timesteps if t>1 \
                                    for k in ['electricity'] \
                                        for i in idx_nodes),technology+'_supply')
                    # case if negative change
                    self.model.addConstrs(
                        (self.arcFlows.sum(i,'*',k,t) - \
                            self.arcFlows.sum(i,'*',k,t-1) >= -ramping_rate \
                                for t in self.timesteps if t>1 \
                                    for k in ['electricity'] \
                                        for i in idx_nodes),technology+'_supply')

        # open-cycle gas turbine (OCGT) generation
        # baseload_supply(technology='ocgt',ramping_rate=self.global_variables['ocgt_ramping_rate'])
        # coal converted gas turbine (ccgt) generation
        baseload_supply(technology='ccgt',ramping_rate=self.global_variables['ccgt_ramping_rate'])
        # Coal generation
        baseload_supply(technology='coal',ramping_rate=self.global_variables['coal_ramping_rate'])
        # Diesel generation
        baseload_supply(technology='diesel',ramping_rate=self.global_variables['diesel_ramping_rate'])
        # Bio-gas generation
        baseload_supply(technology='biogas',ramping_rate=self.global_variables['ccgt_ramping_rate'])
        # Bio-gas generation
        baseload_supply(technology='shale',ramping_rate=self.global_variables['shale_ramping_rate'])
        # Natural gas generation
        baseload_supply(technology='natural gas',ramping_rate=self.global_variables['nat_gas_ramping_rate'])
        
        
        
        #----------------------------------------------------------------------
        # STORAGES
        #----------------------------------------------------------------------
        
        #---
        # Storage node volume must be below capacity
        storage_nodes = get_storage_nodes(self.nodes)
        storage_caps  = storage_nodes.set_index(keys=['name','commodity']).to_dict()['capacity']
        
        # constrain
        self.model.addConstrs(
            (self.storage_volume.sum(n,k,t) <= self.capacity_indices.sum(n,k,t) \
                 for n,k,t in self.storage_volume \
                     if (n,k) in storage_caps),'stor_cap_max')
    
        #---
        # Storage node balance
        storage_nodes = storage_nodes.name.to_list()
    
        # t=1
        self.model.addConstrs(
            (self.storage_volume.sum(j,k,t) == \
             0 + self.arcFlows.sum('*',j,k,t) - self.arcFlows.sum(j,'*',k,t) \
                 for k in self.commodities \
                     for t in self.timesteps if t==1 \
                         for j in storage_nodes if (j,k) in storage_caps),'storage_init')
        # t>1
        self.model.addConstrs(
            (self.storage_volume.sum(j,k,t) == \
                 self.storage_volume.sum(j,k,t-1) + self.arcFlows.sum('*',j,k,t) - self.arcFlows.sum(j,'*',k,t) \
                     for k in self.commodities \
                         for t in self.timesteps if t>1 \
                             for j in storage_nodes if (j,k) in storage_caps),'storage_balance')
        
        #---
        # Battery minimum capacity level to maintain (helps increase battery life)
        #   ---> start at t=10 to allow time for battery to charge up
        self.model.addConstrs(
            (self.storage_volume.sum(i,k,t) >= \
                 global_variables['battery_minimum_level'] * self.capacity_indices.sum(i,k,t) \
                     for k in self.commodities \
                         for t in self.timesteps if t>10 \
                             for i in storage_nodes if (i,k) in storage_caps),'bat_min_lev')
        
            
        #----------------------------------------------------------------------
        # JUNCTIONS
        #----------------------------------------------------------------------

        # get junctions
        junction_nodes = get_junction_nodes(self.nodes).name.to_list()
        
        # constrain
        self.model.addConstrs(
            (self.arcFlows.sum('*',j,k,t)  == self.arcFlows.sum(j,'*',k,t) \
                 for k in self.commodities \
                     for t in self.timesteps \
                         for j in junction_nodes),'junction_balance')
        
            
        
        #----------------------------------------------------------------------
        # GENERAL CONSTRAINTS
        #----------------------------------------------------------------------
        
        #---
        # Assign a max capacity to control the decision variable
        #---

        # # Max capacity - i.e. we can't build anything above 10,000 MW
        # self.model.addConstrs(
        #     (self.capacity_indices[n,k,t] <= self.global_variables['maximum_capacity'] \
        #          for n,k,t in self.capacity_indices),'cap_max')
        
            
        #---
        # Solar energy output
        #---
        
        # get solar nodes
        solar_nodes = get_nodes_by_technology(self.nodes, technology='solar')
        # get supply dict
        supply_dict = make_supply_dict(self)
        
        # loop through each region
        for region in adjust_nodal_names(self.nodes.territory).unique():
            # get solar asset
            solar_asset = solar_nodes[solar_nodes.name.str.contains(region)].name.to_list()
            
            # constrain
            self.model.addConstrs(
                (self.arcFlows.sum(i,'*',k,t)  \
                     == global_variables['loss_factor_transmission'] * \
                            global_variables['reserve_capacity_factor'] * \
                                global_variables['loss_factor_maintenance_res'] * \
                                    self.capacity_indices.sum(i,k,t) * supply_dict[region+'_solar',t] \
                                        for t in self.timesteps \
                                            for k in self.commodities \
                                                for i in solar_asset),'solar_supply')
        
        
        #---
        # Wind energy output
        #---
        
        # get solar nodes
        wind_nodes = get_nodes_by_technology(self.nodes, technology='wind')
        
        # loop through each region
        for region in adjust_nodal_names(self.nodes.territory).unique():
            # get solar asset
            wind_asset = wind_nodes[wind_nodes.name.str.contains(region)].name.to_list()
            
            # constrain
            self.model.addConstrs(
                (self.arcFlows.sum(i,'*',k,t)  \
                     == global_variables['loss_factor_transmission'] * \
                            global_variables['reserve_capacity_factor'] * \
                                global_variables['loss_factor_maintenance_res'] * \
                                    self.capacity_indices.sum(i,k,t) * supply_dict[region+'_wind',t] \
                                        for t in self.timesteps \
                                            for k in self.commodities \
                                                for i in wind_asset),'wind_supply')


        #---
        # Limiting curtailment
        #---

        # Expressed as a function of demand
        #   Constrained as: SUM_CURTAILMENT <= x * SUM_DEMAND
        #       where, x is a fractional quantity defined in global variables

        if not self.curtailment:
            pass
        else:
            self.model.addConstr(
                gp.quicksum(
                    # sum of curtailment
                    (self.arcFlows['gaza_solar','curtailment',k,t] \
                        + self.arcFlows['israel_solar','curtailment',k,t] \
                        + self.arcFlows['israel_wind','curtailment',k,t] \
                        + self.arcFlows['jordan_solar','curtailment',k,t] \
                        + self.arcFlows['jordan_wind','curtailment',k,t] \
                        + self.arcFlows['west_bank_solar','curtailment',k,t] \
                        + self.arcFlows['west_bank_wind','curtailment',k,t] \
                            for k in self.commodities
                                    for t in self.timesteps))
                <= \
                gp.quicksum(
                    (global_variables['maximum_curtailment'] * \
                        (self.arcFlows['gaza_generation','gaza_energy_demand',k,t] \
                            + self.arcFlows['israel_generation','gaza_energy_demand',k,t]
                            + self.arcFlows['israel_generation','israel_energy_demand',k,t]
                            + self.arcFlows['israel_generation','jordan_energy_demand',k,t]
                            + self.arcFlows['israel_generation','west_bank_energy_demand',k,t]
                            + self.arcFlows['jordan_generation','israel_energy_demand',k,t]
                            + self.arcFlows['jordan_generation','jordan_energy_demand',k,t]
                            + self.arcFlows['jordan_generation','west_bank_energy_demand',k,t]
                            + self.arcFlows['west_bank_generation','israel_energy_demand',k,t]
                            + self.arcFlows['west_bank_generation','jordan_energy_demand',k,t]
                            + self.arcFlows['west_bank_generation','west_bank_energy_demand',k,t]) \
                            for k in self.commodities
                                for t in self.timesteps)),'max_curtail')



        #---
        # Battery storage requirements
        #---
        
        battery_nodes = ['israel_battery_storage','jordan_battery_storage','gaza_battery_storage','west_bank_battery_storage']

        #---
        # Battery storage minimum capacity
        for i in ['israel','jordan','west_bank','gaza']:
            if i != 'gaza':
                self.model.addConstrs(
                    (self.capacity_indices[i + '_battery_storage',k,t] >= \
                        global_variables['battery_capacity_min_percentage'] * (self.capacity_indices[i + '_solar',k,t] + self.capacity_indices[i + '_wind',k,t]) \
                        for k in self.commodities \
                            for t in self.timesteps),'bat_min')
            else:
                self.model.addConstrs(
                    (self.capacity_indices[i + '_battery_storage',k,t] >= \
                        global_variables['battery_capacity_min_percentage'] * (self.capacity_indices[i + '_solar',k,t]) \
                        for k in self.commodities \
                            for t in self.timesteps),'bat_min')
        
        #---
        # Battery storage maximum capacity
        for i in ['israel','jordan','west_bank','gaza']:
            if i != 'gaza':
                self.model.addConstrs(
                    (self.capacity_indices[i + '_battery_storage',k,t] <= \
                        global_variables['battery_capacity_max_percentage'] * (self.capacity_indices[i + '_solar',k,t] + self.capacity_indices[i + '_wind',k,t]) \
                        for k in self.commodities \
                            for t in self.timesteps),'bat_min')
            else:
                self.model.addConstrs(
                    (self.capacity_indices[i + '_battery_storage',k,t] <= \
                        global_variables['battery_capacity_max_percentage'] * (self.capacity_indices[i + '_solar',k,t]) \
                        for k in self.commodities \
                            for t in self.timesteps),'bat_min')

        #---
        # Battery inflow cannot exceed capacity
        self.model.addConstrs( \
            (self.arcFlows.sum('*',j,k,t) <= self.capacity_indices.sum(j,k,t) \
                for k in self.commodities \
                    for t in self.timesteps
                        for j in battery_nodes),'stor_inflow') 

        #---
        # Battery outflow cannot exceed capacity
        self.model.addConstrs( \
            (self.arcFlows.sum(i,'*',k,t) <= self.capacity_indices.sum(i,k,t) \
                for k in self.commodities \
                    for t in self.timesteps
                        for i in battery_nodes),'stor_outflow') 

        #---
        # Battery dynamics
        #---

        charging_timesteps      = self.flows.loc[self.flows.hour.isin(global_variables['battery_charge_hours'])].timestep.to_list()
        discharging_timesteps   = self.flows.loc[~self.flows.hour.isin(global_variables['battery_charge_hours'])].timestep.to_list()

        # Set maximum charging rate
        self.model.addConstrs(
            (self.arcFlows[i,j,k,t] <= self.global_variables['battery_charge_rate']
                 for i,j,k,t in self.arcFlows \
                     if 'battery' in i),'battery_charge_rate')

         # Set maximum discharging rate
        self.model.addConstrs(
            (self.arcFlows[i,j,k,t] <= self.global_variables['battery_discharge_rate']
                 for i,j,k,t in self.arcFlows \
                     if 'battery' in j),'battery_discharge_rate')

        # battery charging window
        self.model.addConstrs(
            (self.arcFlows.sum(i,'*',k,t) == 0 \
                for i in battery_nodes \
                    for k in ['electricity'] \
                        for t in charging_timesteps),'bat_chg')
        
        # battery discharging window
        self.model.addConstrs(
            (self.arcFlows.sum('*',j,k,t) == 0 \
                for j in battery_nodes \
                    for k in ['electricity'] \
                        for t in self.timesteps if t not in charging_timesteps),'bat_dischg')

        
        #---
        # Egyptian export to Gaza
        #---

        self.model.addConstrs(
            (self.arcFlows.sum(i,j,k,t) <= self.global_variables['egypt_to_gaza_export'] \
                for i in ['egypt_generation'] \
                    for j in ['gaza_energy_demand'] \
                        for k in self.commodities \
                            for t in self.timesteps),'egypt_import')
        
            
        #---
        # Israel's baseload output
        #---

        # Coal output must always be half of total capacity
        self.model.addConstrs(
            (self.arcFlows.sum(i,'*',k,t)  \
                >= self.global_variables['isr_min_coal_output'] * self.capacity_indices.sum(i,k,t) \
                    for i in ['israel_coal'] \
                        for k in ['electricity'] \
                            for t in self.timesteps),'isr_coal_base')

        # CCGT output must always be half of total capacity
        self.model.addConstrs(
            (self.arcFlows.sum(i,'*',k,t)  \
                 >= self.global_variables['isr_min_gas_output'] * self.capacity_indices.sum(i,k,t)\
                     for i in ['israel_ccgt'] \
                         for k in ['electricity']\
                             for t in self.timesteps),'isr_ng_base')
        
        
        #---
        # Jordan's baseload output
        #---
        
        # Shale output as a percentage of capacity
        self.model.addConstrs(
            (self.arcFlows.sum(i,'*',k,t)  \
                >= self.global_variables['jor_min_shale_output'] * self.capacity_indices.sum(i,k,t)\
                    for i in ['jordan_shale'] \
                        for k in ['electricity'] \
                            for t in self.timesteps),'shale_base')
        
        # Natural gas as a percentage of capacity
        self.model.addConstrs(
            (self.arcFlows.sum(i,'*',k,t)  \
                >= self.global_variables['jor_min_gas_output'] * self.capacity_indices.sum(i,k,t)\
                    for i in ['jordan_natural_gas']\
                        for k in ['electricity']\
                            for t in self.timesteps),'ng_base')
        

        #---
        # Palestine's baseload output
        #---
        
        # West Bank - Natural gas output must be at least half of capacity
        self.model.addConstrs(
            (self.arcFlows.sum(i,'*',k,t)  \
                >= self.global_variables['jor_min_gas_output'] * self.capacity_indices.sum(i,k,t)\
                    for i in ['west_bank_natural_gas']\
                        for k in ['electricity']\
                            for t in self.timesteps),'ng_base')
        
        # Gaza - Natural gas output must be at least half of capacity
        self.model.addConstrs(
            (self.arcFlows.sum(i,'*',k,t)  \
                >= self.global_variables['jor_min_gas_output'] * self.capacity_indices.sum(i,k,t)\
                    for i in ['gaza_natural_gas']\
                        for k in ['electricity']\
                            for t in self.timesteps),'ng_base')
        

        #---
        # Prevent renewable deconstruction 
        #---
        renewable_assets = ['israel_solar','israel_wind',
                            'west_bank_solar','west_bank_wind',
                            'jordan_solar','jordan_wind',
                            'gaza_solar',#'gaza_wind'
                            ]
        # constr
        self.model.addConstrs(
            (self.capacity_indices[n,k,t] >= self.nodes.loc[self.nodes.name==n,'capacity'].values[0]\
                 for n in renewable_assets \
                     for k in ['electricity'] \
                         for t in self.timesteps),'res_decom')

            
        #----------------------------------------------------------------------
        # TARGETS FOR 2030
        #----------------------------------------------------------------------
        
        timesteps_2030 = get_timesteps_by_year(self, year=2030)
        
        #---
        # Emissions reductions
        #---

        # 
        emission_reduction = \
                (1-global_variables['emissions_reduction_2030']) * (global_variables['BAS_emissions_in_2030']/(24*365)) * len(self.timesteps) * 10**6
                #0.7 * 61343/(24*365) * len(self.timesteps) * 10**6 >= \

        if self.scenario != 'BAS':
            # constr 
            self.model.addConstr( \
                emission_reduction >= \
                    gp.quicksum( \
                        # diesel
                        (co2['Diesel'] * \
                            (self.arcFlows['israel_diesel','israel_generation',k,t] \
                                + self.arcFlows['jordan_diesel','jordan_generation',k,t] \
                                + self.arcFlows['west_bank_diesel','west_bank_generation',k,t]
                                + self.arcFlows['gaza_diesel','gaza_generation',k,t])) \
                        # gas
                        + (co2['Gas'] * \
                            (self.arcFlows['israel_natural_gas','israel_gas_storage',k,t] \
                                + self.arcFlows['jordan_natural_gas','jordan_generation',k,t] \
                                + self.arcFlows['gaza_natural_gas','gaza_generation',k,t] \
                                + self.arcFlows['west_bank_natural_gas','west_bank_generation',k,t]))
                        # ccgt
                        + (co2['Gas'] * \
                            (self.arcFlows['israel_ccgt','israel_generation',k,t] \
                                + self.arcFlows['jordan_ccgt','jordan_generation',k,t] \
                                + self.arcFlows['west_bank_ccgt','west_bank_generation',k,t]))
                        # coal
                        + (co2['Coal'] * \
                            (self.arcFlows['israel_coal','israel_generation',k,t] \
                                + self.arcFlows['jordan_coal','jordan_generation',k,t] \
                                + self.arcFlows['west_bank_coal','west_bank_generation',k,t]))
                        # shale
                        + (co2['Shale'] * \
                            (self.arcFlows['jordan_shale','jordan_generation',k,t]))
                        for k in ['electricity']
                            for t in self.timesteps if t in timesteps_2030),'emission_reduction')


        #---
        # Israel's energy targets
        #---

        # No high carbon energy technologies in 2030
        high_carbon_techs   = ['israel_coal', 'israel_diesel']
        self.model.addConstrs(
            (self.capacity_indices[n,k,t] == 0\
                 for n,k,t in self.capacity_indices \
                     if t in timesteps_2030 and n in high_carbon_techs),'isr_carb1')

        # There can only be a maximum of 700 MW of wind capacity due to land constraints
        self.model.addConstrs(
            (self.capacity_indices[n,k,t] <= self.global_variables['isr_max_wind_cap']\
                 for n in ['israel_wind']\
                     for k in ['electricity']\
                         for t in self.timesteps),'isr_wind')

        # Additional capacity of carbon-intensive technologies cannot be built
        high_carbon_techs = ['israel_coal', 'israel_diesel']
        self.model.addConstrs(
            (self.capacity_indices[n,k,t] <= self.capacity_indices[n,k,t-1]\
                 for n,k,t in self.capacity_indices\
                     if t>1 and n in high_carbon_techs),'isr_carb2')

        # There must be a minimum amount of natural gas
        self.model.addConstrs(
            (self.capacity_indices[n,k,t] >= self.nodes.loc[self.nodes.name==n,'capacity'].values[0]\
                 for n in ['israel_natural_gas']\
                     for k in ['electricity']\
                         for t in self.timesteps),'isr_ng')

        # There must be 3400 MW of ccgt
        self.model.addConstrs(
            (self.capacity_indices[n,k,t] == self.global_variables['isr_max_ccgt_cap']\
                 for n in ['israel_ccgt']\
                     for k in ['electricity']\
                         for t in self.timesteps\
                             if t in timesteps_2030),'isr_ccgt')
        
        # Israel's storage targets
        #   >>> zero out gas storages
        self.model.addConstrs(
            (self.capacity_indices[n,k,t] == 0\
                 for n in ['israel_gas_storage']\
                     for k in ['electricity']\
                         for t in self.timesteps\
                             if t in timesteps_2030),'isr_storage')
        
            
        #---
        # Jordan's energy targets
        #---

        # No high carbon energy technologies in 2030
        high_carbon_techs   = ['jordan_coal', 'jordan_diesel', 'jordan_ccgt']
        self.model.addConstrs(
            (self.capacity_indices[n,k,t] == 0\
                 for n,k,t in self.capacity_indices\
                     if t in timesteps_2030 and n in high_carbon_techs),'jor_carbon')

        # jordan_solar should be more than baseline
        self.model.addConstrs(
            (self.capacity_indices[n,k,t] >= self.nodes.loc[self.nodes.name==n,'capacity'].values[0]\
                 for n in ['jordan_solar']\
                     for k in ['electricity']\
                         for t in self.timesteps),'jor_sol1')

        # jordan_natural_gas should be more than baseline
        self.model.addConstrs(
            (self.capacity_indices[n,k,t] >= self.nodes.loc[self.nodes.name==n,'capacity'].values[0]\
                 for n in ['jordan_natural_gas']\
                     for k in ['electricity']\
                         for t in self.timesteps),'jor_sol2')
        
        
        #---
        # West Bank's energy targets
        #---

        # Wind in West Bank
        self.model.addConstrs(
            (self.capacity_indices[n,k,t] == 50\
                 for n in ['west_bank_wind']\
                     for k in ['electricity']\
                         for t in timesteps_2030),'wb_wind')
        
        # Baseload technologies in West Bank (#,'west_bank_natural_gas')
        self.model.addConstrs(
            (self.capacity_indices[n,k,t] == 0\
                 for n in ['west_bank_coal','west_bank_ccgt','west_bank_diesel']\
                     for k in ['electricity']\
                         for t in timesteps_2030),'wb_baseload')


        #---
        # Gaza's energy targets
        #---

        # gaza_diesel is 0 MW due to plans to convert existing plant to gas
        self.model.addConstrs(
            (self.capacity_indices[n,k,t] == 0\
                 for n in ['gaza_diesel']\
                     for k in ['electricity']\
                         for t in timesteps_2030),'gaza_diesel')
        
        # # Solar in Gaza
        self.model.addConstrs(
            (self.capacity_indices[n,k,t] >= 0\
                 for n in ['gaza_solar']\
                     for k in ['electricity']\
                         for t in timesteps_2030),'gaza_solar')
        
        # Natural gas in Gaza at least capacity of diesel today (due to plans to convert existing plant to gas)
        self.model.addConstrs(
            (self.capacity_indices[n,k,t] >= self.global_variables['gaz_diesel_cap']\
                 for n in ['gaza_natural_gas']\
                     for k in ['electricity']\
                         for t in timesteps_2030),'gaza_ng')
        

        #---
        # CAPACITY RATIOS
        #---
        
        # # Jordan wind ratio
        # self.model.addConstrs(
        #     (self.capacity_indices['jordan_solar',k,t] * 0.2 >= self.capacity_indices['jordan_wind',k,t]\
        #         for k in ['electricity']\
        #             for t in self.timesteps),'jor_wind')
        
        # # Israel wind ratio
        # self.model.addConstrs(
        #     (self.capacity_indices['israel_solar',k,t] * 0.05 >= self.capacity_indices['israel_wind',k,t]\
        #         for k in ['electricity']\
        #             for t in self.timesteps),'isr_wind_ratio')
            

        #----------------------------------------------------------------------
        # ENERGY GOALS
        #----------------------------------------------------------------------
        
        # The following constraints are only implemented if the
        #   energy_objectives parameter is True. This is activated by default.
        
        if self.energy_objective is True:
            
            #========================================
            # BUSINESS AS USUAL
            #========================================
            
            if self.scenario == 'BAU':
            
                #-----
                # ISRAEL
                #-----
        
                # [1] RES
                self.model.addConstr( \
                    gp.quicksum( \
                        self.global_variables['isr_res_target_2030'] * self.res_factor * \
                            (self.arcFlows['israel_generation','israel_energy_demand',k,t] \
                                + self.arcFlows['israel_generation','west_bank_energy_demand',k,t] \
                                + self.arcFlows['israel_generation','gaza_energy_demand',k,t])
                                    for k in ['electricity']
                                            for t in self.timesteps if t in timesteps_2030) \
                    <= \
                    gp.quicksum( \
                        (self.arcFlows['israel_solar','israel_generation',k,t] \
                            + self.arcFlows['israel_wind','israel_generation',k,t] \
                                + self.arcFlows['israel_solar','israel_battery_storage',k,t] \
                                    + self.arcFlows['israel_wind','israel_battery_storage',k,t]) \
                                        for k in ['electricity']
                                            for t in self.timesteps if t in timesteps_2030),'isr_res')
                
                # [2] NATURAL GAS
                self.model.addConstr( \
                    gp.quicksum( \
                        self.global_variables['isr_ng_target_2030'] *  \
                            (self.arcFlows['israel_generation','israel_energy_demand',k,t] \
                            + self.arcFlows['israel_generation','west_bank_energy_demand',k,t] \
                            + self.arcFlows['israel_generation','gaza_energy_demand',k,t])
                                for k in ['electricity']
                                        for t in self.timesteps if t in timesteps_2030) \
                    <= \
                    gp.quicksum( \
                        (self.arcFlows['israel_natural_gas','israel_gas_storage',k,t] \
                            + self.arcFlows['israel_ccgt','israel_generation',k,t])
                                for k in ['electricity']
                                    for t in self.timesteps if t in timesteps_2030),'isr_ng')
            
                #-----
                # JORDAN
                #-----
        
                # [1] RES
                self.model.addConstr( \
                    gp.quicksum( \
                        self.global_variables['jor_res_target_2030'] * self.res_factor * \
                            (self.arcFlows['jordan_generation','jordan_energy_demand',k,t] \
                                + self.arcFlows['jordan_generation','west_bank_energy_demand',k,t] \
                                    + self.arcFlows['jordan_generation','israel_energy_demand',k,t])
                                        for k in ['electricity']
                                            for t in self.timesteps if t in timesteps_2030) \
                    <= \
                    gp.quicksum( \
                        (self.arcFlows['jordan_solar','jordan_generation',k,t] \
                            + self.arcFlows['jordan_wind','jordan_generation',k,t] \
                                + self.arcFlows['jordan_solar','jordan_battery_storage',k,t] \
                                    + self.arcFlows['jordan_wind','jordan_battery_storage',k,t]) \
                                        for k in ['electricity']
                                            for t in self.timesteps if t in timesteps_2030),'jor_res')
                
                # [2] NATURAL GAS
                self.model.addConstr( \
                    gp.quicksum( \
                        self.global_variables['jor_ng_target_2030'] * \
                            (self.arcFlows['jordan_generation','jordan_energy_demand',k,t] \
                                + self.arcFlows['jordan_generation','west_bank_energy_demand',k,t] \
                                + self.arcFlows['jordan_generation','israel_energy_demand',k,t])
                                    for k in ['electricity']
                                        for t in self.timesteps if t in timesteps_2030) \
                    <= \
                    gp.quicksum( \
                        (self.arcFlows['jordan_natural_gas','jordan_generation',k,t])
                            for k in ['electricity']
                                for t in self.timesteps if t in timesteps_2030),'jor_ng')
        
                # [3] SHALE OIL
                self.model.addConstr( \
                    gp.quicksum( \
                        self.global_variables['jor_shale_target_2030'] * \
                            (self.arcFlows['jordan_generation','jordan_energy_demand',k,t] \
                                + self.arcFlows['jordan_generation','west_bank_energy_demand',k,t] \
                                + self.arcFlows['jordan_generation','israel_energy_demand',k,t])
                                    for k in ['electricity']
                                        for t in self.timesteps if t in timesteps_2030) \
                    <= \
                    gp.quicksum( \
                        (self.arcFlows['jordan_shale','jordan_generation',k,t])
                            for k in ['electricity']
                                for t in self.timesteps if t in timesteps_2030),'jor_shale')
    
    
                #-----
                # WEST BANK
                #-----
        
                # [1] RES
                # <<<<< Does not apply >>>>>

                # [2] NO CAPACITY ADDITIONS ALLOWED UNDER BAU
                unexpandable = ['west_bank_natural_gas']
                self.model.addConstrs(
                    (self.capacity_indices[n,k,t] == 0\
                        for n in unexpandable\
                            for k in ['electricity']\
                                for t in self.timesteps),'wb_gas_change')
        
        
                #-----
                # GAZA
                #-----
        
                # [1] RES
                # <<<<< Does not apply >>>>>

                # # [2] NO CAPACITY ADDITIONS ALLOWED UNDER BAU
                # unexpandable = ['gaza_natural_gas']
                # self.model.addConstrs(
                #     (self.capacity_indices[n,k,t] == 0\
                #         for n in unexpandable\
                #             for k in ['electricity']\
                #                 for t in self.timesteps),'gz_gas_change')
            
            
            #========================================
            # NON-COOPERATIVE
            #========================================
            
            if self.scenario == 'NCO':
                            
                #-----
                # ISRAEL
                #-----
        
                # [1] RES
                self.model.addConstr( \
                    gp.quicksum( \
                        self.global_variables['isr_res_target_2030'] * self.res_factor * \
                            (self.arcFlows['israel_generation','israel_energy_demand',k,t])
                                    for k in ['electricity']
                                            for t in self.timesteps if t in timesteps_2030) \
                    <= \
                    gp.quicksum( \
                        (self.arcFlows['israel_solar','israel_generation',k,t] \
                            + self.arcFlows['israel_wind','israel_generation',k,t] \
                                + self.arcFlows['israel_solar','israel_battery_storage',k,t] \
                                    + self.arcFlows['israel_wind','israel_battery_storage',k,t]) \
                                        for k in ['electricity']
                                            for t in self.timesteps if t in timesteps_2030),'isr_res')
                
                # [2] NATURAL GAS
                self.model.addConstr( \
                    gp.quicksum( \
                        self.global_variables['isr_ng_target_2030'] *  \
                            (self.arcFlows['israel_generation','israel_energy_demand',k,t])
                                for k in ['electricity']
                                        for t in self.timesteps if t in timesteps_2030) \
                    <= \
                    gp.quicksum( \
                        (self.arcFlows['israel_natural_gas','israel_gas_storage',k,t] \
                            + self.arcFlows['israel_ccgt','israel_generation',k,t])
                                for k in ['electricity']
                                    for t in self.timesteps if t in timesteps_2030),'isr_ng')
                
                
                #-----
                # JORDAN
                #-----
        
                # [1] RES
                self.model.addConstr( \
                    gp.quicksum( \
                        self.global_variables['jor_res_target_2030'] * self.res_factor * \
                            (self.arcFlows['jordan_generation','jordan_energy_demand',k,t])
                                for k in ['electricity']
                                    for t in self.timesteps if t in timesteps_2030) \
                    <= \
                    gp.quicksum( \
                        (self.arcFlows['jordan_solar','jordan_generation',k,t] \
                            + self.arcFlows['jordan_wind','jordan_generation',k,t] \
                                + self.arcFlows['jordan_solar','jordan_battery_storage',k,t] \
                                    + self.arcFlows['jordan_wind','jordan_battery_storage',k,t]) \
                                        for k in ['electricity']
                                            for t in self.timesteps if t in timesteps_2030),'jor_res')
                
                # [2] NATURAL GAS
                self.model.addConstr( \
                    gp.quicksum( \
                        self.global_variables['jor_ng_target_2030'] * \
                            (self.arcFlows['jordan_generation','jordan_energy_demand',k,t])
                                    for k in ['electricity']
                                        for t in self.timesteps if t in timesteps_2030) \
                    <= \
                    gp.quicksum( \
                        (self.arcFlows['jordan_natural_gas','jordan_generation',k,t])
                            for k in ['electricity']
                                for t in self.timesteps if t in timesteps_2030),'jor_ng')
        
                # [3] SHALE OIL
                self.model.addConstr( \
                    gp.quicksum( \
                        self.global_variables['jor_shale_target_2030'] * \
                            (self.arcFlows['jordan_generation','jordan_energy_demand',k,t] )
                                    for k in ['electricity']
                                        for t in self.timesteps if t in timesteps_2030) \
                    <= \
                    gp.quicksum( \
                        (self.arcFlows['jordan_shale','jordan_generation',k,t])
                            for k in ['electricity']
                                for t in self.timesteps if t in timesteps_2030),'jor_shale')
                
                
                #-----
                # WEST BANK
                #-----
        
                # [1] RES
                self.model.addConstr( \
                    gp.quicksum( \
                        self.global_variables['pal_res_target_2030'] * self.res_factor * \
                            (self.arcFlows['west_bank_generation','west_bank_energy_demand',k,t])
                                    for k in ['electricity']
                                        for t in self.timesteps if t in timesteps_2030) \
                    <= \
                    gp.quicksum( \
                        (self.arcFlows['west_bank_solar','west_bank_generation',k,t] \
                            + self.arcFlows['west_bank_wind','west_bank_generation',k,t] \
                                + self.arcFlows['west_bank_solar','west_bank_battery_storage',k,t] \
                                    + self.arcFlows['west_bank_wind','west_bank_battery_storage',k,t])
                                        for k in ['electricity']
                                            for t in self.timesteps if t in timesteps_2030),'wb_res')
                
                # [2] SELF-SUFFICIENCY
                # <<<<< Does not apply >>>>>
                
                
                #-----
                # GAZA
                #-----
        
                # [1] RES (no wind in gaza)
                self.model.addConstr( \
                    gp.quicksum( \
                        self.global_variables['gaz_res_target_2030'] * self.res_factor * \
                            (self.arcFlows['gaza_generation','gaza_energy_demand',k,t])
                                    for k in ['electricity']
                                        for t in self.timesteps if t in timesteps_2030) \
                    <= \
                    gp.quicksum( \
                        (self.arcFlows['gaza_solar','gaza_generation',k,t] \
                            + self.arcFlows['gaza_solar','gaza_battery_storage',k,t])
                                for k in ['electricity']
                                    for t in self.timesteps if t in timesteps_2030),'gaza_res')
                
                # [2] SELF-SUFFICIENCY
                # <<<<< Does not apply >>>>>
            
            
            #========================================
            # EXTENDED ARAB GRID
            #========================================
            
            if self.scenario == 'EAG':
            
                #-----
                # ISRAEL
                #-----

                # [1] RES
                self.model.addConstr( \
                    gp.quicksum( \
                        self.global_variables['isr_res_target_2030'] * self.res_factor * \
                            (self.arcFlows['israel_generation','israel_energy_demand',k,t])
                                    for k in ['electricity']
                                            for t in self.timesteps if t in timesteps_2030) \
                    <= \
                    gp.quicksum( \
                        (self.arcFlows['israel_solar','israel_generation',k,t] \
                            + self.arcFlows['israel_wind','israel_generation',k,t] \
                                + self.arcFlows['israel_solar','israel_battery_storage',k,t] \
                                    + self.arcFlows['israel_wind','israel_battery_storage',k,t]) \
                                        for k in ['electricity']
                                            for t in self.timesteps if t in timesteps_2030),'isr_res')
                
                # [2] NATURAL GAS
                self.model.addConstr( \
                    gp.quicksum( \
                        self.global_variables['isr_ng_target_2030'] *  \
                            (self.arcFlows['israel_generation','israel_energy_demand',k,t])
                                for k in ['electricity']
                                        for t in self.timesteps if t in timesteps_2030) \
                    <= \
                    gp.quicksum( \
                        (self.arcFlows['israel_natural_gas','israel_gas_storage',k,t] \
                            + self.arcFlows['israel_ccgt','israel_generation',k,t])
                                for k in ['electricity']
                                    for t in self.timesteps if t in timesteps_2030),'isr_ng')
                
                
                #-----
                # JORDAN
                #-----
        
                # [1] RES
                # <<<<< Does not apply >>>>>
                
                # [2] NATURAL GAS
                self.model.addConstr( \
                    gp.quicksum( \
                        self.global_variables['jor_ng_target_2030'] * \
                            (self.arcFlows['jordan_generation','jordan_energy_demand',k,t])
                                    for k in ['electricity']
                                        for t in self.timesteps if t in timesteps_2030) \
                    <= \
                    gp.quicksum( \
                        (self.arcFlows['jordan_natural_gas','jordan_generation',k,t])
                            for k in ['electricity']
                                for t in self.timesteps if t in timesteps_2030),'jor_ng')
        
                # [3] SHALE OIL
                self.model.addConstr( \
                    gp.quicksum( \
                        self.global_variables['jor_shale_target_2030'] * \
                            (self.arcFlows['jordan_generation','jordan_energy_demand',k,t] )
                                    for k in ['electricity']
                                        for t in self.timesteps if t in timesteps_2030) \
                    <= \
                    gp.quicksum( \
                        (self.arcFlows['jordan_shale','jordan_generation',k,t])
                            for k in ['electricity']
                                for t in self.timesteps if t in timesteps_2030),'jor_shale')
                
                
                #-----
                # WEST BANK
                #-----
        
                # [1] RES
                # <<<<< Does not apply >>>>>
                
                # [2] SELF-SUFFICIENCY
                self.model.addConstr(
                    gp.quicksum( \
                        self.ss_factor * \
                            # sum of total demand
                            (self.arcFlows['west_bank_generation',j,k,t] \
                                + self.arcFlows['israel_generation',j,k,t] \
                                    + self.arcFlows['jordan_generation',j,k,t])
                                        for j in ['west_bank_energy_demand']
                                            for k in ['electricity']
                                                for t in self.timesteps if t in timesteps_2030)
                    == \
                    gp.quicksum( \
                        (self.arcFlows['west_bank_generation','west_bank_energy_demand',k,t])
                            for k in ['electricity']
                                for t in self.timesteps if t in timesteps_2030),'wb_ss')
                
                # [3] CAPACITY ADDITIONS IN WEST BANK UNDER EAG
                unexpandable = ['west_bank_natural_gas']
                self.model.addConstrs(
                    (self.capacity_indices[n,k,t] == 0\
                        for n in unexpandable\
                            for k in ['electricity']\
                                for t in self.timesteps),'wb_gas_change')

                self.model.addConstrs(
                    (self.capacity_indices['west_bank_solar',k,t] <= 1500 \
                        for n in unexpandable\
                            for k in ['electricity']\
                                for t in self.timesteps),'wb_solar_chg')
                
                #-----
                # GAZA
                #-----
    
                # [1] RES (hard coded as with NCO scenario)
                self.model.addConstrs(
                    (self.capacity_indices[n,k,t] == 2535\
                        for n in ['gaza_solar']\
                            for k in ['electricity']\
                                for t in self.timesteps),'gaza_sol_hard')

                self.model.addConstrs(
                    (self.capacity_indices[n,k,t] == 2028\
                        for n in ['gaza_battery_storage']\
                            for k in ['electricity']\
                                for t in self.timesteps),'gaza_sol_hard')

                # self.model.addConstr( \
                #     gp.quicksum( \
                #         self.global_variables['gaz_res_target_2030'] * self.res_factor * \
                #             (self.arcFlows['gaza_generation','gaza_energy_demand',k,t])
                #                     for k in ['electricity']
                #                         for t in self.timesteps if t in timesteps_2030) \
                #     <= \
                #     gp.quicksum( \
                #         (self.arcFlows['gaza_solar','gaza_generation',k,t] \
                #             + self.arcFlows['gaza_solar','gaza_battery_storage',k,t])
                #                 for k in ['electricity']
                #                     for t in self.timesteps if t in timesteps_2030),'gaza_res')
            
                # [2] SELF-SUFFICIENCY
                self.model.addConstr(
                    gp.quicksum( \
                        self.ss_factor * \
                            # sum of total demand
                            (self.arcFlows['gaza_generation',j,k,t] \
                                + self.arcFlows['israel_generation',j,k,t] \
                                    + self.arcFlows['egypt_generation',j,k,t])
                                        for j in ['gaza_energy_demand']
                                            for k in ['electricity']
                                                for t in self.timesteps if t in timesteps_2030) \
                    == \
                    gp.quicksum( \
                        (self.arcFlows['gaza_generation','gaza_energy_demand',k,t])
                            for k in ['electricity']
                                for t in self.timesteps if t in timesteps_2030),'gaz_ss')

                #-----
                # JORDAN AND PALESTINE INTEGRATED RES TARGET
                #-----
                
                self.model.addConstr( \
                    gp.quicksum( \
                        self.global_variables['eag_res_target_2030'] * self.res_factor * \
                            (self.arcFlows['jordan_generation','jordan_energy_demand',k,t] \
                                + self.arcFlows['jordan_generation','west_bank_energy_demand',k,t] \
                                    + self.arcFlows['west_bank_generation','west_bank_energy_demand',k,t]\
                                        + self.arcFlows['gaza_generation','gaza_energy_demand',k,t])
                                            for k in ['electricity']
                                                    for t in self.timesteps if t in timesteps_2030) \
                    <= \
                    gp.quicksum( \
                        ( # jordan
                        self.arcFlows['jordan_solar','jordan_generation',k,t] \
                            + self.arcFlows['jordan_wind','jordan_generation',k,t] \
                                + self.arcFlows['jordan_solar','jordan_battery_storage',k,t] \
                                    + self.arcFlows['jordan_wind','jordan_battery_storage',k,t] \
                                    # west bank
                                    + self.arcFlows['west_bank_solar','west_bank_generation',k,t] \
                                        + self.arcFlows['west_bank_wind','west_bank_generation',k,t] \
                                            + self.arcFlows['west_bank_solar','west_bank_battery_storage',k,t] \
                                                + self.arcFlows['west_bank_wind','west_bank_battery_storage',k,t] \
                                                    # gaza
                                                    + self.arcFlows['gaza_solar','gaza_generation',k,t]
                                                        + self.arcFlows['gaza_solar','gaza_battery_storage',k,t])
                                                            for k in ['electricity']
                                                                for t in self.timesteps if t in timesteps_2030),'eag_res')
            
            
            #========================================
            # COOPERATIVE AND UTOPIA
            #========================================
            
            if self.scenario == 'COO' or self.scenario == 'UTO':
                # [1] COMBINED RES TARGET
                self.model.addConstr( \
                    gp.quicksum( \
                        #variables['coop_res_target_2030'] * self.res_factor * \
                            self.coo_factor * \
                            # israel
                            (self.arcFlows['israel_solar','israel_generation',k,t] \
                                + self.arcFlows['israel_wind','israel_generation',k,t] \
                                + self.arcFlows['israel_solar','israel_battery_storage',k,t] \
                                + self.arcFlows['israel_wind','israel_battery_storage',k,t] \
                                + self.arcFlows['israel_diesel','israel_generation',k,t] \
                                + self.arcFlows['israel_coal','israel_generation',k,t] \
                                + self.arcFlows['israel_ccgt','israel_generation',k,t] \
                                + self.arcFlows['israel_natural_gas','israel_gas_storage',k,t] \
                                # jordan
                                + self.arcFlows['jordan_solar','jordan_generation',k,t] \
                                + self.arcFlows['jordan_wind','jordan_generation',k,t] \
                                + self.arcFlows['jordan_solar','jordan_battery_storage',k,t] \
                                + self.arcFlows['jordan_wind','jordan_battery_storage',k,t] \
                                + self.arcFlows['jordan_natural_gas','jordan_generation',k,t] \
                                + self.arcFlows['jordan_diesel','jordan_generation',k,t] \
                                + self.arcFlows['jordan_coal','jordan_generation',k,t] \
                                + self.arcFlows['jordan_ccgt','jordan_generation',k,t] \
                                + self.arcFlows['jordan_shale','jordan_generation',k,t] \
                                # west bank
                                + self.arcFlows['west_bank_solar','west_bank_generation',k,t] \
                                + self.arcFlows['west_bank_wind','west_bank_generation',k,t] \
                                + self.arcFlows['west_bank_solar','west_bank_battery_storage',k,t] \
                                + self.arcFlows['west_bank_wind','west_bank_battery_storage',k,t] \
                                + self.arcFlows['west_bank_coal','west_bank_generation',k,t] \
                                + self.arcFlows['west_bank_ccgt','west_bank_generation',k,t] \
                                + self.arcFlows['west_bank_natural_gas','west_bank_generation',k,t] \
                                + self.arcFlows['west_bank_diesel','west_bank_generation',k,t] \
                                # gaza
                                + self.arcFlows['gaza_diesel','gaza_generation',k,t] \
                                + self.arcFlows['gaza_solar','gaza_generation',k,t] \
                                + self.arcFlows['gaza_solar','gaza_battery_storage',k,t] \
                                + self.arcFlows['gaza_natural_gas','gaza_generation',k,t] \
                                + self.arcFlows['egypt_generation','gaza_energy_demand',k,t])
                                    for k in ['electricity']
                                            for t in self.timesteps if t in timesteps_2030) \
                    <= \
                    gp.quicksum( \
                        # israel
                        (self.arcFlows['israel_solar','israel_generation',k,t] \
                            + self.arcFlows['israel_wind','israel_generation',k,t] \
                            + self.arcFlows['israel_solar','israel_battery_storage',k,t] \
                            + self.arcFlows['israel_wind','israel_battery_storage',k,t] \
                            # jordan
                            + self.arcFlows['jordan_solar','jordan_generation',k,t] \
                            + self.arcFlows['jordan_wind','jordan_generation',k,t] \
                            + self.arcFlows['jordan_solar','jordan_battery_storage',k,t] \
                            + self.arcFlows['jordan_wind','jordan_battery_storage',k,t] \
                            # west bank
                            + self.arcFlows['west_bank_solar','west_bank_generation',k,t] \
                            + self.arcFlows['west_bank_wind','west_bank_generation',k,t] \
                            + self.arcFlows['west_bank_solar','west_bank_battery_storage',k,t] \
                            + self.arcFlows['west_bank_wind','west_bank_battery_storage',k,t] \
                            # gaza
                            + self.arcFlows['gaza_solar','gaza_generation',k,t] \
                            + self.arcFlows['gaza_solar','gaza_battery_storage',k,t])
                                for k in ['electricity']
                                    for t in self.timesteps if t in timesteps_2030),'coo_res')
            
            
                #-----
                # ISRAEL
                #-----
        
                # [1] RES
                # <<<<< Does not apply >>>>>
                
                # [2] NATURAL GAS
                self.model.addConstr( \
                    gp.quicksum( \
                        self.global_variables['isr_ng_target_2030'] *  \
                            (self.arcFlows['israel_solar','israel_generation',k,t] \
                                + self.arcFlows['israel_wind','israel_generation',k,t] \
                                + self.arcFlows['israel_battery_storage','israel_generation',k,t] \
                                + self.arcFlows['israel_diesel','israel_generation',k,t] \
                                + self.arcFlows['israel_coal','israel_generation',k,t] \
                                + self.arcFlows['israel_ccgt','israel_generation',k,t] \
                                + self.arcFlows['israel_natural_gas','israel_gas_storage',k,t])
                                    for k in ['electricity']
                                            for t in self.timesteps if t in timesteps_2030) \
                    <= \
                    gp.quicksum( \
                        (self.arcFlows['israel_natural_gas','israel_gas_storage',k,t] \
                            + self.arcFlows['israel_ccgt','israel_generation',k,t])
                                for k in ['electricity']
                                    for t in self.timesteps if t in timesteps_2030),'isr_ng')
                

                #-----
                # JORDAN
                #-----

                # ZERO SHALE IN JORDAN UNDER COO/UTO
                self.model.addConstrs(
                    (self.capacity_indices[n,k,t] == 0\
                        for n in ['jordan_shale']\
                            for k in ['electricity']\
                                for t in self.timesteps\
                                    if t in timesteps_2030),'jor_shale')
                

                #-----
                # WEST BANK
                #-----
        
                # [1] RES
                # <<<<< Does not apply >>>>>
                
                # [2] SELF-SUFFICIENCY
                if self.scenario == 'COO': #and self.scenario != 'UTO':
                    self.model.addConstr(
                        gp.quicksum( \
                            self.ss_factor * \
                                # sum of total demand
                                (self.arcFlows['west_bank_generation',j,k,t] \
                                    + self.arcFlows['israel_generation',j,k,t] \
                                        + self.arcFlows['jordan_generation',j,k,t])
                                            for j in ['west_bank_energy_demand']
                                                for k in ['electricity']
                                                    for t in self.timesteps if t in timesteps_2030)
                        == \
                          gp.quicksum( \
                              (self.arcFlows['west_bank_generation','west_bank_energy_demand',k,t])
                                    for k in ['electricity']
                                        for t in self.timesteps if t in timesteps_2030),'wb_ss')

                # [3] NO GAS CAPACITY ALLOWED UNDER COO 
                unexpandable = ['west_bank_natural_gas']
                self.model.addConstrs(
                    (self.capacity_indices[n,k,t] == 0\
                        for n in unexpandable\
                            for k in ['electricity']\
                                for t in self.timesteps),'wb_gas_change')
                
                #-----
                # GAZA
                #-----
        
                # [1] RES
                # <<<<< Does not apply >>>>>
                
                # [2] SELF-SUFFICIENCY
                if self.scenario == 'COO': #and self.scenario != 'UTO':
                    self.model.addConstr(
                        gp.quicksum( \
                            self.ss_factor * \
                                # sum of total demand
                                (self.arcFlows['gaza_generation',j,k,t] \
                                    + self.arcFlows['israel_generation',j,k,t] \
                                        + self.arcFlows['egypt_generation',j,k,t])
                                            for j in ['gaza_energy_demand']
                                                for k in ['electricity']
                                                    for t in self.timesteps if t in timesteps_2030) \
                        == \
                        gp.quicksum( \
                            (self.arcFlows['gaza_generation','gaza_energy_demand',k,t])
                                for k in ['electricity']
                                    for t in self.timesteps if t in timesteps_2030),'gaz_ss')

        
        
    def run(self,pprint=True,write=True):
        '''Function to solve GurobiPy model
        '''
        if write==True:
            print('')
        # set output flag
        if not pprint:
            self.model.setParam('OutputFlag', 0)
        else:
            self.model.setParam('OutputFlag', 1)
        # optimise
        self.model.optimize()


    def get_results(self):
        '''Fetch results from model
        '''
        if self.model.Status != 2:
            raise ValueError('Could not get results! Model may be infeasible')
        else:
            return nextra_postprocess(self)


    def debug(self,output_path='../outputs/__cache__/'):
        '''Compute model Irreducible Inconsistent Subsystem (IIS) to help deal with infeasibilies
        '''
        self.model.computeIIS()
        self.model.write(output_path+'debug_report.ilp')