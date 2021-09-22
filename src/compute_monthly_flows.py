# -*- coding: utf-8 -*-
'''
    compute_monthly_flows.py

        Aggregate raw hourly datasets to monthly resolution

'''

import pandas as pd

path = '../data/nodal_flows/processed_flows_2030.csv'
data = pd.read_csv(path)

monthly_sum = data.groupby(by=['Month']).sum().reset_index()