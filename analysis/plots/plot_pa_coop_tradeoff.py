import pandas as pd
import matplotlib.pyplot as plt
import matplotlib as mpl

mpl.rcParams['ytick.direction'] = 'out'
mpl.rcParams['xtick.direction'] = 'out'
mpl.rcParams['font.family']      = 'Arial'

capacities = pd.read_csv('../outputs/results/sensitivity_coop_sufficiency.csv')
capacities = capacities.groupby(by='self_sufficiency_factor').sum().reset_index()

f,ax = plt.subplots(nrows=1,ncols=1,figsize=(4.5,4))

x = capacities.self_sufficiency_factor.mul(100).to_numpy()
y = capacities.value.divide(1000).to_numpy()

plt.plot(x,y,color='teal')

plt.xlabel('Self-sufficiency (%)')
plt.ylabel('Total capacity added (GW)')
#plt.title('Capacity in West Bank and Gaza',loc='left',fontweight='bold')
plt.xlim([0,100])
plt.ylim([0,1.400])
f.savefig('../outputs/figures/coop_tradeoff.pdf',bbox_inches='tight')