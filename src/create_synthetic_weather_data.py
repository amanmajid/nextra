import pandas as pd
import numpy
from tqdm import tqdm
import random
import seaborn
import matplotlib.pyplot as plt

fields = ['Israel_Direct_Radiation',
          'Jordan_Direct_Radiation',
          'Israel_Wind_Speed',
          'Jordan_Wind_Speed',
          'West_Bank_Direct_Radiation',
          'West_Bank_Wind_Speed']

replicates       = 100
new_data_list    = []

for replicate in range(1,replicates+1):
    # define start and end
    start = '1/1/2018'
    end   = '12/31/2030'
    # init realisation
    realisation = pd.DataFrame({'Date' : pd.date_range(start=start, end=end, freq='H')})
    realisation['Replicate']    = replicate
    realisation['Hour']         = realisation.Date.dt.hour
    realisation['Day']          = realisation.Date.dt.day
    realisation['Month']        = realisation.Date.dt.month
    realisation['Year']         = realisation.Date.dt.year
    #init with blanks
    realisation['Israel_Direct_Radiation']     = numpy.nan
    realisation['Jordan_Direct_Radiation']     = numpy.nan
    realisation['Israel_Wind_Speed']           = numpy.nan
    realisation['Jordan_Wind_Speed']           = numpy.nan
    realisation['West_Bank_Direct_Radiation']  = numpy.nan
    realisation['West_Bank_Wind_Speed']        = numpy.nan
    # loop each time step
    pbar = tqdm(realisation.index)
    for i in pbar:
        pbar.set_description('Replicate ' + str(replicate))
        for f in fields:
            hour  = realisation.at[i,'Hour']
            month = realisation.at[i,'Month']
            # sample
            idx_historical = weather_data[['Hour','Month',f]]
            idx_historical = idx_historical[(idx_historical.Hour==hour) & \
                                            (idx_historical.Month==month)].reset_index(drop=True)

            realisation.at[i,f] = random.choices(idx_historical[f].values,weights=None,k=1)[0]

    new_data_list.append(realisation)

new_weather_data = pd.concat(new_data_list,ignore_index=True)
new_weather_data.to_csv('../data/csv/synthetic_weather_data.csv')


new_weather_data = pd.read_csv('../data/csv/synthetic_weather_data.csv')
new_weather_data = new_weather_data[new_weather_data.Year==2025].reset_index(drop=True)
new_weather_data = new_weather_data[new_weather_data.Day==20].reset_index(drop=True)

f,ax = plt.subplots(figsize=(8,8),nrows=2,ncols=2,sharey=True,sharex=True)

israel = new_weather_data[['Replicate','Hour','Israel_Direct_Radiation']]
seaborn.lineplot(x='Hour',y='Israel_Direct_Radiation',
                 hue='Replicate',data=israel,ax=ax[0,0])
ax[0,0].set_title('Israel')
del israel

jordan = weather_data[['Replicate','Hour','Jordan_Direct_Radiation']]
seaborn.lineplot(x='Hour',y='Jordan_Direct_Radiation',
                 hue='Replicate',data=jordan,ax=ax[0,1])
ax[0,1].set_title('Jordan')
del jordan

west_bank = weather_data[['Replicate','Hour','West_Bank_Direct_Radiation']]
seaborn.lineplot(x='Hour',y='West_Bank_Direct_Radiation',
                 hue='Replicate',data=west_bank,ax=ax[1,0])
ax[1,0].set_title('West Bank')
del west_bank

f.savefig('../outputs/figures/stochastic_sample.png',bbox_inches='tight')
