import os

import numpy as np
import pandas as pd
from datetime import datetime
from tqdm import tqdm

f_path = "#PATH TO PIPELINE PREDICITONS#"
files = [f for f in os.listdir(f_path) if f.endswith(".csv") and "prediction" in f]
output_file_name = "#PATH + NAME FOR OUTPUT FILE" # "./output.csv"

def select_reformat(df):
    dff = df.loc[df['seg_class'] == 1.]

    dff = dff.drop(['seg_class', 'Unnamed: 0'], axis=1)

    if dff.empty:
        return dff, dff, dff, dff, {}

    dff['datetime'] = dff.apply(lambda x: datetime.strptime("-".join(x['file_name'].split("_")[2:4]), '%Y%m%d-%H%M%S') +
                                          pd.Timedelta(seconds=x['frame_number'] / 36.5), axis=1)

    dff['camera'] = dff['file_name'].str.split("_").str[-1]
    dff['file_name'] = dff['file_name'].str.split("_").str[0:-1].str.join('_')

    conv_loc_num = {x: i for i, x in enumerate(np.unique(df.location))}
    conv_num_loc = {v: k for k, v in conv_loc_num.items()}

    dff['location'] = dff['location'].replace(conv_loc_num, regex=True)

    cus_df = dff.loc[dff['animal_id'] == 1.].sort_values(['datetime'])
    mal_df = dff.loc[dff['animal_id'] == 2.].sort_values(['datetime'])

    cus_df_r = cus_df.loc[cus_df['camera'] == "right"]
    cus_df_l = cus_df.loc[cus_df['camera'] == "left"]
    mal_df_r = mal_df.loc[mal_df['camera'] == "right"]
    mal_df_l = mal_df.loc[mal_df['camera'] == "left"]

    return cus_df_r, cus_df_l, mal_df_r, mal_df_l, conv_num_loc


def resample(aid_df):
    aid_df = aid_df.set_index('datetime').resample('.5S').agg({'x': np.mean,
                                                               'y': np.mean,
                                                               'poly_area': np.mean,
                                                               'track_conf': np.mean,
                                                               'frame_number': np.min,
                                                               'location': lambda x: np.argmax(np.bincount(x)) if (
                                                                       len(x) > 0) else np.NaN,
                                                               'animal_id': lambda x: np.argmax(np.bincount(x)) if (
                                                                       len(x) > 0) else np.NaN,
                                                               'file_name': lambda x: "_".join(np.unique(x)),
                                                               'camera': lambda x: "_".join(np.unique(x))
                                                               }).dropna(axis=0)

    aid_df['x'] = aid_df['x'].astype(int)
    aid_df['y'] = aid_df['y'].astype(int)
    aid_df['frame_number'] = aid_df['frame_number'].astype(int)
    return aid_df


def calc_speed(aid_df_res):
    if aid_df_res.empty:
        return aid_df_res
    aid_df_res['timebin_1min'] = aid_df_res.index.floor('1min')
    aid_df_res['timebin_5min'] = aid_df_res.index.floor('5min')
    aid_df_res['timebin_10min'] = aid_df_res.index.floor('10min')
    aid_df_res['timebin_30min'] = aid_df_res.index.floor('30min')
    aid_df_res = aid_df_res.reset_index()
    aid_df_res['prev_x'] = aid_df_res.x.shift(1)
    aid_df_res['prev_y'] = aid_df_res.y.shift(1)
    aid_df_res['timediff2prev'] = aid_df_res.datetime - aid_df_res.datetime.shift(1)
    aid_df_res['velocity'] = aid_df_res.apply(lambda x:
                                              np.sqrt((x['prev_x'] - x['x']) ** 2 + (x['prev_y'] - x['y']) ** 2)
                                              if not np.isnan(x['timediff2prev'].total_seconds()) or
                                                 x['timediff2prev'].total_seconds() < 1 else np.NaN,
                                              axis=1)

    aid_df_res = aid_df_res.drop(['prev_x', 'prev_y', 'timediff2prev'], axis=1)

    return aid_df_res


def combined_resample(df):
    cus_df_r, cus_df_l, mal_df_r, mal_df_l, conv_num_loc = select_reformat(df)

    if not cus_df_r.empty:
        cus_df_r = calc_speed(resample(cus_df_r))
        #cus_df_r = resample(cus_df_r)
        cus_df_r['location'] = cus_df_r['location'].replace(conv_num_loc, regex=True)

    if not cus_df_l.empty:
        cus_df_l = calc_speed(resample(cus_df_l))
        #cus_df_l = resample(cus_df_l)
        cus_df_l['location'] = cus_df_l['location'].replace(conv_num_loc, regex=True)

    if not mal_df_r.empty:
        mal_df_r = calc_speed(resample(mal_df_r))
        #mal_df_r = resample(mal_df_r)
        mal_df_r['location'] = mal_df_r['location'].replace(conv_num_loc, regex=True)

    if not mal_df_l.empty:
        mal_df_l = calc_speed(resample(mal_df_l))
        #mal_df_l = resample(mal_df_l)
        mal_df_l['location'] = mal_df_l['location'].replace(conv_num_loc, regex=True)

    out_df = pd.concat([dframe for dframe in [mal_df_r, mal_df_l, cus_df_r, cus_df_l] if not df.empty], ignore_index=True)

    return out_df



df = pd.DataFrame()
for file in tqdm(files):
    data = pd.read_csv(f_path + file)

    if data.empty:
        continue
    print(file)
    data = combined_resample(data)


    df = pd.concat([df, data], axis=0)

df.to_csv(output_file_name, index=False)

