import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib as mpl

mpl.rcParams['ytick.direction'] = 'out'
mpl.rcParams['xtick.direction'] = 'out'
mpl.rcParams['font.family']      = 'Arial'

basepath = '../../data/nextra/nodal_flows/processed_flows_2030.csv'
data = pd.read_csv(basepath)
data['date'] = pd.to_datetime(data['date'])
data['palestine_energy_demand'] = data['west_bank_energy_demand'] + data['gaza_energy_demand']
data.head(3)

f,ax=plt.subplots(nrows=3,ncols=1,figsize=(8,9),sharex=True)

sns.lineplot(x='date',y='israel_energy_demand',data=data,color='teal',ax=ax[0])
ax[0].set_ylabel('Energy demand (kWh)')
ax[0].set_xlabel('Date')
ax[0].set_title('a',loc='left',fontweight='bold',fontsize=14)

sns.lineplot(x='date',y='jordan_energy_demand',data=data,color='teal',ax=ax[1])
ax[1].set_ylabel('Energy demand (kWh)')
ax[1].set_xlabel('Date')
ax[1].set_title('b',loc='left',fontweight='bold',fontsize=14)

sns.lineplot(x='date',y='palestine_energy_demand',data=data,color='teal',ax=ax[2])
ax[2].set_ylabel('Energy demand (kWh)')
ax[2].set_xlabel('Date')
ax[2].set_title('c',loc='left',fontweight='bold',fontsize=14)

f.savefig('../../outputs/figures/supp_demand_curves.pdf',bbox_inches='tight')

print('done.')