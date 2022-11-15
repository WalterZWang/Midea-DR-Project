# -*- coding: utf-8 -*-
"""
Created on Sun Jun 19 23:31:20 2022

@author: Mingyue Guo
"""

#%% import
import pandas as pd
import numpy as np
import os
import matplotlib.pyplot as plt
import seaborn as sns
import joypy
sns.set_style('darkgrid', {'font.sans-serif':['SimHei', 'Arial']})
plt.rcParams['axes.unicode_minus']=False
# sns.set(palette='pastel')
from pytz import timezone
from sklearn.metrics import r2_score as R 
import missingno as msno

#%% functions
class Visulize():
    cmap_seq  = 'YlGn'
    cmap_div = 'RdBu'
    cmap_qua = 'tab10'
    def __init__(self, title = None, xlabel = None, ylabel = None):
        self.title = title
        self.xlabel = xlabel
        self.ylabel = ylabel
    ''''
    legend_type: int, 0 for no legend, 1 for legend inside of box, 2 for legend outside of box
    '''
    def settings(self, legend_type = 1):
        if self.xlabel != None:
            plt.xlabel(self.xlabel)
        if self.ylabel != None:
            plt.ylabel(self.ylabel)
        if legend_type == 1:
            plt.legend()
        elif legend_type == 2:
            plt.legend(bbox_to_anchor=(1, 0), loc = 3, borderaxespad = 0)
        if self.title != None:
            plt.title(self.title)
        plt.show()
            
    def norm_boxplot(self, df, legend_type = 1):
        df = df.copy()
        sns.boxplot( data = df, 
                       palette = Visulize.cmap_div
                      )
        self.settings(legend_type)
        
    def norm_scatterplot(self, x, y, alpha, legend_type = 1):
        plt.scatter(x, y, alpha = alpha)
        self.settings(legend_type)


        
    def norm_heatmap(self, df, cbar_name, legend_type = 1):
        sns.heatmap(df
                    , cmap=Visulize.cmap_seq
                    , cbar_kws={'label': cbar_name, 
                   # 'orientation': 'horizontal',#color bar的方向设置，默认为'vertical'，可水平显示'horizontal'
                   # "ticks":np.arange(4.5,8,0.5),#color bar中刻度值范围和间隔
                   # "format":"%.3f",#格式化输出color bar中刻度值
                   # "pad":0.15,#color bar与热图之间距离，距离变大热图会被压缩
                    },
                    )
        self.settings(legend_type)

        

def change_timezone(date_time):
    tz = timezone('Asia/Shanghai')
    utc = timezone('UTC')
    return date_time.replace(tzinfo=utc).astimezone(tz)


def eda_all(weather):
    # 先看一下数据质量
    #weather
    #Missing data: May 6 10:00 to May 7 10:00
    for i in weather['result'].columns:
        try:
            weather['result'].plot()
            plt.ylabel(i)
            plt.show()
        except:
            pass
        
    item = weather['result']
    # item = item[item['onOff'] == 1]
    item['Date'] = item.index.map(lambda t: t.date())
    item['Time'] = item.index.map(lambda t: t.time().hour)
    item_pivot = pd.pivot_table(item, values='e3', index='Date', columns='Time')
    #roomTemp_pivot.T.plot(legend=False, figsize=(15,5), color='k', alpha=0.1, xticks=np.arange(0, 86400, 10800))
    # item_pivot.T.plot(legend=False)
    # plt.title('outdoor temp')
    # plt.xlabel("Hour of Day")
    # plt.ylabel("e3")
    
    # p = sns.boxplot( data = item_pivot, 
    #                # order = ['on','off'], 
    #                palette = Visulize.cmap_div
    #               )
    Visulize(title = 'Outdoor Temp Distribution'
             , ylabel = 'e3'
             , xlabel = "Hour of Day"
             ).norm_boxplot(item_pivot)
    # #VRF
    # #VRF_each outdoor: April 28, 10:00 to April 28, 15:50
    # for key,item in VRF_each.items():
    #    for i in VRF_each[key].columns:
    #         try:
    #             VRF_each[key][i].plot()
    #             plt.ylabel(i)
    #             plt.show()
    #         except:
    #             pass

# VRF_each['indoor']['roomTemp'][0:24].plot(alpha=0.5)
# VRF_each['indoor']['tempSetting'][0:24].plot(alpha=0.5)
# # VRF_each['outdoor']['t5Temp'].plot(alpha=0.5)
# plt.legend()
# plt.ylabel("temp")

def meter_decompose(meter):
    meter_df = meter['result'].copy()
    meter_groups =  meter_df.groupby('devSn')
    submeters = {}
    for name,group in meter_groups:
        submeters[name] = group.copy().resample('15T').mean()
        submeters[name]['E_diff'] = submeters[name]['E'].diff()
        submeters[name]['Evar_diff'] = group['Evar'].diff()
    return submeters

