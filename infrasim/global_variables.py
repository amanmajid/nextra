'''
    global_variables.py

    @amanmajid
'''


global_variables = {
                    # -DIRECTORIES
                    'results_directory'                 : '../nextra_results/',
                    # -INDICES
                    'edge_index_variables'              : ['from_id','to_id','commodity','timestep'],
                    # -ELECTRICITY SYSTEM
                    'baseload_coefficient'              : 0.5,
                    'storage_loss_coefficient'          : 0.1,
                    'peak_demand_reserve'               : 0.2,
                    'loss_factor_seasonal'              : 0.90,         # seasonal losses (10%) for thermoelectric plants (from Nurit)
                    'loss_factor_maintenance_thermo'    : 0.92,         # maintenance downtime (8%) per annum in thermoelectric plants
                    'loss_factor_maintenance_res'       : 0.92,         # maintenance downtime (8%) per annum in solar/wind plants
                    'loss_factor_transmission'          : 0.95,         # losses (%) due to transmission
                    'reserve_capacity_factor'           : 0.80,         # 10% reserve capacity
                    'maximum_curtailment'               : 0.15,         # Percentage of total generation (zero curtailment usually makes model infeasible)
                    'emissions_reduction_2030'          : 0.30,         # Percentage reduction in total emissions to 2030 relative to BAS scenario
                    'BAS_emissions_in_2030'             : 61343,        # Total estimated CO2 emissions (tonnes) under BAS in 2030
                    # -BATTERY PARAMS
                    'battery_capacity_min_percentage'   : 0.20,         # Percentage of total renewable capacity (solar + wind) installed
                    'battery_capacity_max_percentage'   : 0.80,         # Percentage of total renewable capacity (solar + wind) installed
                    'battery_minimum_level'             : 0.35,         # Minimum level to maintain in battery (preserves health), also incorporates losses/inefficiencies/maintanence
                    'battery_charge_rate'               : 200*24,       # MW
                    'battery_discharge_rate'            : 300*24,       # MW
                    'battery_charge_hours'              : [9,10,11,12,13,14],
                    # -RAMPING RATE
                    # https://www.researchgate.net/post/What_is_the_typical_MW_minute_ramping_capability_for_each_type_of_reserve
                    'ocgt_ramping_rate'                 : 3500,         # MW/h
                    'ccgt_ramping_rate'                 : 3500,         # MW/h
                    'coal_ramping_rate'                 : 240,          # MW/h
                    'solar_ramping_rate'                : 12000,        # MW/h
                    'wind_ramping_rate'                 : 3600,         # MW/h
                    'nuclear_ramping_rate'              : 1200,         # MW/h
                    'nat_gas_ramping_rate'              : 3500,         # MW/h
                    'pumped_hydro_ramping_rate'         : 12000,        # MW/h
                    'diesel_ramping_rate'               : 420,          # MW/h
                    'shale_ramping_rate'                : 420,          # MW/h
                    # -DEMAND GROWTH
                    'jordan_demand_growth_rate'         : 0.03,         # From Jordan's reports
                    'israel_demand_growth_rate'         : 0.028,        # From Nurit
                    'palestine_demand_growth_rate'      : 0.05,         # From Nurit
                    'peak_demand_factor'                : 1,
                    # -ISRAEL
                    'isr_res_target_2030'               : 0.3,          # %
                    'isr_ng_target_2030'                : 0.7,          # %
                    'isr_max_wind_cap'                  : 739,          # MW
                    'isr_max_ccgt_cap'                  : 3400,         # MW
                    'isr_min_coal_output'               : 0.5,          # % of capacity [ASK GROUP]
                    'isr_min_gas_output'                : 0.5,          # % of capacity [ASK GROUP]
                    # -JORDAN
                    'jor_res_target_2030'               : 0.3,          # %
                    'jor_ng_target_2030'                : 0.5,          # %
                    'jor_shale_target_2030'             : 0.2,          # %
                    'jor_min_shale_output'              : 0.0,          # % of capacity [ASK GROUP]
                    'jor_min_gas_output'                : 0.1,          # % of capacity [ASK GROUP]
                    # -WEST BANK
                    'pal_res_target_2030'               : 0.3,          # %
                    'pal_ng_target_2030'                : 0.3,          # %
                    # -GAZA
                    'gaz_res_target_2030'               : 0.3,          # %
                    'gaz_ng_target_2030'                : 0.7,          # %
                    'gaz_diesel_cap'                    : 60,           # MW
                    'egypt_to_gaza_export'              : 0,            # Zero as of 2018
                    # -COOPERATION
                    'coop_res_target_2030'              : 0.3,          # %
                    'self_sufficiency_factor'           : 0.3,          # %
                    # -EXTENDED ARAB GRID
                    'eag_res_target_2030'               : 0.3,          # %
                    'eag_ng_target_2030'                : 0.5,          # %
                    # -OTHER
                    'super_source_maximum'              : 10**12,
                    'mask_value'                        : -999,
                    'maximum_capacity'                  : 20000,        # MW
                    }


