import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt
import seaborn

mpl.rcParams['ytick.direction'] = 'out'
mpl.rcParams['xtick.direction'] = 'out'
mpl.rcParams['font.family']      = 'Arial'

demand = pd.DataFrame({'Region' : ['ISR','ISR','JOR','JOR','WBK','WBK','GZA','GZA'],
                       'Year'   : [2020,2030,2020,2030,2020,2030,2020,2030],
                       'Demand' : [68,82.42,20.72,25.69,4.96,6.3,1.3,1.70],
                       'Population' : [9216900,10735866,10203140,12415557,2759324,3300286,2043944,2444656]})

f = plt.figure(figsize=(4,3))
f.patch.set_facecolor('white')
seaborn.barplot(x='Region',y='Demand',hue='Year',data=demand,palette='hls',
                edgecolor='lightgray',linewidth=0.5)
plt.legend(frameon=False)
plt.ylabel('Demand (TWh)')
plt.savefig('../../outputs/figures/energy_demand.pdf',bbox_inches='tight')

f = plt.figure(figsize=(4,3))
f.patch.set_facecolor('white')

demand['Population'] = demand['Population'].divide(10**6)

seaborn.barplot(x='Region',y='Population',hue='Year',data=demand,palette='hls',
                edgecolor='lightgray',linewidth=0.5)

plt.legend(frameon=False)
plt.ylabel('Population (million)')
plt.savefig('../../outputs/figures/population.pdf',bbox_inches='tight')