def meter_eda(meter_df):
    meter_df = pd.read_excel(r'D:\project\Midea\data\0620-0626西区数据\西区示范工程电表数据.xlsx'
                             , parse_dates = ['time'])
    meter_df.set_index('time', inplace = True)
    meter_df.index = meter_df.index.map(lambda x: change_timezone(x))

    # meter_df = meter['result'].copy()
    msno.matrix(meter_df, labels=True)
            
    meter_groups =  meter_df.groupby('devSn')
    submeters = {}
    for name,group in meter_groups:
        submeters[name] = group
        submeters[name] = group.copy().resample('15T').mean()
        submeters[name]['E_diff'] = submeters[name]['E'].diff()
        submeters[name]['Evar_diff'] = submeters[name]['Evar'].diff()

    
    #看一下哪个表的数据没有提供
    meter_meta = pd.read_excel(r'D:\project\Midea\data\0620-0626西区数据\能耗表说明.xlsx', skiprows = 1)
    all_submeters = meter_meta['设备SN']
    missing_meter = set(all_submeters) - set(submeters.keys())
    
    
    #missing data
    for key,item in submeters.items():
        for co in item.columns:
            missing_data(key, item)
            
    # 比较关心的某几个表
    floor1 = ['mDev_EMeter_F1_IDU'
            ,'mDev_EMeter_F1_IDU_1'
            ,'mDev_EMeter_F1_IDU_2'
            ,'mDev_EMeter_F1_Hall'
            ,'mDev_EMeter_F1_Guard'
            ,'mDev_EMeter_Roof_PV'
            ]
    
    floor2 = ['mDev_EMeter_F2_FAU'
                , 'mDev_EMeter_F2_IDU'
                , 'mDev_EMeter_F2_Backup'
                , 'mDev_EMeter_Power_1'
                ]
    
    floor3 = [ 'mDev_EMeter_Power_3'
            ,'mDev_EMeter_Power_2'
            ,'mDev_EMeter_F3_Plug'
            ,'mDev_EMeter_F3_Toilet'
            ,'mDev_EMeter_F3_IDU'
            ,'mDev_EMeter_F3_FAU']
    
    recover = ['mDev_EMeter_HeatRecovery_WaterModule'
            ,'mDev_EMeter_HeatRecovery_RecyclePump'
            ]

    
    vrfs = ['mDev_EMeter_Roof_MDV_5'
            ,'mDev_EMeter_Roof_MDV_7'
            ,'mDev_EMeter_Roof_MDV_4'
            ,'mDev_EMeter_Roof_MDV_10'
            ,'mDev_EMeter_Roof_MDV_6'
            ,'mDev_EMeter_Roof_Backup_1'
            ,'mDev_EMeter_Roof_MDV_3'
            ,'mDev_EMeter_Roof_Elevator'
            ,'mDev_EMeter_Roof_MDV_1'
            ,'mDev_EMeter_Roof_MDV_2'
            ,'mDev_EMeter_Roof_Backup_2'
            ,'mDev_EMeter_Roof_MDV_6_New'
            ,'mDev_EMeter_Roof_MDV_7_New'
            ,'mDev_EMeter_Roof_Backup_3'
            ,'mDev_EMeter_Roof_Mobile'
            ,'mDev_EMeter_Roof_MDV_9'
            ,'mDev_EMeter_Roof_2'
            ,'mDev_EMeter_Roof_MDV_8'
            ,'mDev_EMeter_Roof_NEW_1_2'
            ,'mDev_EMeter_Roof_NEW_3_4'
            ,'mDev_EMeter_Roof_NEW_5'
            ,'mDev_EMeter_Roof_FAN_NEW'
            ]

    vrf_2F = [ 'mDev_EMeter_Roof_MDV_8'
              ,'mDev_EMeter_Roof_MDV_1'
              ,'mDev_EMeter_Roof_MDV_9'
              ,'mDev_EMeter_Roof_MDV_3'
              ,'mDev_EMeter_Roof_MDV_10'
              ,'mDev_EMeter_Roof_MDV_7'
              ,'mDev_EMeter_Roof_MDV_6'
            ]
    
    # xlabel的设备
    def meter_group(meter_group):
        for submeter_name in meter_group:
            fig, ax1 = plt.subplots()
            ax2 = ax1.twinx()    
            ax1.plot(submeters[submeter_name].index,submeters[submeter_name]['E']
                      ,color='#94B49F', label = 'E')
            ax2.plot(submeters[submeter_name].index,submeters[submeter_name]['Evar']
                      ,color='#ECB390', linestyle = '--', label = 'Evar')
            ax1.set_xlabel('Time')
            fig.autofmt_xdate(rotation=45)
            ax1.set_ylabel('E')
            ax2.set_ylabel('Evar')
            plt.title(submeter_name)
            fig.legend()
            plt.show()
        
    def meter_group_E(meter_group):
        y_co1 = 'E'
        y_co2 = 'Evar'
        for submeter_name in meter_group:

            fig, ax1 = plt.subplots()
            ax2 = ax1.twinx()    
            ax1.plot(submeters[submeter_name].index,submeters[submeter_name][y_co1]
                      ,color='#94B49F', label = y_co1)
            ax2.plot(submeters[submeter_name].index,submeters[submeter_name][y_co2]
                      ,color='#ECB390', linestyle = '--', label = y_co2)
            ax1.set_xlabel('Time')
            ax1.set_ylabel(y_co1)
            ax2.set_ylabel(y_co2)
            fig.autofmt_xdate(rotation=45)
            plt.title(submeter_name)
            fig.legend()
            plt.show()
    
    light_plug = [ 'mDev_EMeter_F2_IDU'
            # ,'mDev_EMeter_Power_2'
            # ,'mDev_EMeter_F3_Plug'
            # ,'mDev_EMeter_Power_1'
            ]

    for co in light_plug:
        (submeters[co]['E_diff'] * 1000 / 0.25).plot()
        (submeters[co]['P'] * 1000).plot()
        # (submeters[co]['Evar_diff'] * 1000).plot()
        plt.ylabel('Power / W')
        plt.title(co)
        plt.legend()
        plt.show()
    
def weather_eda(weather_df):
    # weather_df = weather['result'].copy()
    # sns.heatmap(weather_df,cmap= Visulize().cmap_seq)
    msno.matrix(weather_df, labels=True)


def missing_data(item_name, item):
    msno.matrix(item, labels=True)
    plt.title(item_name, fontsize=40)
    plt.show()
    msno.bar(item, labels=True)
    plt.title(item_name, fontsize=40)




def system_eda(VRF_name, VRF_each_sys):
    if VRF_each_sys.shape[0] == 0:
        return '********No data in system sheet********'
    
    for co in VRF_each_sys.columns:
        if 'Power' in co:
            VRF_each_sys[co].plot(alpha = 0.5)
    Visulize(title = VRF_name+' Power', ylabel = 'Power / W').settings(legend_type = 2)
    
    for co in VRF_each_sys.columns:
        if 'Meter' in co:
            VRF_each_sys[co].plot(alpha = 0.5)
    Visulize(title = VRF_name+' Meter', ylabel = 'Meter / kWh').settings(legend_type = 2)

    #hist
    colors = ['#791E94','#58C9B9','#519D9E']
    fig,axs = joypy.joyplot( VRF_each_sys
                            , column = ['outdoor0Power', 'outdoor1Power','outdoor2Power']
                            ,fill=True
                            ,legend=True
                            ,alpha=.8
                              ,range_style='own'
                              ,xlabelsize=22,ylabelsize=22
                              ,grid='both'
                              , linewidth=.8
                              ,linecolor='k'
                              , figsize=(12,6)
                              , hist = True
                              #,color=colors,
                              ,overlap = 0
                              )
    label_dic = {'family': 'SimHei',
             'weight': 'normal',
             'size': 20,
             }
    plt.xlabel(VRF_name + 'Power / W', label_dic)
    plt.show()
    



