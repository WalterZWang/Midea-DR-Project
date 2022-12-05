# -*- encoding: utf-8 -*-
'''
@File    :   data_evaluation.py
@Time    :   2022/11/23 12:57:53
@Author  :   Zhenyu Wang 
'''
import matplotlib.pyplot as plt
from matplotlib.pylab import mpl
import numpy as np
import utility as util
import pandas as pd
import sys
import pickle
import copy
import data_processing as dp
import get_influxDB



plt.style.use('seaborn-deep')
mpl.rcParams['font.sans-serif'] = ['SimSun']     # 显示中文, {'SimHei', 'FangSong', 'SimSun'}
mpl.rcParams['axes.unicode_minus'] = False       # 显示负号
mpl.rcParams['font.size'] = 8



# start_time和end_time与get_influxDB中保持一致（415行）
start_time = pd.to_datetime('2022-05-01 00:00:00+08:00')
end_time = pd.to_datetime('2022-11-23 00:00:00+08:00')
# get_influxDB中的resample_min_interval修改了数据重采样的时间, 统一为15分钟一次, 方便比较, rsp = '15T' --> rsp_num = 4
rsp_num = 4


def cal_missing_rate1(data, time_window, **kw):

    time = []
    missing_rate = copy.deepcopy(kw)
    for key in missing_rate.keys():
        if key == 'vrf_id': continue
        missing_rate[key] = dict(zip(missing_rate[key], [[] for i in range(len(missing_rate[key]))]))
    '''
    if: kw = {'vrf_id': 'VRF_1K0V',
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
    
    for i in range(0, (end_time-start_time).days//time_window):
        time1 = start_time + pd.to_timedelta(time_window*i, unit='D')
        time2 = start_time + pd.to_timedelta(time_window*(i+1), unit='D')
        # print(time1, time2)
        time.append(time1)

        if 'blg_devSn_id' in kw.keys():
            for str in kw['blg_devSn_id']:
                if str == kw['vrf_id']:
                    missing_rate['blg_devSn_id'][str].append\
                        (1 - data.VRF_rsp[kw['vrf_id']]['meter'].loc[time1:time2]['E'].count() / (rsp_num*time_window*24))
                    continue
                missing_rate['blg_devSn_id'][str].append\
                    (1 - data.blg_meter_rsp[str].loc[time1:time2]['E'].count() / (rsp_num*time_window*24))
                
        if 'idr_data' in kw.keys():
            j = 0
            while 'idu_'+f'{j}' in data.VRF_rsp[kw['vrf_id']]:
                for str in kw['idr_data']:
                    missing_rate['idr_data'][str].append([]) 
                    missing_rate['idr_data'][str][j].append\
                        (1 - data.VRF_rsp[kw['vrf_id']]['idu_'+f'{j}'].loc[time1:time2][str].count() / (rsp_num*time_window*24))
                j = j+1

        if 'odr_data' in kw.keys():
            for str in kw['odr_data']:
                missing_rate['odr_data'][str].append\
                    (1 - data.VRF_rsp[kw['vrf_id']]['odu_129'].loc[time1:time2][str].count() / (rsp_num*time_window*24))

        if 'sys_data' in kw.keys():
            for str in kw['sys_data']:
                missing_rate['sys_data'][str].append\
                    (1 - data.VRF_rsp[kw['vrf_id']]['sys_'+kw['vrf_id'].split('_')[1]].loc[time1:time2][str].count() / (rsp_num*time_window*24))

        if 'weather_data' in kw.keys():
            for str in kw['weather_data']:
                missing_rate['weather_data'][str].append\
                    (1 - data.weather_rsp.loc[time1:time2][str].count() / (rsp_num*time_window*24))


    # plot
    i = 0
    while 'idu_'+f'{i}' in data.VRF_rsp[kw['vrf_id']]:
        plt.plot(time, missing_rate['idr_data']['roomTemp'][i], label=f'idu_{i}_'+'roomTemp', marker='D')
        i = i+1
    i = 0
    while 'idu_'+f'{i}' in data.VRF_rsp[kw['vrf_id']]:
        plt.plot(time, missing_rate['idr_data']['onOff'][i], label=f'idu_{i}_'+'onOff', marker='p')
        i = i+1

    plt.plot(time, missing_rate['blg_devSn_id']['mDev_EMeter_F2_Backup'], label='E_lightplug', marker='x')
    plt.plot(time, missing_rate['blg_devSn_id'][kw['vrf_id']], label='E_vrf', marker='x')

    plt.plot(time, missing_rate['odr_data']['t4Temp'], label='odu_t4Temp', marker='o')
    plt.plot(time, missing_rate['odr_data']['powerNeed'], label='odu_powerNeed', marker='o')
    plt.plot(time, missing_rate['sys_data']['systemQc'], label='sys_systemQc', marker='o')

    plt.plot(time, missing_rate['weather_data']['e3'], label='weather_e3', marker='*')
    plt.plot(time, missing_rate['weather_data']['e11'], label='weather_e11', marker='*')

    plt.title(kw['vrf_id']+f' Missing Rate (Per {time_window} day)')
    plt.xlabel("Date")
    plt.ylabel("Missing rate")
    plt.legend(loc = 'upper left')

    plt.gcf().set_size_inches(16, 8)
    plt.savefig(f'./results/data_evaluation/'+kw['vrf_id']+f' Missing Rate (Per {time_window} day).png', dpi=300, bbox_inches='tight', pad_inches=0.1)
    # plt.show()
    
    plt.close()
    # plt.clf()
    
    return







# information to be evaluated
data_eval = {'vrf_id': 'VRF_JSJR',
        'idr_data': ['roomTemp', 'onOff'],
        'odr_data': ['t4Temp', 'powerNeed'],
        'sys_data': ['systemQc'],
        'blg_devSn_id': ['mDev_EMeter_F2_Backup', 'VRF_JSJR'],
        'weather_data': ['e3', 'e11']
}


# # get data from infuxDB
# data,VRF_rsp, blg_meter_rsp, weather_rsp, PV_meter_rsp, PV_dev_rsp,\
#             battery_meter_rsp, battery_dev_rsp, PV_meter, PV_dev = get_influxDB.get_influxDB_main()
# print('data acquired')

# # save data
# file = open('data.pkl','wb')  
# pickle.dump(data, file)  
# file.close() 
# print('data saved')

# load data
file = open(r'C:\Users\Wang\Desktop\data.pkl','rb')  
data = pickle.load(file)  
file.close()  
print('data loaded')

# data_process与data内部属性命名不一致
# dp.DataProcess(data)内是对data的浅拷贝，process后data的子对象也被更改，所以不能修改后一起绘图
for time_window in range(1, 8, 2):
    cal_missing_rate1(data, time_window, **data_eval)
    print(f'Missing Rate (Per {time_window} day)')

# dp.DataProcess中修改了使用的utility.py的函数：util.outlier_meter --> util.outlier
# util.outlier修改了箱线图的分位点参数quantile
# data_process = dp.DataProcess(data)
# for time_window in range(1, 8, 2):
    # cal_missing_rate2(data_process, time_window)
    # print(f'Missing Rate (Per {time_window} day)(process)')
