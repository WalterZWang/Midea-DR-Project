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


def resampling(df: pd.DataFrame, rsp_time: str='15min', **kw) -> pd.DataFrame:
    df_rsp = copy.deepcopy(df)
    return df_rsp.resample(rsp_time).mean()

def cal_missing_rate(df: pd.DataFrame, step: int, ms_thresh: float=0.2, **kw) -> pd.DataFrame:
    '''
    Calculates the missing rate of a data_frame
    '''

    missing_rate = pd.DataFrame(data=None, index=df.index, columns=df.columns)
    for col in df.columns:
        missing_rate[col] = 1 - (df[col].rolling(step, min_periods=0).count() / float(step))
    describe = missing_rate.describe()
    
    for col in df.columns:
        print(f'{col} minimal missing rate: ', describe.loc['min', col])
        print(f'{col} average missing rate: ', describe.loc['mean', col])

        # 获取具有最小missing_rate时刻的所有索引
        idxmin = np.where(missing_rate[col] == missing_rate[col].min())
        # 获得最近的具有最小missing_rate的时刻
        best = missing_rate[col].iloc[idxmin[0]].tail(1)
        best_time = best.index.strftime('%Y-%m-%d %H:%M:00')
        print(f'{col} the closest optimal moment to the present: ', best_time[0], '\n------------------')

    # 当dataframe有多组数据时
    if len(df.columns) > 1:
        # 获取每一行数据的missing_rate都小于20%的所有索引
        idx_thresh = missing_rate[missing_rate <= ms_thresh]
        idx_thresh = idx_thresh.dropna()
        # 所有数据满足距离当前时间段最近的3天缺失率低于20%的时刻
        closest_time = idx_thresh.tail(1).index.strftime('%Y-%m-%d %H:%M:00')
        print(f'The closest moment meets the condition (missing rate < {ms_thresh}) for multivariables: ', closest_time[0], '\n------------------\n\n')

    if 'plot' in kw:
        if kw['plot']:
            if 'mark' in kw:
                mark = kw['mark']
                df.plot(title=f'Measurement data ({mark})', figsize=(12,6))
                plt.legend(loc = 'upper left')
                missing_rate.plot(title=f'Missing Rate ({step} steps forward) ({mark})', figsize=(12,6))
                plt.legend(loc = 'upper left')
                plt.show()
            else:
                df.plot(title=f'Measurement data', figsize=(12,6))
                plt.legend(loc = 'upper left')
                missing_rate.plot(title=f'Missing Rate ({step} steps forward)', figsize=(12,6))
                plt.legend(loc = 'upper left')
                plt.show()


    return missing_rate

def remove_outliers(df: pd.DataFrame, window: int, **kw) -> pd.DataFrame:
    '''remove outliers in a data_frame'''

    df_new = copy.deepcopy(df)

    Q1 = df_new.rolling(window, center=True, min_periods=1).quantile(0.25)
    Q3 = df_new.rolling(window, center=True, min_periods=1).quantile(0.75)
    IQR = Q3 - Q1
    min = Q1 - 2*IQR
    max = Q3 + 2*IQR

    for i in range(df_new.shape[0]):
        for j in range(df_new.shape[1]):
            if df_new.iat[i, j] < min.iat[i, j] or df_new.iat[i, j] > max.iat[i, j]:
                df_new.iat[i, j] = np.nan

    # Q1 = df.quantile(0.25)
    # Q3 = df.quantile(0.75)
    # print(Q1, Q3)
    # IQR = Q3 - Q1
    # min = Q1 - 2*IQR
    # max = Q3 + 2*IQR
    # df[df<min] = np.nan
    # df[df>max] = np.nan

    # for col in df.columns:
    #     Q1 = df[col].quantile(0.25)
    #     Q3 = df[col].quantile(0.75)
    #     print(Q1, Q3)
    #     IQR = Q3 - Q1
    #     min = Q1 - 2*IQR
    #     max = Q3 + 2*IQR
    #     df[col][df[col]<min] = np.nan
    #     df[col][df[col]>max] = np.nan

    return df_new

def linear_imputation(df: pd.DataFrame, imputation_time_delta: pd.Timedelta, rsp_time: pd.Timedelta, **kw) -> pd.DataFrame:
    '''
    Linear interpolation of a data_frame

    df: data that belongs to the "data_frame" format.
    imputation_time_delta: data missing for more than consecutive imputation_time_delta will not be interpolated.
    sampling_time_delta: sampling interval.
    '''
    df_new = copy.deepcopy(df)
    for col in df_new.columns:
        # 不对启停(0,1)数据进行插值
        if col in ['onOff', 'exv1Opening']: continue
        series = df_new[col]

        # 获取空值索引
        series_nan = series[series.isna()]
        series_nan_index = series_nan.index
        if series_nan_index.empty: continue
        
        # 获取小于imputation_time_delta的空值索引
        series_imputation_list = []
        start = series_nan_index[0]
        temp = series_nan_index[0]
        end = series_nan_index[0]
        for i in range(len(series_nan_index)-1):
            end = series_nan_index[i+1]
            if (end-temp) == rsp_time:
                temp = end
            else:
                if ((temp - start) <= imputation_time_delta) and (start!=series.head(1).index and end!=series.tail(1).index):
                    series_imputation_list.append([start, temp])
                start = end
                temp = end
        if ((temp - start) <= imputation_time_delta) and (start!=series.head(1).index and end!=series.tail(1).index):
            series_imputation_list.append([start, temp])

        # 对满足imputation_time_delta的空值进行线性插值
        for imputation in series_imputation_list:
            df_new[col].loc[imputation[0]-rsp_time: imputation[1]+rsp_time] = \
                series.loc[imputation[0]-rsp_time: imputation[1]+rsp_time].interpolate(method='polynomial', order=1)
        
    return df_new






'''

def cal_missing_rate_old(data_frame, time_window, params):

    missing_rate = pd.DataFrame(data=None, columns=data_frame.columns)
    for i in range(0, (params['end_time']-params['start_time']).days//time_window):
        time1 = params['start_time'] + pd.to_timedelta(time_window*i, unit='D')
        time2 = params['start_time'] + pd.to_timedelta(time_window*(i+1), unit='D')
        for col in data_frame.columns:
            ms = 1 - data_frame[col].loc[time1:time2].count() / (params['rsp_num']*time_window*24)
            missing_rate.loc[time1, col] = ms

    return missing_rate

def plot_missing_rate_old(missing_rate, params, params_process, mark):
    
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

'''
