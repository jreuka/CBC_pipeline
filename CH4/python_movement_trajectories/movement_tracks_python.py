import pandas as pd
import numpy as np
from datetime import datetime
from tqdm import tqdm


#read in an prepare data
df = pd.read_csv('./BrBr_202210_resampled_500ms.csv')
dff = df[df.duplicated(subset=['location', 'datetime', 'animal_id'], keep='first')]

#numbers of videos included
print(len(np.unique(dff['file_name'])))

dff = dff.drop(['frame_number', 'track_id', 'location', 'file_name', 'timebin_1min', 'timebin_5min', 'timebin_10min',
               'timebin_30min', 'velocity', 'camera'], axis=1)

dff['datetime'] = dff.apply(lambda x: datetime.strptime(x['datetime'], '%Y-%m-%d %H:%M:%S.%f'), axis=1)
#date range included
print(max(dff['datetime']))
print(min(dff['datetime']))

#seperate info for animals
cus_df = dff.loc[dff['animal_id'] == 1.].sort_values(['datetime'])
mal_df = dff.loc[dff['animal_id'] == 2.].sort_values(['datetime'])

# bin to 2 min intervals
cus_df_cl = cus_df.set_index('datetime')
cus_df_cl['bin_times'] = cus_df_cl.index.floor('2T')

mal_df_cl = mal_df.set_index('datetime')
mal_df_cl['bin_times'] = mal_df_cl.index.floor('2T')


# Take tracks with at least n_samples observations and random sample - pivot wide
def get_trackdata_python(df, n_samples):
    tr_df = pd.DataFrame()
    for g in tqdm(df.groupby('bin_times')):
        if g[1].shape[0] < n_samples:
            continue

        gdf = g[1].groupby('datetime').aggregate(func="mean")

        for i in [t for t in pd.date_range(g[1]['bin_times'].unique()[0], periods=240, freq='.5S').to_list() if t not in gdf.index.to_list()]:
            if i not in g[1].index:
                rr = pd.DataFrame(
                    [[g[1]['animal_id'].unique()[0], 0.0, np.nan, np.nan, np.nan, g[1]['bin_times'].unique()[0], i]],
                    columns=g[1].columns.to_list() + ['datetime'])
                rr = rr.set_index('datetime')
                gdf = pd.concat([gdf, rr], ignore_index=False)

        rnr_df = gdf.sort_index().reset_index().drop_duplicates()

        rnr_aid = rnr_df.animal_id.unique().item()
        rnr_time = g[0].to_numpy()
        rnr_df = pd.melt(rnr_df, id_vars=['datetime', 'animal_id'],
                         value_vars=['x', 'y', 'poly_area']).pivot(index='datetime',
                         #value_vars=['x', 'y']).pivot(index='datetime',
                                                                    columns='variable',
                                                                    values='value').reset_index().drop(['datetime'],
                                                                                                       axis=1)

        ndf = rnr_df.unstack().to_frame().T
        ndf.columns = ndf.columns.map('{0[0]}_{0[1]}'.format)
        ndf['time'] = rnr_time
        ndf['animal_id'] = rnr_aid

        tr_df = pd.concat([tr_df, ndf], ignore_index=True)
    return tr_df

# number of samples that have to be present to use the trajectory (within 2 min time window)
n_samples = 240

tr_mal = get_trackdata_python(mal_df_cl, n_samples)
tr_cus = get_trackdata_python(cus_df_cl, n_samples)

pd.concat([tr_mal, tr_cus], ignore_index=True).to_csv("nBrBr_long_2min_" + str(n_samples) + ".csv", index=False)

