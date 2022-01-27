import os
import seaborn as sns
import matplotlib.pyplot as plt
import pickle 
import matplotlib as mpl

import warnings
warnings.filterwarnings('ignore')

import sys
sys.path.append('../../')

from infrasim.optimise import *
from infrasim.utils import *

mpl.rcParams['ytick.direction'] = 'out'
mpl.rcParams['xtick.direction'] = 'out'
mpl.rcParams['font.family']      = 'Arial'


file = open('../../outputs/results/model_run_results.pkl','rb')
results = pickle.load(file)
file.close()

#----
# preprocessing
#----

df = results['COO'].results_edge_flows.copy()
# remove gas storages
df = df[~df.from_id.str.contains('reservoir')]
# loop through storage nodes
for s in df[df.from_id.str.contains('storage')].from_id.unique():
    inflow = df.loc[df.to_id == s].reset_index(drop=True).groupby(\
                by=['timestep','hour','day','month','year']).sum().reset_index()
    
    outflow = df.loc[df.from_id == s].reset_index(drop=True).groupby(\
                by=['timestep','hour','day','month','year']).sum().reset_index()

    charge = outflow.copy()
    charge['value'] = outflow['value'] - inflow['value']
    charge['from_id'] = s
    charge['scenario'] = df.scenario.unique()[0]
    charge['commodity'] = df.commodity.unique()[0]
    df = df[~df.from_id.isin([s])].reset_index(drop=True)
    df = df.append(charge,ignore_index=True)

df = df.drop('to_id',axis=1)

results['COO'].results_edge_flows = df

#----
# plotting: summer curve
#----

day         = 1
month_sum   = 6
month_win   = 12
isr_ylims   = [-1000,6000]
jor_ylims   = [-4000,16000]
wbk_ylims   = [-50,400]
gza_ylims   = [-10,70]

f,ax=plt.subplots(nrows=2,ncols=2,figsize=(12,8),sharex=True)

results['COO'].plot_hourly_profile(day=day,month=month_sum,year=2030,territory='Israel',
                                   linewidth=1,ax=ax[0,0])

results['COO'].plot_hourly_profile(day=day,month=month_sum,year=2030,territory='Jordan',
                                   linewidth=1,ax=ax[0,1])

results['COO'].plot_hourly_profile(day=day,month=month_sum,year=2030,territory='West Bank',
                                   linewidth=1,ax=ax[1,0])

results['COO'].plot_hourly_profile(day=day,month=month_sum,year=2030,territory='Gaza',
                                   linewidth=1,ax=ax[1,1])

ax[0,0].set_ylim(isr_ylims)
ax[0,1].set_ylim(jor_ylims)
ax[1,0].set_ylim(wbk_ylims)
ax[1,1].set_ylim(gza_ylims)

ax[0,0].set_xlim([1,24])
ax[0,1].set_xlim([1,24])
ax[1,0].set_xlim([1,24])
ax[1,1].set_xlim([1,24])

ax[0,0].set_ylabel('Supply (kWh)')
ax[1,0].set_ylabel('Supply (kWh)')
ax[1,0].set_xlabel('Hour')
ax[1,1].set_xlabel('Hour')

ax[0,0].set_title('a',loc='left',fontweight='bold',fontsize=14)
ax[0,1].set_title('b',loc='left',fontweight='bold',fontsize=14)
ax[1,0].set_title('c',loc='left',fontweight='bold',fontsize=14)
ax[1,1].set_title('d',loc='left',fontweight='bold',fontsize=14)

f.savefig('../../outputs/figures/supp_operations_curves_summer.pdf',bbox_inches='tight')

#----
# plotting: winter curve
#----

f,ax=plt.subplots(nrows=2,ncols=2,figsize=(12,8),sharex=True)

results['COO'].plot_hourly_profile(day=day,month=month_win,year=2030,territory='Israel',
                                   linewidth=1,ax=ax[0,0])

results['COO'].plot_hourly_profile(day=day,month=month_win,year=2030,territory='Jordan',
                                   linewidth=1,ax=ax[0,1])

results['COO'].plot_hourly_profile(day=day,month=month_win,year=2030,territory='West Bank',
                                   linewidth=1,ax=ax[1,0])

results['COO'].plot_hourly_profile(day=day,month=month_win,year=2030,territory='Gaza',
                                   linewidth=1,ax=ax[1,1])

ax[0,0].set_ylim(isr_ylims)
ax[0,1].set_ylim(jor_ylims)
ax[1,0].set_ylim(wbk_ylims)
ax[1,1].set_ylim(gza_ylims)

ax[0,0].set_xlim([1,24])
ax[0,1].set_xlim([1,24])
ax[1,0].set_xlim([1,24])
ax[1,1].set_xlim([1,24])

ax[0,0].set_ylabel('Supply (kWh)')
ax[1,0].set_ylabel('Supply (kWh)')
ax[1,0].set_xlabel('Hour')
ax[1,1].set_xlabel('Hour')

ax[0,0].set_title('a',loc='left',fontweight='bold',fontsize=14)
ax[0,1].set_title('b',loc='left',fontweight='bold',fontsize=14)
ax[1,0].set_title('c',loc='left',fontweight='bold',fontsize=14)
ax[1,1].set_title('d',loc='left',fontweight='bold',fontsize=14)

f.savefig('../../outputs/figures/supp_operations_curves_winter.pdf',bbox_inches='tight')