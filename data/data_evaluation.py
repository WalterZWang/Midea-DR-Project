# -*- encoding: utf-8 -*-
'''
@File    :   data_evaluation.py
@Time    :   2022/11/23 12:57:53
@Author  :   Zhenyu Wang 
'''
'''
This module is used to evaluate data by missing rate.
The data format comes from "get_influxDB.py".
'''

import matplotlib.pyplot as plt
from matplotlib.pylab import mpl
import numpy as np
import utility as util
import pandas as pd
import sys
import pickle
import copy
import get_influxDB

plt.style.use('seaborn-deep')
mpl.rcParams['axes.unicode_minus'] = False
mpl.rcParams['font.size'] = 8


def cal_missing_rate(data, time_window, eval, param):
    '''
    Calculates the missing rate of the specified variable in the data

    data: data format comes from "get_influxDB.py".
    time_window: specifies the size of the time window, the minimum is 1(day).
    eval: specifies the variable to be evaluated.
    param: other parameters, like time and rsp_num per hour.
    '''

    date = []
    missing_rate = copy.deepcopy(eval)
    for key in missing_rate.keys():
        if key == 'vrf_id': continue
        missing_rate[key] = dict(zip(missing_rate[key], [[] for i in range(len(missing_rate[key]))]))
    '''
    if: eval = {'vrf_id': 'VRF_1K0V',
            'idr_data': ['roomTemp', 'onOff'],
            'odr_data': ['t4Temp', 'powerNeed'],
            'sys_data': ['systemQc'],
            'blg_devSn_id': ['mDev_EMeter_F2_Backup', 'VRF_1K0V'],
            'weather_data': ['e3', 'e11']
        }
        missing_rate = {'vrf_id': 'VRF_1K0V',
            'idr_data': {'roomTemp': [], 'onOff': []},
            'odr_data': {'t4Temp': [], 'powerNeed': []},
            'sys_data': {'systemQc': []},
            'blg_devSn_id': {'mDev_EMeter_F2_Backup': [], 'VRF_1K0V': []},
            'weather_data': {'e3': [], 'e11': []}
        }
    '''
    
    for i in range(0, (param['end_time']-param['start_time']).days//time_window):
        time1 = param['start_time'] + pd.to_timedelta(time_window*i, unit='D')
        time2 = param['start_time'] + pd.to_timedelta(time_window*(i+1), unit='D')
        # print(time1, time2)
        date.append(time1)

        for key in eval.keys():
            if key == 'idr_data':        
                j = 0
                while 'idu_'+f'{j}' in data.VRF_rsp[eval['vrf_id']]:
                    for str in eval['idr_data']:
                        if i == 0: missing_rate['idr_data'][str].append([]) 
                        missing_rate['idr_data'][str][j].append\
                            (1 - data.VRF_rsp[eval['vrf_id']]['idu_'+f'{j}'].loc[time1:time2][str].count() / (param['rsp_num']*time_window*24))
                    j = j+1

            if key == 'odr_data':
                for str in eval['odr_data']:
                    missing_rate['odr_data'][str].append\
                        (1 - data.VRF_rsp[eval['vrf_id']]['odu_129'].loc[time1:time2][str].count() / (param['rsp_num']*time_window*24))

            if key == 'sys_data':
                for str in eval['sys_data']:
                    missing_rate['sys_data'][str].append\
                        (1 - data.VRF_rsp[eval['vrf_id']]['sys_'+eval['vrf_id'].split('_')[1]].loc[time1:time2][str].count() / (param['rsp_num']*time_window*24))

            if key == 'weather_data':
                for str in eval['weather_data']:
                    missing_rate['weather_data'][str].append\
                        (1 - data.weather_rsp.loc[time1:time2][str].count() / (param['rsp_num']*time_window*24))

            if key == 'blg_devSn_id':
                for str in eval['blg_devSn_id']:
                    if str == eval['vrf_id']:
                        missing_rate['blg_devSn_id'][str].append\
                            (1 - data.VRF_rsp[eval['vrf_id']]['meter'].loc[time1:time2]['E'].count() / (param['rsp_num']*time_window*24))
                        continue
                    missing_rate['blg_devSn_id'][str].append\
                        (1 - data.blg_meter_rsp[str].loc[time1:time2]['E'].count() / (param['rsp_num']*time_window*24))

    return missing_rate, date

def plot_missing_rate(missing_rate, date, time_window, mark):
    '''
    Plot missing rate over time
    '''

    for i in range(0, len(missing_rate['idr_data']['roomTemp'])):
        plt.plot(date, missing_rate['idr_data']['roomTemp'][i], label=f'idu_{i}_'+'roomTemp', marker='D')
    for i in range(0, len(missing_rate['idr_data']['onOff'])):
        plt.plot(date, missing_rate['idr_data']['onOff'][i], label=f'idu_{i}_'+'onOff', marker='p')

    plt.plot(date, missing_rate['blg_devSn_id']['mDev_EMeter_F2_Backup'], label='E_lightplug', marker='x')
    plt.plot(date, missing_rate['blg_devSn_id'][missing_rate['vrf_id']], label='E_vrf', marker='x')

    plt.plot(date, missing_rate['odr_data']['t4Temp'], label='odu_t4Temp', marker='o')
    plt.plot(date, missing_rate['odr_data']['powerNeed'], label='odu_powerNeed', marker='o')
    plt.plot(date, missing_rate['sys_data']['systemQc'], label='sys_systemQc', marker='o')

    plt.plot(date, missing_rate['weather_data']['e3'], label='weather_e3', marker='*')
    plt.plot(date, missing_rate['weather_data']['e11'], label='weather_e11', marker='*')

    plt.title(missing_rate['vrf_id']+f' Missing Rate (Per {time_window} day) '+mark)
    plt.xlabel("Date")
    plt.ylabel("Missing rate")
    plt.legend(loc = 'upper left')

    plt.gcf().set_size_inches(16, 8)
    plt.savefig(f'./results/data_evaluation/'+missing_rate['vrf_id']+f' Missing Rate (Per {time_window} day) '+mark+'.png', dpi=300, bbox_inches='tight', pad_inches=0.1)
    # plt.show()
    
    plt.close()
    # plt.clf()

    print(missing_rate['vrf_id'] + f' Missing Rate (Per {time_window} day) ' + mark)
    return

def remove_outlier_df(data_frame):
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

def remove_outliers(data, eval):
    '''
    Remove outliers

    data: data format comes from "get_influxDB.py".
    '''

    data_process = copy.deepcopy(data)

    data_process.weather_rsp = remove_outlier_df(data_process.weather_rsp)
    for key, value in data_process.VRF_rsp[eval['vrf_id']].items():
        data_process.VRF_rsp[eval['vrf_id']][key] = remove_outlier_df(value)
    for key, value in data_process.blg_meter_rsp.items():
        data_process.blg_meter_rsp[key] = remove_outlier_df(value)

    return data_process

def linear_imputation_df(data_frame, imputation_time_delta, sampling_time_delta):
    '''
    Linear interpolation of a data_frame

    data_frame: ata that belongs to the "data_frame" format.
    imputation_time_delta: data loss for more than consecutive imputation_time_delta will not be interpolated.
    sampling_time_delta: sampling interval (15min).
    '''

    for col in data_frame.columns:
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

def polynomial_imputation(data, eval, param):
    '''
    Polynomial interpolation (currently only linear interpolation)

    data: data format comes from "get_influxDB.py".
    '''

    data_new = copy.deepcopy(data)

    data_new.weather_rsp = \
        linear_imputation_df(data_new.weather_rsp, param['imputation_time_delta'], param['rsp_time'])
    for key, value in data_new.VRF_rsp[eval['vrf_id']].items():
        data_new.VRF_rsp[eval['vrf_id']][key] = \
            linear_imputation_df(value, param['imputation_time_delta'], param['rsp_time'])
    for key, value in data_new.blg_meter_rsp.items():
        data_new.blg_meter_rsp[key] = \
            linear_imputation_df(value, param['imputation_time_delta'], param['rsp_time'])
    
    return data_new



# # get data from ''get_infuxDB.py''
# data,VRF_rsp, blg_meter_rsp, weather_rsp, PV_meter_rsp, PV_dev_rsp,\
#             battery_meter_rsp, battery_dev_rsp, PV_meter, PV_dev = get_influxDB.get_influxDB_main()
# print('data acquired')
# # save data
# file = open('data.pkl','wb')  
# pickle.dump(data, file)  
# file.close() 
# print('data saved')

# or load local data
file = open(r'C:\Users\ADMIN\Desktop\data.pkl','rb')  
data = pickle.load(file)  
file.close()  
print('local data loaded')

# set information to be evaluated and other parameters
eval = {'vrf_id': 'VRF_1K0V',
        'idr_data': ['roomTemp', 'onOff'],
        'odr_data': ['t4Temp', 'powerNeed'],
        'sys_data': ['systemQc'],
        'blg_devSn_id': ['mDev_EMeter_F2_Backup', 'VRF_1K0V'],
        'weather_data': ['e3', 'e11']
}
param = {
    'start_time': pd.to_datetime('2022-05-01 00:00:00+08:00'),
    'end_time': pd.to_datetime('2022-11-23 00:00:00+08:00'),
    'rsp_num': 4,  # rsp = '15T' --> rsp_num = 4 times per hour
    'rsp_time': pd.Timedelta('15 minutes'),
    'imputation_time_delta': pd.Timedelta('6 hours')
}


# evaluate missing rate of data and save results
for time_window in range(1, 8, 2):
    missing_rate, date = cal_missing_rate(data, time_window, eval, param)
    plot_missing_rate(missing_rate, date, time_window, mark='origin')

data_process = remove_outliers(data, eval)
for time_window in range(1, 8, 2):
    missing_rate, date = cal_missing_rate(data_process, time_window, eval, param)
    plot_missing_rate(missing_rate, date, time_window, mark='remove_outliers')

data_new = polynomial_imputation(data_process, eval, param)
for time_window in range(1, 8, 2):
    missing_rate, date = cal_missing_rate(data_new, time_window, eval, param)
    plot_missing_rate(missing_rate, date, time_window, mark='polynomial_imputation')