def outdoor_eda(VRF_name, VRF_each_outdoor_5t, VRF_each_outdoor, VRF_each_sys,VRF_each_indoor_5t):
    for key in VRF_each_outdoor.keys():
        VRF_each_otd = VRF_each_outdoor[key].copy()
        VRF_each_otd_5t = VRF_each_outdoor_5t[key].copy()
        # TODO temparary
        VRF_each_otd['powerNeed'] = 0
        VRF_each_otd.loc[VRF_each_otd['compressor1Frequency'] > 0, 'powerNeed'] = 1
        VRF_each_otd_5t['powerNeed'] = 0
        VRF_each_otd_5t.loc[VRF_each_otd_5t['compressor1Frequency'] > 0, 'powerNeed'] = 1
        # analysis_co = [
        #     #'nid',
        #     'powerNeed',
        #     #'errorCode',
        #     'compressor1Frequency',
        #        # 'compressor2Frequency', 
        #        'compressor1Electricity',
        #        # 'compressor2Electricity', 
        #        # 'alternatingVoltage', 'directVoltage1',
        #        # 'directVoltage2', 
        #        # 't3bTemp',
        #        't3Temp', 't4Temp',
        #        #  't5Temp',
        #        # 'inletT6ATemp', 'outletT6BTemp', 't8Temp', 't9Temp', 'tgTemp', 'tLTemp',
        #        # 'refrigerantRadiatingTemp',
        #        #'radiatorTemp', 'radiatorTemp2',
        #        # 'dischargeTemp1', 'dischargeTemp2', 'superHeatTemp',
        #        # 'SV1',
        #        #'SV2',
        #        #'SV3', 'SV4', 'SV5', 'SV6', 'SV7', 'SV8', 'SV8B', 'SV9', 'ST1', 'ST2',
        #        #'ST3',
        #        'exv1Opening',
        #        # 'exv2Opening', 'exv3Opening', 'highPressure',
        #        'lowPressure',
        #        #'Date', 'Hour'
        #        ]
        # plt.matshow(VRF_each_otd_timeind[analysis_co].corr(method = 'pearson'))
        # plt.xlabel('features')
        # plt.title('pearson')
        # scale_ls = range(len(analysis_co))
        # plt.colorbar()
        # plt.xticks(scale_ls,analysis_co, rotation = 90)
        # plt.yticks(scale_ls,analysis_co)
        # plt.savefig(r'D:\project\media\data\corr.png',dpi = 400, bbox_inches = 'tight')
        # plt.show()
        # pivot_values = ['compressor1Electricity', 't4Temp']
        pivot_values = ['compressor1Electricity']

        for co in pivot_values:
            VRF_each_otd['Date'] = VRF_each_otd.index.date
            VRF_each_otd['Hour'] = VRF_each_otd.index.hour
            pivot_otd = pd.pivot_table(VRF_each_otd, values = co, index = 'Date', columns = "Hour")
            # pivot_otd.T.plot(alpha = 0.3, legend = False)
            Visulize(title = VRF_name + ': Houly Distribution'
                     , xlabel = 'Hour of Day'
                     , ylabel = co
                     ).norm_boxplot(pivot_otd, legend_type = 0)
        
        # TODO relation of power and indoorTemp
        plt.scatter(VRF_each_otd['t4Temp'], VRF_each_otd['compressor1Frequency']
                    ,color='cornflowerblue', alpha = 0.5,label='original values')

        plt.xlabel('t4Temp')
        plt.ylabel('compressor1Frequency')
        plt.title('VRF_each')
        plt.show()
        
        VRF_each_otd.loc[~(VRF_each_otd['powerNeed'] == 0), 't3Temp'].reset_index()['t3Temp'].plot(alpha = 0.5)
        VRF_each_otd.loc[~(VRF_each_otd['powerNeed'] == 0),'t4Temp'].reset_index()['t4Temp'].plot(alpha = 0.5)
        plt.title(VRF_name + ": " + key.split('/')[-1] + ' Temp')
        plt.ylabel('Temperature')
        plt.xlabel('Timestamp')
        plt.legend()
        plt.show()

        # VRF_each_otd['compressor1Frequency'].plot(alpha = 0.5)
        VRF_each_otd['compressor1Electricity'].plot(alpha = 0.5)
        plt.ylabel(key.split('/')[-1] )
        plt.legend()
        plt.show()
        
        plt.scatter(VRF_each_otd['compressor1Frequency'], VRF_each_otd['compressor1Electricity']
                    ,color='cornflowerblue', alpha = 0.5,label='original values')
                    #,color='#1f77b4', alpha = 0.3,label='original values')
        plt.xlabel('compressor1Frequency')
        plt.ylabel('compressor1Electricity')
        parameter = np.polyfit(VRF_each_otd['compressor1Frequency'], VRF_each_otd['compressor1Electricity'], 1)
        p = np.poly1d(parameter)
        plt.scatter(VRF_each_otd['compressor1Frequency'], p(VRF_each_otd['compressor1Frequency'])
                    , color='burlywood', alpha = 0.5, label='polyfit values', s=10)
                    #, color='#ff7f0e', alpha = 0.3, label='polyfit values', s=10)
                    
        r_score = R(VRF_each_otd['compressor1Electricity'], p(VRF_each_otd['compressor1Frequency']))
        plt.title('r score is {}'.format(r_score))
        plt.show()
        # 

    # outdoor ambient weather
    # weather_5t = weather['result'].copy().resample('5T').mean()
    # weather_compare =  {}
    # weather_diff = pd.DataFrame()

    # for key,item in VRF_each_outdoor_5t.items():
    #     weather_compare[key] = pd.DataFrame()
    #     weather_compare[key] = item.copy()
    #     weather_compare[key]['e3'] = weather_5t['e3']
    #     weather_compare[key]['e3 - t4Temp'] = weather_compare[key]['e3'] - weather_compare[key]['t4Temp']
    #     weather_compare[key]['onOff'] = None
    #     weather_compare[key].loc[weather_compare[key]['powerNeed'] == 0, 'onOff'] = 'off'
    #     weather_compare[key].loc[weather_compare[key]['powerNeed'] == 100, 'onOff'] = 'on'
    #     weather_compare[key]['nid'] = key.split('/')[1][-4:] + "/" + key.split('/')[-1]
    #     weather_diff = pd.concat([weather_diff, weather_compare[key]])
    #     ## lmplot
    #     gridobj = sns.lmplot(x='e3' 
    #                   , y='t4Temp' 
    #                   , hue='onOff'
    #                   , data= weather_compare[key]
    #                     , height=8 
    #                     , aspect=1.5  # long =aspect * height
    #                    , palette='tab10'
    #                   , legend= False
    #                   , scatter_kws=dict(s=60, linewidths=.7, alpha = 0.2))
    #     x = np.arange(gridobj.facet_axis(0,0).get_xlim()[0],gridobj.facet_axis(0,0).get_xlim()[1],1)
    #     plt.plot(x,x, color = '#4E944F', linestyle = '-', label = 'y = x')
    #     plt.legend(prop={'size': 20})
    #     plt.xticks(fontsize=20)
    #     plt.yticks(fontsize=20)
    #     label_dic = {'family': 'SimHei',
    #              'weight': 'normal',
    #              'size': 20,
    #              }
    #     plt.xlabel('e3', label_dic)
    #     plt.ylabel('t4Temp', label_dic)
    #     plt.title(VRF_name + ': DryT measured by weather station and unit {}'.format(key.split('/')[-1])
    #               , label_dic)
    #     plt.show()
        
    # ## analysis difference
    # if len(weather_diff['nid'].unique()) > 1: 
    #     sns.violinplot(x = "onOff",
    #                    y = "e3 - t4Temp",
    #                    hue = "nid",
    #                    data = weather_diff, 
    #                    order = ['on','off'], 
    #                    scale = 'count', 
    #                    split = True, 
    #                    palette = Visulize.cmap_div 
    #                   )
    #     plt.legend()
    # else:
    #     sns.violinplot(x = "onOff",
    #                    y = "e3 - t4Temp",
    #                    # hue = "nid",
    #                    data = weather_diff, 
    #                    order = ['on','off'], 
    #                    scale = 'count', 
    #                    split = False, 
    #                    palette = Visulize.cmap_div 
    #                   )
    # plt.title(VRF_name + ': Difference of DryT')
    # plt.show()

    
    #Power decomposition
    VRF_each_otd_cal = {}
    for key,item in VRF_each_outdoor_5t.items():
        VRF_each_otd_cal[key] = item.copy()
        # VRF_each_otd_cal[key]['compressor1DirectPower'] = item['compressor1Electricity'] * item['directVoltage1']
        # VRF_each_otd_cal[key]['compressor2DirectPower'] = item['compressor2Electricity'] * item['directVoltage2']
        # TODO 还需乘上功率因数
        # VRF_each_otd_cal[key]['compressorCalculatedPower'] = item['compressor1Electricity'] * item['alternatingVoltage'] * 1.732
        # VRF_each_otd_cal[key]['deltaIOCondensingTemp'] =  item['t8Temp'] -  item['tLTemp']
        # VRF_each_otd_cal[key]['deltaCondEvapTemp'] =  item['t8Temp'] -  item['tgTemp']
        VRF_each_otd_cal[key]['outdoor0Power'] =  VRF_each_sys['outdoor0Power']
        VRF_each_otd_cal[key]['outdoor1Power'] =  VRF_each_sys['outdoor1Power']
        VRF_each_otd_cal[key]['outdoor2Power'] =  VRF_each_sys['outdoor2Power']

        # for co in VRF_each_otd_cal[key].columns:
        #     VRF_each_otd_cal[key][co].plot( alpha = 0.3)
        #     plt.ylabel(co)
        #     plt.title(key)
        #     plt.show()
            
    # (default ourdoor0 is 129, outdoor2 is 130)
        # if '129' in key:
        #     VRF_each_otd_cal[key]['fanOutdoorCaculatedPower'] =  VRF_each_sys['outdoor0Power']/100 - VRF_each_otd_cal[key]['compressor1DirectPower'] 
        # elif '130' in key:
        #     VRF_each_otd_cal[key]['fanOutdoorCaculatedPower'] =  VRF_each_sys['outdoor1Power']/100- VRF_each_otd_cal[key]['compressor1DirectPower'] 
        # VRF_each_otd_cal[key]['fanOutdoorCaculatedPower'].plot()
        # plt.title(VRF_name + ": " + key.split('/')[-1] + " fanPower")
        # plt.ylabel('fanOutdoorCaculatedPower')
        # plt.show()
        
        
    # regression again
    # for key,item in VRF_each_otd_cal.items():
    #     item_on = VRF_each_otd_cal[key].copy()[~(VRF_each_otd_cal[key]['powerNeed'] == 0)]
    #     item_on.dropna(how = 'any', inplace = True)
        # power_cos = ['compressor1DirectPower']
        # if '129' in key:
        #     power_cos.append('outdoor0Power')
        # elif '130' in key:
        #     power_cos.append('outdoor1Power')
        # for power_co in power_cos:
        #     plt.scatter(item_on['compressor1Frequency'], item_on[power_co]
        #                 ,color='cornflowerblue', alpha = 0.5,label='original values')
        #                 #,color='#1f77b4', alpha = 0.3,label='original values')
        #     plt.xlabel('compressor1Frequency')
        #     plt.ylabel(power_co)
        #     parameter = np.polyfit(item_on['compressor1Frequency'], item_on[power_co], 1)
        #     p = np.poly1d(parameter)
        #     plt.scatter(item_on['compressor1Frequency'], p(item_on['compressor1Frequency'])
        #                 , color='burlywood', alpha = 0.5, label='polyfit values', s=10)
        #                 #, color='#ff7f0e', alpha = 0.3, label='polyfit values', s=10)
                        
        #     r_score = R(item_on[power_co], p(item_on['compressor1Frequency']))
        #     plt.title('r2 of {} nid {} is {}'.format(VRF_name, key.split('/')[-1], r_score))
        #     plt.legend()
        #     plt.show()

    # analysis power with condensing and evaporating temperature
    temp_co = ['deltaIOCondeseningTemp', 'deltaCondEvapTemp', 't8Temp','tLTemp','tgTemp']

    # # power
    # for key,item in VRF_each_otd_cal.items():
    #     item_on = VRF_each_otd_cal[key].copy()[~(VRF_each_otd_cal[key]['powerNeed'] == 0)]
    #     item_on.dropna(how = 'any', inplace = True)
    #     # power_cos = ['compressor1DirectPower']
    #     if '129' in key:
    #         power_cos.append('outdoor0Power')
    #     elif '130' in key:
    #         power_cos.append('outdoor1Power')

    #     for co in temp_co:
    #         for power_co in power_cos:
    #             plt.scatter(item_on[co], item_on[power_co]
    #                         ,color='cornflowerblue', alpha = 0.5,label='original values')
    #                         #,color='#1f77b4', alpha = 0.3,label='original values')
    #             plt.xlabel(co)
    #             plt.ylabel(power_co)
    #             parameter = np.polyfit(item_on[co], item_on[power_co], 1)
    #             p = np.poly1d(parameter)
    #             plt.scatter(item_on[co], p(item_on[co])
    #                         , color='burlywood', alpha = 0.5, label='polyfit values', s=10)
    #                         #, color='#ff7f0e', alpha = 0.3, label='polyfit values', s=10)
                            
    #             r_score = R(item_on[power_co], p(item_on[co]))
    #             plt.title('r2 of {} nid {} is {}'.format(VRF_name, key.split('/')[-1], r_score))
    #             plt.legend()
    #             plt.show()
    
    # frequency
    # for key,item in VRF_each_otd_cal.items():
    #     item_on = VRF_each_otd_cal[key].copy()[~(VRF_each_otd_cal[key]['powerNeed'] == 0)]
    #     item_on.dropna(how = 'any', inplace = True)
    #     for co in temp_co:
    #         plt.scatter(item_on[co], item_on['compressor1Frequency']
    #                     ,color='cornflowerblue', alpha = 0.5,label='original values')
    #                     #,color='#1f77b4', alpha = 0.3,label='original values')
    #         plt.xlabel(co)
    #         plt.ylabel('compressor1Frequency')
    #         parameter = np.polyfit(item_on[co], item_on['compressor1Frequency'], 1)
    #         p = np.poly1d(parameter)
    #         plt.scatter(item_on[co], p(item_on[co])
    #                     , color='burlywood', alpha = 0.5, label='polyfit values', s=10)
    #                     #, color='#ff7f0e', alpha = 0.3, label='polyfit values', s=10)
                        
    #         r_score = R(item_on['compressor1Frequency'], p(item_on[co]))
    #         plt.title('r2 of {} nid {} is {}'.format(VRF_name, key.split('/')[-1], r_score))
    #         plt.legend()
    #         plt.show()
            
    # different emperature
    # for key,item in VRF_each_otd_cal.items():
    #     item_on = VRF_each_otd_cal[key].copy()[~(VRF_each_otd_cal[key]['powerNeed'] == 0)]
    #     item_on.dropna(how = 'any', inplace = True)
    #     for co in temp_co:
    #         for co1 in temp_co:
    #             if co1 != co:
    #                 plt.scatter(item_on[co], item_on[co1]
    #                             ,color='cornflowerblue', alpha = 0.5,label='original values')
    #                             #,color='#1f77b4', alpha = 0.3,label='original values')
    #                 plt.xlabel(co)
    #                 plt.ylabel(co1)
    #                 parameter = np.polyfit(item_on[co], item_on[co1], 1)
    #                 p = np.poly1d(parameter)
    #                 plt.scatter(item_on[co], p(item_on[co])
    #                             , color='burlywood', alpha = 0.5, label='polyfit values', s=10)
    #                             #, color='#ff7f0e', alpha = 0.3, label='polyfit values', s=10)
                                
    #                 r_score = R(item_on[co1], p(item_on[co]))
    #                 plt.title('r2 of {} nid {} is {}'.format(VRF_name, key.split('/')[-1], r_score))
    #                 plt.legend()
    #                 plt.show()

    #onOff and power(system power and compressor power)
    VRF_each_sys['totalPower'] = VRF_each_sys['outdoor0Power'] + VRF_each_sys['outdoor1Power'] #+ VRF_each_sys['outdoor2Meter']
    for co in VRF_each_sys.columns:
        if "Power" in co:
            VRF_each_sys['Date'] = VRF_each_sys.index.map(lambda t: t.date())
            VRF_each_sys['Time'] = VRF_each_sys.index.map(lambda t: t.time().hour)
            pivot = pd.pivot_table(VRF_each_sys, values=co, index='Date', columns='Time')
            Visulize(title = VRF_name+' Hourly System Power Distribution'
                     , xlabel =  "Hour of Day"
                     , ylabel = co +' / W').norm_boxplot(pivot, legend_type = 2)
            #roomTemp_pivot.T.plot(legend=False, figsize=(15,5), color='k', alpha=0.1, xticks=np.arange(0, 86400, 10800))
            # pivot.T.plot( alpha = 0.3, legend=False)

    # # total power and the number of indoor unit
    # room_co = []
    # for key,item in VRF_each_indoor_5t.items():
    #     VRF_each_sys['onOff_' + key.split('/')[-1]] = item['onOff']
    #     room_co.append('onOff_' + key.split('/')[-1])
    # VRF_each_sys['onOffCount'] = VRF_each_sys[room_co].sum(axis = 1)
    # sns.violinplot(x = "onOffCount", 
    #                y = "totalPower",
    #                data = VRF_each_sys, 
    #                scale = 'count', 
    #                split = False,
    #                palette = Visulize().cmap_div 
    #               )
    # plt.title(VRF_name + ': TotalPower and The No. of Indoor Unit')
    # plt.show()
    
    # compressor power and the number of indoor unit
    # for key in VRF_each_otd_cal.keys():
    #     if '129' in key:
    #         VRF_each_sys['compressor1DirectPower129'] = VRF_each_otd_cal[key]['compressor1DirectPower']
    #         compressor_power_co = 'compressor1DirectPower129'
    #     elif '130' in key:
    #         VRF_each_sys['compressor1DirectPower130'] = VRF_each_otd_cal[key]['compressor1DirectPower']
    #         compressor_power_co = 'compressor1DirectPower130'
    #     sns.violinplot(x = "onOffCount", 
    #                     y = compressor_power_co,
    #                     data = VRF_each_sys, 
    #                     scale = 'count', 
    #                     split = False,
    #                     palette = Visulize().cmap_div 
    #                   )
    #     plt.title(VRF_name + ': '+ compressor_power_co +' and The No. of Indoor Unit')
    #     plt.show()
        
    #     sns.boxplot(x = "onOffCount", 
    #                     y = compressor_power_co, 
    #                     data = VRF_each_sys, 
    #                     palette = Visulize().cmap_div 
    #                   )
    #     plt.title(VRF_name + ': '+ compressor_power_co +' and The No. of Indoor Unit')
    #     plt.show()
    
    #     Visulize(title = VRF_name + ': compressor1DirectPower and The No. of Indoor Unit'
    #               , xlabel = 'onOffCount'
    #               , ylabel = 'compressor1DirectPower / W'
    #               ).norm_scatterplot( x = VRF_each_sys['onOffCount']
    #                                 , y = VRF_each_sys[compressor_power_co]
    #                                 , alpha = 0.1
    #                                 , legend_type = 2)

    sns.boxplot(x = "onOffCount", 
                   y = "totalPower", 
                   data = VRF_each_sys, 
                   palette = Visulize().cmap_div 
                  )
    plt.title(VRF_name + ': TotalPower and The No. of Indoor Unit')
    plt.show()

    Visulize(title = VRF_name + ': TotalPower and The No. of Indoor Unit'
             , xlabel = 'onOffCount'
             , ylabel = 'totalPower / W'
             ).norm_scatterplot( x = VRF_each_sys['onOffCount']
                                , y = VRF_each_sys['totalPower']
                                , alpha = 0.1
                                , legend_type = 2)

    VRF_each_sys['onOffCount'].hist()
    plt.title(VRF_name + ': onOffCount distribution')
    plt.xlabel('The No. of On Indoor Unit')
    plt.ylabel('Count')
    plt.legend()
    plt.show()
    
    
    # onOff analysis  #TODO need to debug
    # onOff_df = pd.DataFrame()
    # onOffColumns = ['outdoor0Power', 'outdoor1Power', 'onOffCount']
    # for key in VRF_each_indoor_5t.keys():
    #     onOffColumns.append('onOff_' + key.split('/')[-1])

    # onOff_df[onOffColumns] = VRF_each_sys[onOffColumns].dropna(how = 'any', axis = 0)
    # onOff_df['outdoor0OnOff'] = 0
    # onOff_df['outdoor1OnOff'] = 0
    # onOff_df.loc[~(onOff_df['outdoor0Power'] == 0), 'outdoor0OnOff'] = 1
    # onOff_df.loc[~(onOff_df['outdoor1Power'] == 0), 'outdoor1OnOff'] = 1
    
    
    # onOff_df['systemOnOffCount'] = 0
    # onOff_df['outdoorOnOffCount'] = 0
    # onOff_df['indoorOnOffCount'] = 0
    # for key,item in VRF_each_outdoor_5t.items():
    #     onOff_df['onOff' + key.split('/')[-1]] = item['powerNeed'].dropna(how = 'any', axis = 0)/100
    #     onOff_df.loc[~((onOff_df['onOff' + key.split('/')[-1]] == 0)), 'outdoorOnOffCount'] = 1

    # onOff_df.loc[~((onOff_df['outdoor1Power'] == 0) & (onOff_df['outdoor0Power'] == 0)), 'systemOnOffCount'] = 1
    # onOff_df.loc[(~(onOff_df['onOffCount'] == 0)), 'indoorOnOffCount'] = 1
    
    # onOff_analysis_co = ['indoorOnOffCount', 'systemOnOffCount', 'outdoorOnOffCount']
    # for co in onOff_analysis_co:
    #     onOff_df[co].plot()
    #     plt.title(VRF_name +': '+ co)
    #     plt.ylabel('onOff')
    #     plt.show()





