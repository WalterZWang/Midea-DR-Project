# -*- encoding: utf-8 -*-
'''
@File    :   data_evaluation2.py
@Time    :   2022/12/07 20:33:53
@Author  :   Zhenyu Wang 
'''
'''
This module is used to evaluate data by missing rate.
The data format (data frame) comes from Influx_API.
'''

import os
import sys
import matplotlib.pyplot as plt
from matplotlib.pylab import mpl
import numpy as np
import utility as util
import pandas as pd
import pickle
import copy
from Influxdb_API.Influxdb_API import ClientInfluxdb

plt.style.use('seaborn-deep')
mpl.rcParams['axes.unicode_minus'] = False
mpl.rcParams['font.size'] = 8


def resampling(data_frame, rsp_time='15min'):
    df_rsp = copy.deepcopy(data_frame)
    return df_rsp.resample(rsp_time).mean()

def cal_missing_rate(data_frame, time_window, params):
    '''
    Calculates the missing rate of a data_frame
    '''

    missing_rate = pd.DataFrame(data=None, columns=data_frame.columns)
    # date = []
    for i in range(0, (params['end_time']-params['start_time']).days//time_window):
        time1 = params['start_time'] + pd.to_timedelta(time_window*i, unit='D')
        time2 = params['start_time'] + pd.to_timedelta(time_window*(i+1), unit='D')
        # date.append(time1)
        for col in data_frame.columns:
            ms = pd.DataFrame([1 - data_frame[col].loc[time1:time2].count() / (params['rsp_num']*time_window*24)], index=[time1], columns=[col])
            missing_rate = missing_rate.append(ms)
    # missing_rate.index = date

    return missing_rate

def plot_missing_rate(missing_rate, time_window, params, mark):
    '''
    Plot missing rate over time
    '''
    id = params['tag_dict']['nid'].split('/')[-3][-4:]
    label = params['tag_dict']['nid'].split('/')[-2] + '_' + params['tag_dict']['nid'].split('/')[-1]

    plt.plot(missing_rate.index, missing_rate, label=label, marker='*')

    plt.title(id + f' Missing Rate (Per {time_window} day) ' + mark)
    plt.xlabel("Date")
    plt.ylabel("Missing rate")
    plt.legend(loc = 'upper left')

    plt.gcf().set_size_inches(16, 8)
    plt.savefig(f'./results/data_evaluation/'+id+f' Missing Rate (Per {time_window} day) '+mark+'.png', dpi=300, bbox_inches='tight', pad_inches=0.1)
    # plt.show()
    
    plt.close()
    # plt.clf()

    print(id + f' Missing Rate (Per {time_window} day) ' + mark)
    return

def remove_outliers(data_frame):
    '''remove outliers in a data_frame'''

    # 删除小于0的值
    data_frame[data_frame < 0]  = np.nan
    # 利用箱线图去除离群值, 会把不是异常值的判定为异常值
    Dcos = data_frame.quantile(0.95) - data_frame.quantile(0.05)
    L = data_frame.quantile(0.05) - 1.5 * Dcos
    U = data_frame.quantile(0.95) + 1.5 * Dcos
    data_frame[data_frame < L] = np.nan
    data_frame[data_frame > U] = np.nan

    return data_frame

def linear_imputation(data_frame, imputation_time_delta, sampling_time_delta):
    '''
    Linear interpolation of a data_frame

    data_frame: data that belongs to the "data_frame" format.
    imputation_time_delta: data loss for more than consecutive imputation_time_delta will not be interpolated.
    sampling_time_delta: sampling interval (15min).
    '''

    for col in data_frame.columns:
        # 不对启停数据进行插值
        if col == 'onOff': continue
        series = data_frame[col]

        # 获取空值索引
        series_nan = series[series.isna()]
        series_nan_index = series_nan.index
        if series_nan_index.empty: continue
        
        # 获取小于imputation_time_delta的空值索引
        col_imputation_list = []
        start = series_nan_index[0]
        temp = series_nan_index[0]
        end = series_nan_index[0]
        for i in range(len(series_nan_index)-1):
            end = series_nan_index[i+1]
            if (end-temp) == sampling_time_delta:
                temp = end
            else:
                if (temp - start) <= imputation_time_delta and (start!=series.head(1).index and end!=series.tail(1).index):
                    col_imputation_list.append([start, temp])
                start = end
                temp = end
        if (temp - start) <= imputation_time_delta and (start!=series.head(1).index and end!=series.tail(1).index):
            col_imputation_list.append([start, temp])

        # 对满足imputation_time_delta的空值进行线性插值
        for imputation in col_imputation_list:
            data_frame[col].loc[imputation[0]-sampling_time_delta: imputation[1]+sampling_time_delta] = \
                series.loc[imputation[0]-sampling_time_delta: imputation[1]+sampling_time_delta].interpolate(method='polynomial', order=1)
        
    return data_frame



# 1.Get data from Influxdb_API
db_name='moserver'
params={
    'measurement_name':'modata',
    'start_time': pd.to_datetime('2022-11-01 00:00:00'),
    'end_time': pd.to_datetime('2022-12-08 00:00:00'),
    'field_list': ['roomTemp'],
    'tag_dict': {'nid': 'vrf/vrf_0000CC311178CCM26232341000271K0V/indoor/0'},
    'fore': False,
    'fore_horizon': None,
    'interval': None
}
db_client = ClientInfluxdb(db_name=db_name) 
df = db_client.read_influxdb(**params)
# str -> np.float64
for col in df.columns:
    df[col] = pd.to_numeric(df[col], errors='ignore')
print('data acquired')

params_process={
    'start_time': pd.to_datetime('2022-11-01 00:00:00'),
    'end_time': pd.to_datetime('2022-12-08 00:00:00'),
    'rsp_time': pd.Timedelta('15 min'),
    'rsp_num': 4,
    'imputation_time_delta': pd.Timedelta('6 hours')
}
# resampling data, rsp_time=15min
df = resampling(df, params_process['rsp_time'])


# 2.Evaluate missing rate of data_origin/remove_otliers/linear_imputation and save results
missing_rate = cal_missing_rate(df, 3, params_process)
plot_missing_rate(missing_rate, 3, params, mark='origin')

df_process = remove_outliers(df)
missing_rate_process = cal_missing_rate(df_process, 3, params_process)
plot_missing_rate(missing_rate_process, 3, params, mark='remove_outliers')

df_new = linear_imputation(df_process, params_process['imputation_time_delta'], params_process['rsp_time'])
missing_rate_new = cal_missing_rate(df_new, 3, params_process)
plot_missing_rate(missing_rate_new, 3, params, mark='polynomial_imputation')
