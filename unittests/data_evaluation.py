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



def cal_missing_rate1(data, time_window):

        # 采样周期15min，时间窗口7天，理论采样点数rsp*7*24=672
        week = []
        missing_rate_E_light = []
        missing_rate_E_vrf = []
        for i in range(0, (end_time-start_time).days//time_window):
                time1 = start_time + pd.to_timedelta(time_window*i, unit='D')
                time2 = start_time + pd.to_timedelta(time_window*(i+1), unit='D')
                # print(time1, time2)
                week.append(time1)
                missing_rate_E_light.append(1 - data.blg_meter_rsp['mDev_EMeter_F2_Backup'].loc[time1:time2]['E'].count() / (rsp_num*time_window*24))
                missing_rate_E_vrf.append(1 - data.VRF_rsp['VRF_1K0V']['meter'].loc[time1:time2]['E'].count() / (rsp_num*time_window*24))

        missing_rate_idu = []
        for i in range(0, 7):
                missing_rate_idu.append([])
                missing_rate_idu[i].insert(0, [])
                missing_rate_idu[i].insert(1, [])
                for j in range(0, (end_time-start_time).days//time_window):
                        time1 = start_time + pd.to_timedelta(time_window*j, unit='D')
                        time2 = start_time + pd.to_timedelta(time_window*(j+1), unit='D')   
                        mr_roomTemp = 1 - data.VRF_rsp['VRF_1K0V']['idu_'+f'{i}'].loc[time1:time2]['roomTemp'].count() / (rsp_num*time_window*24)
                        mr_onOff = 1 - data.VRF_rsp['VRF_1K0V']['idu_'+f'{i}'].loc[time1:time2]['onOff'].count() / (rsp_num*time_window*24)
                        missing_rate_idu[i][0].append(mr_roomTemp)
                        missing_rate_idu[i][1].append(mr_onOff)

        missing_rate_odu = [[], []]
        for i in range(0, (end_time-start_time).days//time_window):
                time1 = start_time + pd.to_timedelta(time_window*i, unit='D')
                time2 = start_time + pd.to_timedelta(time_window*(i+1), unit='D')
                mr_t4Temp = 1 - data.VRF_rsp['VRF_1K0V']['odu_129'].loc[time1:time2]['t4Temp'].count() / (rsp_num*time_window*24)
                mr_powerNeed = 1 - data.VRF_rsp['VRF_1K0V']['odu_129'].loc[time1:time2]['powerNeed'].count() / (rsp_num*time_window*24)
                missing_rate_odu[0].append(mr_t4Temp)
                missing_rate_odu[1].append(mr_powerNeed)

        missing_rate_sys = []
        for i in range(0, (end_time-start_time).days//time_window):
                time1 = start_time + pd.to_timedelta(time_window*i, unit='D')
                time2 = start_time + pd.to_timedelta(time_window*(i+1), unit='D')
                missing_rate_sys.append(1 - data.VRF_rsp['VRF_1K0V']['sys_1K0V'].loc[time1:time2]['systemQc'].count() / (rsp_num*time_window*24))


        missing_rate_weather = [[], []]
        for i in range(0, (end_time-start_time).days//time_window):
                time1 = start_time + pd.to_timedelta(time_window*i, unit='D')
                time2 = start_time + pd.to_timedelta(time_window*(i+1), unit='D')
                mr_e3 = 1 - data.weather_rsp.loc[time1:time2]['e3'].count() / (rsp_num*time_window*24)
                mr_e11 = 1 - data.weather_rsp.loc[time1:time2]['e11'].count() / (rsp_num*time_window*24)
                missing_rate_weather[0].append(mr_e3)
                missing_rate_weather[1].append(mr_e11)


        # plot
        for i in range(0, 7):
                plt.plot(week, missing_rate_idu[i][0], label=f'idu_{i}_'+'roomTemp', marker='D')
        for i in range(0, 7):
                plt.plot(week, missing_rate_idu[i][1], label=f'idu_{i}_'+'onOff', marker='p')

        plt.plot(week, missing_rate_E_light, label='E_light', marker='x')
        plt.plot(week, missing_rate_E_vrf, label='E_vrf', marker='x')

        plt.plot(week, missing_rate_odu[0], label='odu_t4Temp', marker='o')
        plt.plot(week, missing_rate_odu[1], label='odu_powerNeed', marker='o')
        plt.plot(week, missing_rate_sys, label='sys_systemQc', marker='o')

        plt.plot(week, missing_rate_weather[0], label='weather_e3', marker='*')
        plt.plot(week, missing_rate_weather[1], label='weather_e11', marker='*')

        plt.title(f'Missing Rate (Per {time_window} day)')
        plt.xlabel("Date")
        plt.ylabel("Missing rate")
        plt.legend(loc = 'upper left')

        plt.gcf().set_size_inches(16, 8)
        plt.savefig(f'./results/data_evaluation/Missing Rate (Per {time_window} day).png', dpi=300, bbox_inches='tight', pad_inches=0.1)
        # plt.show()
        
        plt.close()
        # plt.clf()
        
        return

def cal_missing_rate2(data_process, time_window):

        # 采样周期15min，时间窗口7天，理论采样点数rsp_num*7*24=672
        week = []
        missing_rate_E_light = []
        missing_rate_E_vrf = []
        for i in range(0, (end_time-start_time).days//time_window):
                time1 = start_time + pd.to_timedelta(time_window*i, unit='D')
                time2 = start_time + pd.to_timedelta(time_window*(i+1), unit='D')
                # print(time1, time2)
                week.append(time1)
                missing_rate_E_light.append(1 - data_process.blg_meter_pro['mDev_EMeter_F2_Backup'].loc[time1:time2]['E'].count() / (rsp_num*time_window*24))
                missing_rate_E_vrf.append(1 - data_process.VRF_data_pro['VRF_1K0V']['meter'].loc[time1:time2]['E'].count() / (rsp_num*time_window*24))

        missing_rate_idu = []
        for i in range(0, 7):
                missing_rate_idu.append([])
                missing_rate_idu[i].insert(0, [])
                missing_rate_idu[i].insert(1, [])
                for j in range(0, (end_time-start_time).days//time_window):
                        time1 = start_time + pd.to_timedelta(time_window*j, unit='D')
                        time2 = start_time + pd.to_timedelta(time_window*(j+1), unit='D')   
                        mr_roomTemp = 1 - data_process.VRF_data_pro['VRF_1K0V']['idu_'+f'{i}'].loc[time1:time2]['roomTemp'].count() / (rsp_num*time_window*24)
                        mr_onOff = 1 - data_process.VRF_data_pro['VRF_1K0V']['idu_'+f'{i}'].loc[time1:time2]['onOff'].count() / (rsp_num*time_window*24)
                        missing_rate_idu[i][0].append(mr_roomTemp)
                        missing_rate_idu[i][1].append(mr_onOff)

        missing_rate_odu = [[], []]
        for i in range(0, (end_time-start_time).days//time_window):
                time1 = start_time + pd.to_timedelta(time_window*i, unit='D')
                time2 = start_time + pd.to_timedelta(time_window*(i+1), unit='D')
                mr_t4Temp = 1 - data_process.VRF_data_pro['VRF_1K0V']['odu_129'].loc[time1:time2]['t4Temp'].count() / (rsp_num*time_window*24)
                mr_powerNeed = 1 - data_process.VRF_data_pro['VRF_1K0V']['odu_129'].loc[time1:time2]['powerNeed'].count() / (rsp_num*time_window*24)
                missing_rate_odu[0].append(mr_t4Temp)
                missing_rate_odu[1].append(mr_powerNeed)

        missing_rate_sys = []
        for i in range(0, (end_time-start_time).days//time_window):
                time1 = start_time + pd.to_timedelta(time_window*i, unit='D')
                time2 = start_time + pd.to_timedelta(time_window*(i+1), unit='D')
                missing_rate_sys.append(1 - data_process.VRF_data_pro['VRF_1K0V']['sys_1K0V'].loc[time1:time2]['systemQc'].count() / (rsp_num*time_window*24))


        missing_rate_weather = [[], []]
        for i in range(0, (end_time-start_time).days//time_window):
                time1 = start_time + pd.to_timedelta(time_window*i, unit='D')
                time2 = start_time + pd.to_timedelta(time_window*(i+1), unit='D')
                mr_e3 = 1 - data_process.weather_pro.loc[time1:time2]['e3'].count() / (rsp_num*time_window*24)
                mr_e11 = 1 - data_process.weather_pro.loc[time1:time2]['e11'].count() / (rsp_num*time_window*24)
                missing_rate_weather[0].append(mr_e3)
                missing_rate_weather[1].append(mr_e11)



        # plot
        for i in range(0, 7):
                plt.plot(week, missing_rate_idu[i][0], label=f'idu_{i}_'+'roomTemp', marker='D')
        for i in range(0, 7):
                plt.plot(week, missing_rate_idu[i][1], label=f'idu_{i}_'+'onOff', marker='p')

        plt.plot(week, missing_rate_E_light, label='E_light', marker='x')
        plt.plot(week, missing_rate_E_vrf, label='E_vrf', marker='x')

        plt.plot(week, missing_rate_odu[0], label='odu_t4Temp', marker='o')
        plt.plot(week, missing_rate_odu[1], label='odu_powerNeed', marker='o')
        plt.plot(week, missing_rate_sys, label='sys_systemQc', marker='o')

        plt.plot(week, missing_rate_weather[0], label='weather_e3', marker='*')
        plt.plot(week, missing_rate_weather[1], label='weather_e11', marker='*')

        plt.title(f'Missing Rate (Per {time_window} day)(process)')
        plt.xlabel("Date")
        plt.ylabel("Missing rate")
        plt.legend(loc = 'upper left')

        plt.gcf().set_size_inches(16, 8)
        plt.savefig(f'./results/data_evaluation/Missing Rate (Per {time_window} day)(process).png', dpi=300, bbox_inches='tight', pad_inches=0.1)
        # plt.show()
        
        plt.close()
        # plt.clf()

        return



# get data from infuxDB
data,VRF_rsp, blg_meter_rsp, weather_rsp, PV_meter_rsp, PV_dev_rsp,\
            battery_meter_rsp, battery_dev_rsp, PV_meter, PV_dev = get_influxDB.get_influxDB_main()
print('data acquired')
# save data
file = open('data.pkl','wb')  
pickle.dump(data, file)  
file.close() 
print('data saved')

# # load data
# file = open('data.pkl','rb')  
# data = pickle.load(file)  
# file.close()  
# print('data loaded')

# data_process与data内部属性命名不一致
# dp.DataProcess(data)内是对data的浅拷贝，process后data的子对象也被更改，所以不能修改后一起绘图
for time_window in range(1, 8, 2):
        cal_missing_rate1(data, time_window)
        print(f'Missing Rate (Per {time_window} day)')

# dp.DataProcess中修改了使用的utility.py的函数：util.outlier_meter --> util.outlier
# util.outlier修改了箱线图的分位点参数quantile
data_process = dp.DataProcess(data)
for time_window in range(1, 8, 2):
        cal_missing_rate2(data_process, time_window)
        print(f'Missing Rate (Per {time_window} day)(process)')
