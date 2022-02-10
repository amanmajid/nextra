import pandas as pd
import os

##########
# Get renewables ninja data

basepath = '../data/_raw/renewable_ninja/'

# load
data = []
for f in os.listdir(basepath):
    if '.csv' in f:
        d = pd.read_csv(basepath+f,skiprows=3)
        d['region'] = f.split('.')[0].split('_')[0]
        d['type'] = f.split('.')[0].split('_')[1]
        data.append(d)
data = pd.concat(data,ignore_index=True)

# format datetime
data['time'] = pd.to_datetime(data['time'])
data['hour'] = data['time'].dt.hour 
data['day'] = data['time'].dt.day
data['month'] = data['time'].dt.month

# reindex
data = data[['hour','day','month','region','type','electricity']]

##########
# Get flow data

flowpath = '../data/nextra/nodal_flows/processed_flows_2030.csv'
flows = pd.read_csv(flowpath)

##########
# Amend flows
for c in flows.columns:
    print('Processing: ' + c)
    if 'wind' in c or 'solar' in c:
        for i in flows[c].index:
            idx = data.loc[(data.hour == flows.loc[i,'hour']) & \
                           (data.day == flows.loc[i,'day']) & \
                           (data.month == flows.loc[i,'month']) ]
                        
            val = idx.loc[ (idx.region.str.contains(c.split('_')[0])) & \
                           (idx.type.str.contains(c.split('_')[-1])), 'electricity'].iloc[0]
            
            
            flows.loc[i,c] = val
            
##########
# Save

flows.to_csv('../data/nextra/nodal_flows/processed_flows_2030_res_nin.csv',index=False)