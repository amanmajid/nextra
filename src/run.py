# -*- coding: utf-8 -*-
"""
Created on Wed Sep 22 12:42:28 2021

@author: aqua
"""

import sys
sys.path.append('../')

from infrasim.optimise import *

#File paths
nodes = '../data/nextra/spatial/nodes.shp'
edges = '../data/nextra/spatial/edges.shp'
flows = '../data/nextra/nodal_flows/processed_flows_2030.csv'

# Params
timesteps=24
super_source=False
pprint=True
save_figures=True

# BAU
bau = nextra(nodes,edges,flows)