def indoor_eda(VRF_name, VRF_each_indoor):
    #on off
    for key,item in VRF_each_indoor.items():
        item['onOff'].plot(label= key.split('/')[-1], alpha = 0.5)
    plt.legend(bbox_to_anchor=(1, 0), loc = 3, borderaxespad = 0)
    plt.ylabel('onOff')
    plt.title(VRF_name + ': onOff of all indoor unit')

    # comparison of each room
    analysis_columns = ['onOff', 'runMode', 'roomTemp', 'tempSetting', 'fan7SpeedSetting'
                       , 'indoorTempT2B', 'indoorTempT2', 'exv1Opening']
    for co in analysis_columns:
        for key,item in VRF_each_indoor.items():
            if 'int' in str(item[co].dtypes) or 'float' in str(item[co].dtypes):
                item[co].plot(alpha=0.5, label = key.split('/')[-1])
        plt.legend(bbox_to_anchor=(1, 0), loc = 3, borderaxespad = 0)
        plt.ylabel(co)
        plt.title(VRF_name + ': '+ co +' of all indoor unit')
        plt.show()

    # ridge
    hist_columns = ['roomTemp', 'tempSetting']
    for hist_co in hist_columns:
        values = []
        rooms = []
        for key,item in VRF_each_indoor.items():
            item = item[item['onOff'] == 1]
            values.append(item[hist_co].values)
            rooms.append('room ' +key.split('/')[-1])
        # colors = ['#FCF8E8', '#E0D8B0','#94B49F','#ECB390','#DF7861']
        fig,axs = joypy.joyplot(values
                                #, column = ['outdoor0Meter', 'outdoor0Power']
                                ,fill=True
                                ,legend=True
                                ,labels = rooms
                                ,alpha=.8
                                 ,range_style='own'
                                 ,xlabelsize=22,ylabelsize=22
                                 ,grid='both'
                                 , linewidth=.8
                                 ,linecolor='k'
                                 , figsize=(12,6)
                                 , hist = True
                                 #,color=colors,
                                  ,overlap = 0
                                 )
        label_dic = {'family': 'SimHei',
                 'weight': 'normal',
                 'size': 20,
                 }
        plt.xlabel(hist_co,label_dic)
        plt.title(VRF_name + ': '+ hist_co +' distribution',label_dic)
        plt.show()
    
    # heatmap of all rooms
    hp_analysis_cos = ['onOff', 'tempSetting', "roomTemp"]
    for co in hp_analysis_cos:
        value_df = pd.DataFrame()
        for key,item in VRF_each_indoor.items():
            value_df[key.split('/')[-1]] = item.copy().resample('h').mean()[co]
        value_df.index = value_df.index.map(lambda x: x.strftime('%Y-%m-%d %H:%M:%S'))
        sns.heatmap(value_df,cmap=Visulize().cmap_seq,
                    cbar_kws={'label': co,
                    },
                    )
        plt.xlabel('Room')
        plt.title(VRF_name + ': '+ co + ' heatmap')
        plt.show()


    # comparison of roomTemp and tempSetting 
    #all data
    for key,item in VRF_each_indoor.items():
        fig, axs = plt.subplots(1, 1)
        item['roomTemp'].plot(alpha=0.8)
        item['tempSetting'].plot(alpha=0.8)
        plt.fill_between(item.index, 32, 15, where=item['onOff'] == 0, facecolor="#251D3A", alpha=0.3, label = 'off')
        #plt.legend(bbox_to_anchor=(1, 0), loc = 3, borderaxespad = 0)
        plt.legend(bbox_to_anchor=(1, 0), loc = 3, borderaxespad = 0)
        plt.ylabel('Temp')
        plt.title(key)
        axs.set_ylim(15,32)
        plt.show()

    for key,item in VRF_each_indoor.items():
        item = item[item['onOff'] == 0]
        item.reset_index()['roomTemp'].plot(alpha=0.5)
        item.reset_index()['tempSetting'].plot(alpha=0.5)
        plt.legend()
        plt.xlabel('Timestamp')
        plt.ylabel('Temp')
        plt.title(key + 'OFF')
        plt.show()

    for key,item in VRF_each_indoor.items():
        item = item[item['onOff'] == 1]
        item.reset_index()['roomTemp'].plot(alpha=0.5)
        item.reset_index()['tempSetting'].plot(alpha=0.5)
        plt.legend()
        plt.xlabel('Timestamp')
        plt.ylabel('Temp')
        plt.title(key + " ON")
        plt.show()
        
    # tracking error
    tracking_error = []
    room_co = []
    for key,item in VRF_each_indoor.items():
        item = item[item['onOff'] == 1].copy()
        item['tempSetting - roomTemp'] = item['tempSetting'] - item['roomTemp']
        room_co.append(key.split('/')[-1])
        tracking_error.append(item['tempSetting - roomTemp'])
        plt.scatter(item['tempSetting'],item['tempSetting - roomTemp'], alpha = 0.2, label = key.split('/')[-1])
    plt.title('{} tracking error vs. tempSetting'.format(key.split('/')[1][-4:]))
    plt.xlabel('tempSetting')
    plt.ylabel('tempSetting - roomTemp')
    plt.legend()
    plt.show()

    p = sns.boxplot(data = tracking_error, 
                   palette = Visulize.cmap_div 
                  )
    p.set_xticklabels(room_co)
    p.set_ylabel("tempSetting - roomTemp")
    p.set_xlabel("Room")
    plt.title('{} Tracking Error of Room Temperature in 5T'.format(key.split('/')[1][-4:]))
    plt.show()

    #each room cpmparison when onOff ==1
    # for co in analysis_columns:
    #     for key,item in VRF_each_indoor.items():
    #         if 'int' in str(item[co].dtypes) or 'float' in str(item[co].dtypes):
    #             item = item[item['onOff'] == 1]
    #             item.reset_index()[co].plot(alpha=0.5, label = key.split('/')[-1])
    #     plt.legend(bbox_to_anchor=(1, 0), loc = 3, borderaxespad = 0)
    #     plt.ylabel(co)
    #     plt.show()

    #day profile of roomTemp in each room
    for key,item in VRF_each_indoor.items():
        item['Date'] = item.index.map(lambda t: t.date())
        item['Time'] = item.index.map(lambda t: t.time().hour)
        roomTemp_pivot = pd.pivot_table(item, values='roomTemp', index='Date', columns='Time')
        #roomTemp_pivot.T.plot(legend=False, figsize=(15,5), color='k', alpha=0.1, xticks=np.arange(0, 86400, 10800))
        # roomTemp_pivot.T.plot(legend=False)
        p = sns.boxplot( data = roomTemp_pivot, 
                       # order = ['on','off'], 
                       palette = Visulize.cmap_div
                      )
        plt.xlabel("Hour of Day")
        plt.ylabel("roomTemp")
        plt.title(key)
        plt.show()
    
    for key,item in VRF_each_indoor.items():
        # item = item[item['onOff'] == 1]
        item['Date'] = item.index.map(lambda t: t.date())
        item['Time'] = item.index.map(lambda t: t.time().hour)
        tempSetting_pivot = pd.pivot_table(item, values='tempSetting', index='Date', columns='Time')
        #roomTemp_pivot.T.plot(legend=False, figsize=(15,5), color='k', alpha=0.1, xticks=np.arange(0, 86400, 10800))
        # tempSetting_pivot.T.plot(legend=False)
        p = sns.boxplot( data = tempSetting_pivot, 
                       # order = ['on','off'], 
                       palette = Visulize.cmap_div
                      )
        plt.xlabel("Hour of Day")
        plt.ylabel("tempSetting")
        plt.title(key)
        plt.show()


    analysis_column = 'onOff'
    for key,item in VRF_each_indoor.items():
        # item = item[item['onOff'] == 1]
        item['Date'] = item.index.map(lambda t: t.date())
        item['Time'] = item.index.map(lambda t: t.time().hour)
        value_pivot = pd.pivot_table(item, values=analysis_column, index='Date', columns='Time')
        #value_pivot.T.plot(legend=False, figsize=(15,5), color='k', alpha=0.1, xticks=np.arange(0, 86400, 10800))
        # value_pivot.T.plot(legend=False)
        # plt.title(key)
        # plt.xlabel("Daily Time")
        # plt.ylabel(analysis_column)
        
        sns.heatmap(value_pivot,cmap=Visulize().cmap_seq,
                    linewidths= 1,
                    cbar_kws={'label': 'onOff', #color bar的名称
                    },
                    )
        plt.xlabel('Hour of Day')
        plt.title(VRF_name + ': On Off Overview of Room '+key.split('/')[-1])
        plt.show()

    #weather
    # VRF_each_otd_129_hourly = VRF_each_otd_129.resample('h').mean()
    item = weather['result']
    item['Date'] = item.index.map(lambda t: t.date())
    item['Time'] = item.index.map(lambda t: t.time().hour)
    weather_pivot = pd.pivot_table(item, values= 'e3', index='Date', columns='Time')
    #value_pivot.T.plot(legend=False, figsize=(15,5), color='k', alpha=0.1, xticks=np.arange(0, 86400, 10800))
    # value_pivot.T.plot(legend=False)
    sns.heatmap(weather_pivot,cmap=Visulize().cmap_seq,
                linewidths= 1,
                cbar_kws={'label': 'e3',
                },
                )
    plt.xlabel('Hour of Day')
    plt.title(VRF_name + ': Overview of Ambient Temperature')
    plt.show()
    
    
    # evaporator temperature and room temperature
    for key,item in VRF_each_indoor_5t.items():
        item['indoorTempT2'].plot(alpha = 0.3)
        item['indoorTempT2B'].plot(alpha = 0.3)
        item['roomTemp'].plot(alpha = 0.3)
        plt.fill_between(item.index, 35, -5, where=item['onOff'] == 0, facecolor="#251D3A", alpha=0.3, label = 'off')
        plt.legend()
        plt.ylabel('Temperature')
        plt.title(VRF_name + ": room" + key.split('/')[-1] + " Evaporator and Room Temperature")
        plt.show()


    
    # # relationship between temp and electricity
    # VRF_each_sys_hourly = VRF_each_sys.resample('h').mean()  #shape[504,9]
    # VRF_each_indoor_hourly = {}
    # for key,item in VRF_each_indoor_dic.items():
    #     item = item.copy()
    #     item.drop(['nid','Date','Time'], axis = 1, inplace = True)
        
    #     item = item.resample('h').mean()
    #     VRF_each_indoor_hourly[key] = item
        
    # arr = np.zeros(item.shape)
    # VRF_each_indoor_average = pd.DataFrame(data = arr,index = item.index, columns=item.columns)
    # for key,item in VRF_each_indoor_hourly.items():
    #     for co in item.columns:
    #         if 'time' not in co and 'nid' not in co:
    #             VRF_each_indoor_average[co] += item[co]
    # VRF_each_indoor_average /= 5
    
    # plt.scatter(VRF_each_indoor_average['tempSetting'], VRF_each_sys_hourly['total'], alpha = 0.3)
    # plt.xlabel('tempSetting')
    # plt.ylabel('total power')
    # plt.show()
    
    
    
    # comparison_df = pd.DataFrame()
    # comparison_df['t4Temp'] = VRF_each_otd_129_hourly['t4Temp']
    # comparison_df['compressor1Frequency'] = VRF_each_otd_129_hourly['compressor1Frequency']
    # comparison_df['total'] = VRF_each_sys_hourly['total']
    # comparison_df['roomTemp'] = VRF_each_indoor_average['roomTemp']
    # comparison_df['tempSetting'] = VRF_each_indoor_average['tempSetting']
    # comparison_df['fan7SpeedSetting'] = VRF_each_indoor_average['fan7SpeedSetting']
    # comparison_df['onOff'] = VRF_each_indoor_average['onOff']
    
    # comparison_df = comparison_df[~(comparison_df['onOff'] == 0)]


    # plt.matshow(comparison_df.corr(method = 'pearson'))
    # plt.xlabel('features')
    # plt.title('pearson')
    # scale_ls = range(len(comparison_df.columns))
    # plt.colorbar()
    # plt.xticks(scale_ls,comparison_df.columns, rotation = 90)
    # plt.yticks(scale_ls,comparison_df.columns)
    # plt.savefig(r'D:\project\media\data\corr.png',dpi = 400, bbox_inches = 'tight')
    # plt.show()



    # fig, ax1 = plt.subplots()
    # ax2 = ax1.twinx()    
    # # ax1.plot(VRF_each_indoor_39.loc[16516:16600]['roomTemp']
    # #          ,color='#94B49F', label = 'roomTemp')
    # # ax2.plot(VRF_each_indoor_39.loc[16516:16600]['onOff'].reset_index()
    # #          ,color='#ECB390', linestyle = '--', label = 'onOff')

    # ax1.plot(VRF_each_indoor_39.loc[16516:16600].index[::-1],VRF_each_indoor_39.loc[16516:16600]['roomTemp']
    #           ,color='#94B49F', label = 'roomTemp')
    # ax2.plot(VRF_each_indoor_39.loc[16516:16600].index[::-1], VRF_each_indoor_39.loc[16516:16600]['onOff']
    #           ,color='#ECB390', linestyle = '--', label = 'onOff')
    # ax1.set_xlabel('index')
    # ax1.set_ylabel('roomTemp')
    # ax2.set_ylabel('onOff')
    # fig.legend(bbox_to_anchor=(1, 0), loc = 3, borderaxespad = 0)
    # plt.show()


