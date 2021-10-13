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
                    'ocgt_ramping_rate'                 : 1200,         # MW/h
                    'ccgt_ramping_rate'                 : 600,          # MW/h
                    'coal_ramping_rate'                 : 120,          # MW/h
                    'solar_ramping_rate'                : 12000,        # MW/h
                    'wind_ramping_rate'                 : 1800,         # MW/h
                    'nuclear_ramping_rate'              : 1200,         # MW/h
                    'nat_gas_ramping_rate'              : 1800,         # MW/h
                    'pumped_hydro_ramping_rate'         : 12000,        # MW/h
                    'diesel_ramping_rate'               : 120,          # MW/h
                    'shale_ramping_rate'                : 180,          # MW/h
                    # -DEMAND GROWTH
                    'jordan_demand_growth_rate'         : 0.03,
                    'israel_demand_growth_rate'         : 0.028,
                    'palestine_demand_growth_rate'      : 0.03,
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
                    'pal_ng_target_2030'                : 0.7,          # %
                    # -GAZA
                    'gaz_res_target_2030'               : 0.3,          # %
                    'gaz_ng_target_2030'                : 0.7,          # %
                    'gaz_diesel_cap'                    : 60,           # MW
                    # -COOPERATION
                    'coop_res_target_2030'              : 0.3,          # %
                    'self_sufficiency_factor'           : 0.2,          # %
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