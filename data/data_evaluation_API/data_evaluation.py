# -*- encoding: utf-8 -*-
'''
@File    :   data_evaluation.py
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
import pandas as pd
import pickle
import copy

# plt.style.use('seaborn-deep')
# mpl.rcParams['axes.unicode_minus'] = False
# mpl.rcParams['font.size'] = 8

def resampling(data_frame, rsp_time='15min'):
    df_rsp = copy.deepcopy(data_frame)
    return df_rsp.resample(rsp_time).mean()

def cal_missing_rate(data_frame, step):
    '''
    Calculates the missing rate of a data_frame

    '''

    missing_rate = pd.DataFrame(data=None, index=data_frame.index, columns=data_frame.columns)
    for col in data_frame.columns:
        missing_rate[col] = 1 - (data_frame[col].rolling(step, min_periods=0).count() / float(step))
    describe = missing_rate.describe()
    
    for col in data_frame.columns:
        print(f'{col} minimal missing rate: ', describe.loc['min', col])
        print(f'{col} average missing rate: ', describe.loc['mean', col])

        # 获取具有最小missing_rate的时刻的所有索引
        idxmin = np.where(missing_rate[col] == missing_rate[col].min())
        # 获得离最新时刻最近的具有最小missing_rate的时刻
        best = missing_rate[col].iloc[idxmin[0]].tail(1)
        best_time = best.index.strftime('%Y-%m-%d %H:%M:00')
        print(f'{col} the closest optimal moment to the present: ', best_time[0])

    return missing_rate

def cal_missing_rate_old(data_frame, time_window, params):
    '''
    Calculates the missing rate of a data_frame
    '''

    missing_rate = pd.DataFrame(data=None, columns=data_frame.columns)
    for i in range(0, (params['end_time']-params['start_time']).days//time_window):
        time1 = params['start_time'] + pd.to_timedelta(time_window*i, unit='D')
        time2 = params['start_time'] + pd.to_timedelta(time_window*(i+1), unit='D')
        for col in data_frame.columns:
            ms = 1 - data_frame[col].loc[time1:time2].count() / (params['rsp_num']*time_window*24)
            missing_rate.loc[time1, col] = ms

    return missing_rate

def plot_missing_rate(missing_rate, params, params_process, mark):
    '''
    Plot missing rate over time
    '''
    id = params['tag_dict']['nid'].split('/')[-3][-4:]
    label = params['tag_dict']['nid'].split('/')[-2] + '_' + params['tag_dict']['nid'].split('/')[-1]
    step = params_process['step']

    plt.plot(missing_rate.index, missing_rate, label=label)

    plt.title(id + f' Missing Rate ({step} steps forward) ' + mark)
    plt.xlabel("Date")
    plt.ylabel("Missing rate")
    plt.legend(loc = 'upper left')

    plt.gcf().set_size_inches(16, 8)
    plt.savefig(f'./results/data_evaluation/'+id+f' Missing Rate ({step} steps forward) '+mark+'.png', dpi=300, bbox_inches='tight', pad_inches=0.1)
    # plt.show()
    
    plt.close()
    # plt.clf()

    print(id + f' Missing Rate ({step} steps forward) ' + mark)
    return

def remove_outliers(data_frame):
    '''remove outliers in a data_frame'''

    # 删除小于0的值
    data_frame[data_frame < 0]  = np.nan
    # 利用箱线图去除离群值, 会把不是异常值的判定为异常值
    Dcos = data_frame.quantile(0.98) - data_frame.quantile(0.02)
    L = data_frame.quantile(0.02) - 1.5 * Dcos
    U = data_frame.quantile(0.98) + 1.5 * Dcos
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