def data_mining(VRF_each_otd):
    #ambient weather
    ambient_weather = pd.DataFrame()
    
    ambient_weather['e3'] = weather['result'].resample('15m').mean()['e3']
    gridobj = sns.lmplot(x='compressor1Frequency'  # 横坐标
                  , y='compressor1Electricity'  # 纵坐标
                  #, hue='cyl'  # 分类/子集
                  , data=VRF_each_otd  # 数据集
                    , height=8  # 高度
                    , aspect=1.1  # 纵横比 长=aspect * height
                  # , palette='tab10'
                  , legend=True
                  , scatter_kws=dict(s=60, linewidths=.7, alpha = 0.5))

def accumulated_to_momentary(df_co):
    df_co_mom = df_co.copy()
    for i in range(len(df_co_mom.index)):
        try:
            df_co_mom[i] = df_co[df_co_mom.index[i]]- df_co[df_co_mom.index[i-1]]
        except: pass
    return df_co_mom

#%% main
# if __name__ == "__main__":
#     load_data()
#     # VRF_data_copy = VRF_data.copy()
#     # for VRF_name,VRF_each in VRF_data.items():
#     #     VRF_data_recompose(VRF_each)
#     #     system_eda(VRF_name)
#     #     outdoor_eda(VRF_name)
#     #     indoor_eda(VRF_name)
    
    
    
    
# %% abandon
    

# #%% draft
# # ridge plot
# # def test():
# #     VRF_each_sys = VRF_each['system'].copy()
# #     VRF_each_sys.drop('nid', axis = 1, inplace = True)
# #     # VRF_each_sys.set_index("time", inplace = True)
    

