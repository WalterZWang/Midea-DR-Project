# -*- coding: utf-8 -*-
"""
Created on Wed Oct 12 19:51:19 2022

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
import utility as util
#%% utility
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

def data_recompose_and_preprocess(VRF_name, VRF_each):
    VRF_each_sys =  VRF_each['sys_' + VRF_name.split('_')[-1]].resample('5T').mean()
    VRF_each_outdoor = {}; VRF_each_indoor = {}
    VRF_each_outdoor_5t = {}; VRF_each_indoor_5t = {}
    # outlier_detect_co = ['E_diff', 'E', 'P','t3Temp', 't4Temp','t5Temp','tgTemp','roomTemp'
    #                       ,'indoorTempT2A','indoorTempT2B','indoorTempT2']
    outlier_detect_co = ['E']
    for key,item in VRF_each.items():
        if 'odu' in key:
            for co in item.columns:
                item.rename(columns = {co: co.split('_', 2)[-1]},  inplace=True)
            for co in outlier_detect_co:
                if co in item.columns: 
                    item[co] = util.outlier(item, co)
            VRF_each_outdoor[key] = item
            VRF_each_outdoor_5t[key]= item.resample('5T').mean()
            # VRF_each_outdoor_5t[key]['powerNeed'] = item['powerNeed'].resample('5T').max()
        elif 'idu' in key:
            for co in item.columns:
                item.rename(columns = {co: co.split('_', 2)[-1]},  inplace=True)
            for co in outlier_detect_co:
                if co in item.columns: 
                    item[co] = util.outlier(item, co)
            VRF_each_indoor[key] = item
            VRF_each_indoor_5t[key]= item.resample('5T').mean()
            VRF_each_indoor_5t[key]['onOff'] = item['onOff'].resample('5T').max()
        elif 'meter' in key:
            meter_vrf = item.resample('15T').mean()
            for co in outlier_detect_co:
                if co in meter_vrf.columns: 
                    meter_vrf[co] = util.outlier(meter_vrf, co)
            meter_vrf['E_diff'] = meter_vrf['E'].diff()
            meter_vrf['E_diff'] = util.outlier(meter_vrf, 'E_diff')

    return VRF_each_sys, VRF_each_outdoor, VRF_each_indoor\
        , VRF_each_outdoor_5t, VRF_each_indoor_5t, meter_vrf
#%% msno
def weather_msno(weather_rsp):
    # weather_df = weather['result'].copy()
    # sns.heatmap(weather_df,cmap= Visulize().cmap_seq)
    msno.matrix(weather_rsp, labels=True, freq = 'M')
    plt.title( 'weather', fontsize=40)
    plt.show()

def VRF_msno(VRF_rsp):
    for sys, sys_dic in VRF_rsp.items():
        for key, item in sys_dic.items():
            msno.matrix(item, labels=True, freq = 'M')
            plt.title(sys + "_" + key, fontsize=40)
            plt.show()
            
def battery_msno(battery_dev_rsp, battery_meter_rsp):
    msno.matrix(battery_dev_rsp, labels=True, freq = 'M')
    plt.title( 'battery_dev', fontsize=40)
    plt.show()
    msno.matrix(battery_meter_rsp, labels=True, freq = 'M')
    plt.title( 'battery_meter', fontsize=40)
    plt.show()

def blg_meter_msno(blg_meter_rsp):
    for key, item in blg_meter_rsp.items():
        msno.matrix(item, labels=True, freq = 'M')
        plt.title( key, fontsize=40)
        plt.show()
        
def PV_msno(PV_dev_rsp, PV_meter_rsp):
    msno.matrix(PV_dev_rsp, labels=True, freq = 'M')
    plt.title( 'PV_dev', fontsize=40)
    plt.show()
    msno.matrix(PV_meter_rsp, labels=True, freq = 'M')
    plt.title( 'PV_meter', fontsize=40)
    plt.show()

def weather_EDA(weather_rsp):
    weather_rsp['Date'] = weather_rsp.index.map(lambda t: t.date())
    weather_rsp['Time'] = weather_rsp.index.map(lambda t: t.time().hour)
    item_pivot = pd.pivot_table(weather_rsp, values='e3', index='Date', columns='Time')
    Visulize(title = 'Outdoor Temp Distribution'
             , ylabel = 'e3'
             , xlabel = "Hour of Day"
             ).norm_boxplot(item_pivot)
    
    weather_rsp['Date'] = weather_rsp.index.map(lambda t: t.date())
    weather_rsp['Time'] = weather_rsp.index.map(lambda t: t.time().hour)
    item_pivot = pd.pivot_table(weather_rsp, values='e11', index='Date', columns='Time')
    Visulize(title = 'Outdoor Temp Distribution'
             , ylabel = 'e11'  # solar radiation
             , xlabel = "Hour of Day"
             ).norm_boxplot(item_pivot)

    weather_rsp['e3'].plot()
    plt.ylabel('e3 outdoor air temperature')
    plt.ylabel('time')
    plt.show()
    weather_rsp['e11'].plot()
    plt.ylabel('e11 solar radiation')
    plt.ylabel('time')
    plt.show()


#%% VRF device EDA
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
        # VRF_each_otd['powerNeed'] = 0
        # VRF_each_otd.loc[VRF_each_otd['compressor1Frequency'] > 0, 'powerNeed'] = 1
        # VRF_each_otd_5t['powerNeed'] = 0
        # VRF_each_otd_5t.loc[VRF_each_otd_5t['compressor1Frequency'] > 0, 'powerNeed'] = 1
        VRF_each_otd['powerNeed'].plot()
        plt.title(VRF_name + " powerNeed")
        plt.xlabel('Time')
        plt.ylabel('PowerNeed')
        plt.show()
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
        
        # plt.scatter(VRF_each_otd['compressor1Frequency'], VRF_each_otd['compressor1Electricity']
        #             ,color='cornflowerblue', alpha = 0.5,label='original values')
        #             #,color='#1f77b4', alpha = 0.3,label='original values')
        # plt.xlabel('compressor1Frequency')
        # plt.ylabel('compressor1Electricity')
        # parameter = np.polyfit(VRF_each_otd['compressor1Frequency'], VRF_each_otd['compressor1Electricity'], 1)
        # p = np.poly1d(parameter)
        # plt.scatter(VRF_each_otd['compressor1Frequency'], p(VRF_each_otd['compressor1Frequency'])
        #             , color='burlywood', alpha = 0.5, label='polyfit values', s=10)
        #             #, color='#ff7f0e', alpha = 0.3, label='polyfit values', s=10)
                    
        # r_score = R(VRF_each_otd['compressor1Electricity'], p(VRF_each_otd['compressor1Frequency']))
        # plt.title('r score is {}'.format(r_score))
        # plt.show()
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

    # sns.boxplot(x = "onOffCount", 
    #                y = "totalPower", 
    #                data = VRF_each_sys, 
    #                palette = Visulize().cmap_div 
    #               )
    # plt.title(VRF_name + ': TotalPower and The No. of Indoor Unit')
    # plt.show()

    # Visulize(title = VRF_name + ': TotalPower and The No. of Indoor Unit'
    #          , xlabel = 'onOffCount'
    #          , ylabel = 'totalPower / W'
    #          ).norm_scatterplot( x = VRF_each_sys['onOffCount']
    #                             , y = VRF_each_sys['totalPower']
    #                             , alpha = 0.1
    #                             , legend_type = 2)

    # VRF_each_sys['onOffCount'].hist()
    # plt.title(VRF_name + ': onOffCount distribution')
    # plt.xlabel('The No. of On Indoor Unit')
    # plt.ylabel('Count')
    # plt.legend()
    # plt.show()
    
    
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
    analysis_columns = ['onOff', 'roomTemp', 'tempSetting'#, 'fan7SpeedSetting'
                       # , 'indoorTempT2B', 'indoorTempT2', 'exv1Opening'
                       ]
    for co in analysis_columns:
        for key,item in VRF_each_indoor.items():
            # item = item[item['exv1Opening'] > 0]
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
            value_df[key.split('/')[-1]] = item.copy().resample('h').max()[co]
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
        # item = item[item['onOff'] == 1].copy()
        item = item[item['exv1Opening'] > 0].copy()
        item['tempSetting - roomTemp'] = item['tempSetting'] - item['roomTemp']
        room_co.append(key.split('/')[-1])
        tracking_error.append(item['tempSetting - roomTemp'])
        plt.scatter(item['tempSetting'],item['tempSetting - roomTemp'], alpha = 0.2, label = key.split('/')[-1])
    plt.title('{} tracking error vs. tempSetting'.format(key))
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
    plt.title('{} Tracking Error of Room Temperature in 5T'.format(key))
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

def meter_vrf_EDA(VRF_name, meter_vrf):
    meter_vrf['E'].plot()
    plt.title(VRF_name + "_E")
    plt.ylabel('E')
    plt.show()
    
    meter_vrf['E_diff'] =  meter_vrf['E'].diff()
    meter_vrf['E_diff'].plot()
    plt.title(VRF_name + "_E_diff")
    plt.ylable('E_diff')
    plt.show()
    
    meter_vrf['E_diff'] = util.outlier_power(meter_vrf, 'E_diff')
    meter_vrf['E_diff'].plot()
    plt.title(VRF_name + "_E_diff")
    plt.ylable('E_diff')
    plt.show()

def VRF_device_eda_main(VRF_rsp):
    VRF_data_copy = VRF_rsp.copy()
    for VRF_name,VRF_each in VRF_data_copy.items():
        VRF_each_sys, VRF_each_outdoor, VRF_each_indoor\
           , VRF_each_outdoor_5t, VRF_each_indoor_5t, meter_vrf = data_recompose_and_preprocess(VRF_name,VRF_each)
        system_eda(VRF_name, VRF_each_sys)
        outdoor_eda(VRF_name, VRF_each_outdoor_5t, VRF_each_outdoor, VRF_each_sys,VRF_each_indoor_5t)
        indoor_eda(VRF_name, VRF_each_indoor)
        meter_vrf_EDA(VRF_name, meter_vrf)

#%% meter
def meter_EDA(meter_name, meter_df, E_co):
    meter_df[E_co].plot()
    plt.title(meter_name + "_" + E_co)
    plt.ylabel(E_co)
    plt.show()
    
    meter_df['E_diff'] =  meter_df[E_co].diff()
    meter_df['E_diff'].plot()
    plt.title(meter_name + "_E_diff")
    plt.ylabel('E_diff')
    plt.show()
    
    # meter_df['E_diff'] = util.outlier_power(meter_df, 'E_diff')
    meter_df['E_diff'].plot()
    plt.title(meter_name + "_E_diff")
    plt.ylabel('E_diff')
    plt.show()

def meter_EDA_main(PV_meter_rsp,battery_meter_rsp):
    meter_EDA('PV_meter', PV_meter_rsp, "Pri_AE")
    meter_EDA('battery_meter', battery_meter_rsp, "Pri_AE")
    meter_EDA('battery_meter', battery_meter_rsp, "Sec_AE")