connectivity     = {
                    # Jordan ->
                    'jordan_to_westbank'            : 20,
                    'jordan_to_israel'              : 0,
                    # Israel ->
                    'israel_to_westbank'            : 99999,
                    'israel_to_gaza'                : 99999,
                    'israel_to_jordan'              : 0,
                    # West Bank ->
                    'westbank_to_israel'            : 0,
                    # Egypt ->
                    'egypt_to_gaza'                 : 99999,
                   }


# costs
# https://iea.blob.core.windows.net/assets/4ed140c1-c3f3-4fd9-acae-789a4e14a23c/WorldEnergyOutlook2021.pdf
capex           = {'Diesel'   : 1175,         # $/kW
                   'Gas'      : 700,          # $/kW
                   'Solar'    : 310,          # $/kW
                   'Coal'     : 1200,         # $/kW
                   'Battery'  : 1389,         # $/kW 
                   'Wind'     : 980,          # $/kW
                   'Shale'    : 1175,}        # $/kW


opex            =  {'Diesel'   : 100,         # $/kW-year
                    'Gas'      : 100,         # $/kW-year
                    'Solar'    : 5,           # $/kW-year
                    'Coal'     : 135,         # $/kW-year
                    'Battery'  : 15,          # $/kW-year
                    'Wind'     : 10,          # $/kW-year
                    'Shale'    : 100,}        # $/kW-year


# emission variables
co2             =  {'Diesel'   : 848,          # g/kWh
                    'Gas'      : 474,          # g/kWh
                    'Solar'    : 0,            # g/kWh
                    'Coal'     : 880,          # g/kWh
                    'Storage'  : 0,            # g/kWh
                    'Battery'  : 0,            # g/kWh
                    'Wind'     : 0,            # g/kWh
                    'Shale'    : 848,}         # g/kWh


nox             =  {'Diesel'   : 0.43,         # g/kWh
                    'Gas'      : 0.24,         # g/kWh
                    'Solar'    : 0,            # g/kWh
                    'Coal'     : 0.46,         # g/kWh
                    'Storage'  : 0,            # g/kWh
                    'Battery'  : 0,            # g/kWh
                    'Wind'     : 0,            # g/kWh
                    'Shale'    : 0.43,}        # g/kWh


sox             =  {'Diesel'   : 0.14,         # g/kWh
                    'Gas'      : 0.08,         # g/kWh
                    'Solar'    : 0,            # g/kWh
                    'Coal'     : 0.46,         # g/kWh
                    'Storage'  : 0,            # g/kWh
                    'Battery'  : 0,            # g/kWh
                    'Wind'     : 0,            # g/kWh
                    'Shale'    : 0.14,}        # g/kWh

water_use       =  {'Diesel'   : 0.0397,       # g/kWh
                    'Gas'      : 0.0398,       # g/kWh
                    'Solar'    : 0,            # g/kWh
                    'Coal'     : 0.0397,       # g/kWh
                    'Storage'  : 0,            # g/kWh
                    'Battery'  : 0,            # g/kWh
                    'Wind'     : 0,            # g/kWh
                    'Shale'    : 0.0397,}      # g/kWh