# -*- coding: utf-8 -*-
"""
Created on Wed Sep 22 12:42:28 2021

@author: aqua
"""

import sys
sys.path.append('../')

from infrasim.optimise import *

#File paths
nodes = '../data/nextra/spatial/network/nodes.shp'
edges = '../data/nextra/spatial/network/edges.shp'
flows = '../data/nextra/nodal_flows/processed_flows_2030.csv'

# Params
timesteps=24
super_source=False
pprint=True
save_figures=True

infrasim_init_directories()

# BAU
model = nextra(nodes,edges,flows,
               scenario='COO',
               energy_objective=False,
               #super_source=True,
               #super_sink=True,
               #res_factor=99,
               #model_name='meow',
               )


model.build()
