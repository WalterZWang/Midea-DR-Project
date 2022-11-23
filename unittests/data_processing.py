# -*- coding: utf-8 -*-
"""
Created on Thu Jul  7 23:16:33 2022

@author: Mingyue Guo
"""
#%% import
import os
import numpy as np
import pandas as pd
import datetime
from datetime import date, timedelta
from pytz import timezone
import matplotlib.pyplot as plt
import copy
import seaborn as sns
sns.set_style('darkgrid', {'font.sans-serif':['SimHei', 'Arial']})
plt.rcParams['axes.unicode_minus']=False
import missingno as msno
# from VRF_model import *
import utility as util
from sklearn.model_selection import KFold
import solar_angle

# %%
class DataProcess():
    def __init__(self, data):
        self.PV_dev_pro = data.PV_dev_rsp.copy()
        self.PV_meter_pro = data.PV_meter_rsp.copy()
        self.battery_dev_pro = data.battery_dev_rsp.copy()
        self.battery_meter_pro = data.battery_meter_rsp.copy()
        self.weather_pro = data.weather_rsp.copy()
        self.VRF_data_pro = data.VRF_rsp.copy()
        self.blg_meter_pro = data.blg_meter_rsp.copy()
        VRF_outlier_detect_co = ['E_diff', 'meter', 'roomTemp', 'onOff', 't4Temp', 'powerNeed', 'systemQc']
        self.VRF_process(VRF_outlier_detect_co)
        self.other_meter_process()

    # TODO: data celaning
    # mainly dealing with meter data
    def other_meter_process(self):
        self.PV_meter_pro['E_diff'] = self.PV_meter_pro['Pri_AE'].diff()
        self.PV_meter_pro['E_diff'] = util.outlier(self.PV_meter_pro, 'E_diff')
        # For battery: AE is discharging, RE is charging
        self.battery_meter_pro['Dischar_diff'] = self.battery_meter_pro['Pri_AE'].diff()
        self.battery_meter_pro['Dischar_diff'] = util.outlier(self.battery_meter_pro, 'Dischar_diff')
        self.battery_meter_pro['Char_diff'] = self.battery_meter_pro['Pri_RE'].diff()
        self.battery_meter_pro['Char_diff'] = util.outlier(self.battery_meter_pro, 'Char_diff')
        # dev data diff
        self.PV_dev_pro['E_diff'] = self.PV_dev_pro['EacTotal'].diff()
        self.PV_dev_pro['E_diff'] = util.outlier(self.PV_dev_pro, 'E_diff')
        # For battery: AE is discharging, RE is charging
        self.battery_dev_pro['Dischar_diff'] = self.battery_dev_pro['totalDischarge'].diff()
        self.battery_dev_pro['Dischar_diff'] = util.outlier(self.battery_dev_pro, 'Dischar_diff')
        self.battery_dev_pro['Char_diff'] = self.battery_dev_pro['totalCharge'].diff()
        self.battery_dev_pro['Char_diff'] = util.outlier(self.battery_dev_pro, 'Char_diff')
        # MELS diff
        for key,item in self.blg_meter_pro.items():
            self.blg_meter_pro[key]['E_diff'] = self.blg_meter_pro[key]['E'].diff()
            self.blg_meter_pro[key]['E_diff'] = util.outlier(self.blg_meter_pro[key], 'E_diff')
        
    def VRF_process(self, VRF_outlier_detect_co):
        for sys, VRF_spec in self.VRF_data_pro.items():
            for key,item in VRF_spec.items():
                if 'odu' in key:
                    for co in item.columns:
                        item.rename(columns = {co: co.split('_', 2)[-1]},  inplace=True)
                    for co in VRF_outlier_detect_co:
                        if co in item.columns: 
                            item[co] = util.outlier(item, co)
                    self.VRF_data_pro[sys][key] = item
                elif 'idu' in key:
                    for co in item.columns:
                        item.rename(columns = {co: co.split('_', 2)[-1]},  inplace=True)
                    for co in VRF_outlier_detect_co:
                        if co in item.columns: 
                            item[co] = util.outlier(item, co)
                    self.VRF_data_pro[sys][key] = item
                elif 'meter' in key:
                    self.VRF_data_pro[sys][key]['E_diff'] = self.VRF_data_pro[sys][key]['E'].diff()
                    for co in VRF_outlier_detect_co:
                        if co in self.VRF_data_pro[sys][key].columns:
                            self.VRF_data_pro[sys][key][co] = util.outlier(self.VRF_data_pro[sys][key], co)

# get attr: (instance)VRF_spec.__dict__.keys()
class SpecificVRF():
    def __init__(self, data_pro, analysis_vrf = 'VRF_1K0V'):
        self.analysis_vrf = analysis_vrf
        self.VRF_data_pro = data_pro.VRF_data_pro
        # self.VRF_spec = self.get_specific_system()
        self.get_specific_system()
        
    def get_specific_system(self
                            # , VRF_data, Q_data, analysis_vrf = 'VRF_1K0V'
                            ):
        system_name = self.analysis_vrf
        for VRF_name,VRF_spec in self.VRF_data_pro.items():
            if VRF_name == system_name:
                # print(VRF_name)
                # VRF_spec_sys, VRF_spec_outdoor, VRF_spec_indoor, VRF_spec_outdoor_5t\
                #     , VRF_spec_indoor_5t, meter_vrf = specific_vrf(VRF_spec)
                # origin data is in other class
                self.VRF_spec = VRF_spec
                self.VRF_spec_sys, self.VRF_spec_outdoor, self.VRF_spec_indoor, self.meter_vrf = self.specific_vrf()
                self.Q_each = VRF_spec['sys_' + system_name.split('_')[-1]]['systemQc']
                
    def specific_vrf(self):
        # VRF_spec_sys =  VRF_spec['vrf'].resample('5T').mean()
        VRF_spec_sys =  self.VRF_spec['sys_' + self.analysis_vrf.split('_')[-1]]
        VRF_spec_outdoor = {}; VRF_spec_indoor = {}
        # VRF_spec_outdoor_5t = {}; VRF_spec_indoor_5t = {}
        # outlier_detect_co = ['E_diff', 'E', 'P','t3Temp', 't4Temp','t5Temp','tgTemp','roomTemp'
        #                       ,'indoorTempT2A','indoorTempT2B','indoorTempT2']
        for key,item in self.VRF_spec.items():
            if 'odu' in key:
                VRF_spec_outdoor[key] = item
                # VRF_spec_outdoor_5t[key]['powerNeed'] = item['powerNeed'].resample('5T').max()
            elif 'idu' in key:
                VRF_spec_indoor[key] = item
            elif 'meter' in key:
                meter_vrf = item
                # meter_vrf['E_diff'] = util.outlier_meter(meter_vrf, 'E_diff')
        return VRF_spec_sys, VRF_spec_outdoor, VRF_spec_indoor, meter_vrf

class Weather():
    def __init__(self, data_pro):
        self.weather_his = data_pro.weather_pro
        #TODO weather forecast data
        
# TODO: weather forecast data
class RCData():
    def __init__(self, data_pro
                 , analysis_vrf = 'VRF_1K0V'#,'VRF_GUN5'
                 # , neighbor_vrfs = ['VRF_1K0V', 'VRF_87JG', 'VRF_J8UW']):
                 , neighbor_vrfs = [ 'VRF_JSJR']):

        self.analysis_vrf = analysis_vrf
        self.neighbor_vrfs = neighbor_vrfs
        self.weather = data_pro.weather_pro
        self.MELS = data_pro.blg_meter_pro['mDev_EMeter_F2_Backup']
        self.get_RC_data(data_pro)
        self.split_data()
        
    def get_RC_data(self, data_pro):
        self.VRF_spec = SpecificVRF(data_pro, self.analysis_vrf)
        self.VRF_neighbors = []
        for n in self.neighbor_vrfs:
            self.VRF_neighbors.append(SpecificVRF(data_pro, n))

    def split_data(self):
        # ta = VRF_spec_outdoor_5t[list(VRF_spec_outdoor_5t.keys())[0]]['t4Temp']
        # average room temperature
        indoor_dic = self.VRF_spec.VRF_spec_indoor
        # t0_aver = [0] * indoor_dic[list(indoor_dic.keys())[0]].shape[0]
        t0_df = pd.DataFrame()
        for key, item in indoor_dic.items():
            t0_df[key + "_roomTemp"] = indoor_dic[key]['roomTemp']
            # t0_aver += indoor_dic[key]['roomTemp']
        # t0_aver /= len(indoor_dic)
        t0_aver = t0_df.mean(axis = 1)
        self.train_df = pd.DataFrame(index = indoor_dic[list(indoor_dic.keys())[0]].index)
        # train_df['onOff'] = VRF_indoor['onOff']
        self.train_df['roomTemp'] = t0_aver + 273.15
        i = 1
        for VRF_nei in self.VRF_neighbors:
            indoor_dic_nei = VRF_nei.VRF_spec_indoor
            t_neighbor_aver = pd.DataFrame(index = indoor_dic_nei[list(indoor_dic_nei.keys())[0]].index)
            t_neighbor_aver['neighborTemp'] = 0
            # t_neighbor_aver = [0] * VRF_neighbor_indoor_5t[list(VRF_neighbor_indoor_5t.keys())[0]].shape[0]
            for key, item in indoor_dic_nei.items():
                t_neighbor_aver['neighborTemp'] += indoor_dic_nei[key]['roomTemp']
            t_neighbor_aver /= len(indoor_dic_nei)
            self.train_df['neighborTemp' + str(i)] = t_neighbor_aver + 273.15
            i += 1
        self.weather = self.weather[~self.weather.index.duplicated(keep='first')]
        self.train_df['ta'] = self.weather['e3'] + 273.15
        self.train_df['irradiance'] =self.weather['e11']
        self.train_df['Q'] = self.VRF_spec.Q_each
        self.train_df = self.train_df.resample('15T').mean()
        self.train_df['MELs'] = self.MELS['E_diff'] * 1000 / 0.25 # the unit of E_diff should be W
        # self.train_df = self.train_df.dropna(how = 'any', axis = 0)
        self.train_df['tn1_measured'] = np.append(self.train_df['roomTemp'].values[1:], np.nan)
        self.train_df = self.train_df.dropna(how = 'any', axis = 0)
    
        # find the number of whole day which has few missing data
        df = self.train_df.copy()
        df['date'] = df.index.date
        df['hour'] = df.index.hour
        pivot_df = pd.pivot_table(df, values = 'MELs', index = 'date', columns = "hour")
        # whole_date = list(pivot_df.dropna(how = 'any', axis = 0).index)
        whole_date_all = list(np.unique(df.index.date))
        whole_date = []
        for d in whole_date_all:
            if (self.train_df[self.train_df.index.date == d]).shape[0] > 3:
                # print((self.train_df[self.train_df.index.date == d]).shape[0])
                whole_date.append(d)

        self.train_list = []
        self.valid_list = []
        for d in whole_date[:-2]:
            self.train_list.append(self.train_df[self.train_df.index.date == d])
            self.train_list[-1]['deltaTime'] = self.train_list[-1].index
            self.train_list[-1]['deltaTime'] = self.train_list[-1]['deltaTime'].diff().dt.seconds
            self.train_list[-1].iloc[0,-1] = 900
            # train_list[-1]['deltaTime'] = train_list[-1]['deltaTime'].cumsum(axis = 0)
        for d in whole_date[-2:]:
            self.valid_list.append(self.train_df[self.train_df.index.date == d])
            self.valid_list[-1]['deltaTime'] = self.valid_list[-1].index
            self.valid_list[-1]['deltaTime'] = self.valid_list[-1]['deltaTime'].diff().dt.seconds
            self.valid_list[-1].iloc[0,-1] = 900
            # valid_list[-1]['deltaTime'] = valid_list[-1]['deltaTime'].cumsum(axis = 0)
        # train_list, valid_list = smooth(train_list, valid_list)
        
    # For temporary
    def predict_data(self, pred_date = datetime.date(2022,10,23)):
        for valid_data in self.valid_list:
            if valid_data.index.date[0] == pred_date:
                self.pred_date = pred_date
                self.pred_data = valid_data
                self.pred_data = self.pred_data.drop(['tn1_measured', 'Q'], axis = 1)
        return self.pred_data
        
        
        
class VRFData():
    def __init__(self, data_pro
                 , analysis_vrf = 'VRF_1K0V'#,'VRF_1K0V'
                 , target = 'submeterEnergy' # 'Q' or 'submeterEnergy'
                 ):
        self.analysis_vrf = analysis_vrf
        self.target = target
        # no need weather from micro station for now because the outdoor air temperature can be provided by the outdoor unit
        # self.weather = data_pro.weather_pro
        self.VRF_spec = SpecificVRF(data_pro, self.analysis_vrf)
        self.get_basic_data_df()
        self.generate_df(self.target)
        self.split_data()
        
    def get_basic_data_df(self):
        # 压缩机转速， 室外干球温度, 室内平均干球温度，
        VRF_sys =  self.VRF_spec.VRF_spec_sys.copy().resample('15T').mean()
        Q = self.VRF_spec.Q_each.copy().resample('15T').mean()
        min_time = VRF_sys.index.min()
        max_time = VRF_sys.index.max()

        VRF_outdoor = self.VRF_spec.VRF_spec_outdoor[list(self.VRF_spec.VRF_spec_outdoor.keys())[0]]
        # for co in VRF_outdoor_5t.columns:
        #     VRF_outdoor_5t.rename(columns = {co: co.split('_', 2)[-1]},  inplace=True)
        VRF_outdoor_15t = VRF_outdoor.resample('15T').mean()
        min_time = min(min_time, VRF_outdoor.index.min())
        max_time = max(max_time, VRF_outdoor.index.max())
        
        VRF_indoor_15t = {}
        for key,item in self.VRF_spec.VRF_spec_indoor.items():
            VRF_indoor_15t[key] = item.copy().resample('15T').mean()
            
            VRF_indoor_15t[key] = item.copy().resample('15T').mean()
            VRF_indoor_15t[key]['onOff'] = item['onOff'].resample('15T').max()
            min_time = min(min_time, VRF_indoor_15t[key].index.min())
            max_time = max(max_time, VRF_indoor_15t[key].index.max())

        self.VRF_df = pd.DataFrame()
        self.VRF_df.index = pd.date_range(start = min_time,end = max_time,freq = '15T')
        self.VRF_df['outdoor0Power'] = self.VRF_spec.VRF_spec_sys['outdoor0Power']
        # if submeter_name != None:
        #     submeter = submeters[submeter_name]
        meter = self.VRF_spec.meter_vrf.copy()
        # meter['E_diff'] = meter['E'].diff()
        self.VRF_df['submeterPower'] = meter['P'] * 1000   #W?
        self.VRF_df['submeterEnergy'] = meter['E_diff'] * 1000 / 0.25
        self.VRF_df['Q'] = self.VRF_spec.Q_each  # unit: W

        self.VRF_df['compressor1Frequency'] = VRF_outdoor_15t['compressor1Frequency']
        # p 是电机旋转磁场的极对数，但是可以当作常数项，假设极对数是2
        p = 2
        self.VRF_df['revolvingSpeed'] = 60 * self.VRF_df['compressor1Frequency'] / p

        self.VRF_df['ambientTemp'] = VRF_outdoor_15t['t4Temp']  # 室外机的环境温度，如果没有的话用下一行气象站的
        # self.VRF_df['ambientTemp'] = weather_df['e3']
        # try:
        # self.VRF_df['evaporatorTempO'] = VRF_outdoor_15t['tgTemp']
        # self.VRF_df['evaporatorTempI'] = VRF_outdoor_15t['t5Temp']
        self.VRF_df['evaporatorTemp'] = VRF_outdoor_15t['lowPressureSaturationTemp']
        self.VRF_df['condenserTemp'] = VRF_outdoor_15t['highPressureSaturationTemp']
        # self.VRF_df['condenserTemp'] = VRF_outdoor_15t['t4Temp']
        # self.VRF_df['evaporatorTemp'] = VRF_outdoor_15t['tgTemp'] 
        # self.VRF_df['condenserTemp'] = VRF_outdoor_15t['t3Temp']
            # self.VRF_df['condenserTemp'] = self.VRF_df['ambientTemp']
        # except:
        #     self.VRF_df['condenserTemp'] = self.VRF_df['ambientTemp']
        self.VRF_df['fanFreq'] = VRF_outdoor_15t['fan1Frequency']
        # self.VRF_df['fanFreq'] = 891
        # self.VRF_df['powerNeed'] = VRF_outdoor_15t['powerNeed']
        # TODO 没有power need，暂时先：电表数据不等于0的powerNeed == 1，电表数据等于0的powerNeed == 0
        self.VRF_df['powerNeed'] = 0
        self.VRF_df.loc[self.VRF_df['submeterEnergy'] > 0, 'powerNeed'] = 1
        self.VRF_df.loc[self.VRF_df['submeterEnergy'] > 100, 'powerNeed'] = 1
        self.VRF_df.loc[self.VRF_df['Q'] > 10, 'powerNeed'] = 1
        
        indoor_co = ['roomTemp'
                      # , 'indoorTempT2A'
                      # , 'indoorTempT2B'
                      # , 'indoorTempT2'
                       ]
        df_onOff = pd.DataFrame()
        for key,item in VRF_indoor_15t.items():
            df_onOff[key] = item['onOff']
        df_onOff['onCount'] = df_onOff.sum(axis = 1)
        self.VRF_df['onCount'] = df_onOff['onCount']
        
        for co in indoor_co:
            df_indoor = pd.DataFrame()
            for key,item in VRF_indoor_15t.items():
                df_indoor[key] = item[co]
            df_indoor[co] = df_indoor.mean(axis = 1)
            self.VRF_df[co] = df_indoor[co]

        # for key,item in VRF_indoor_15t.items():
        #     self.VRF_df['onCount'] += item['onOff'].fillna(0)
        #     # select rooms turned on AC
        #     for co in indoor_co:
        #         self.VRF_df.loc[item[item['onOff'] >0].index, co] += item.loc[item['onOff'] >0, co]
        # for co in indoor_co:
        #     self.VRF_df.loc[~(self.VRF_df['onCount'] == 0),co] /= self.VRF_df.loc[~(self.VRF_df['onCount'] == 0),'onCount']


    # all_df is self.model_df, x_co is self.x_co
    def generate_df(self 
                    , target = 'submeterEnergy'
                    , modelNO = 'model1'
                    ):
        self.modelNO = modelNO
        if self.target == 'Q':
            self.VRF_df_reg = self.VRF_df.copy().drop('submeterEnergy', axis = 1)
        elif self.target == 'submeterEnergy':
            self.VRF_df_reg = self.VRF_df.copy().drop('Q', axis = 1)
        if modelNO == "model1":
            self.VRF_df_reg = self.VRF_df_reg[[target, 'evaporatorTemp'
                                              , 'condenserTemp', 'fanFreq', 'powerNeed', 'onCount']]
        self.VRF_df_reg = self.VRF_df_reg.dropna(how = 'any')
        self.VRF_df_reg = self.VRF_df_reg[self.VRF_df_reg['powerNeed'] > 0]
        evaporaterTemps = [
                            'evaporatorTemp',
                            # 'evaporatorTempO',
                            # 'evaporatorTempI',
                            #  'indoorTempT2A',    # bad temperature
                            # 'indoorTempT2B',
                            # 'indoorTempT2'
                           ]
        if modelNO != 'model1':
            self.VRF_df_reg['revQuad'] = self.VRF_df_reg['revolvingSpeed'] ** 2
            self.VRF_df_reg['revCube'] = self.VRF_df_reg['revolvingSpeed'] ** 3
            self.VRF_df_reg['roomQuad'] = self.VRF_df_reg['roomTemp'] **2
            self.VRF_df_reg['ambientQuad'] = self.VRF_df_reg['ambientTemp'] **2
            self.VRF_df_reg['roomAmbient'] = self.VRF_df_reg['roomTemp'] * self.VRF_df_reg['ambientTemp']
            self.VRF_df_reg['roomAmbient'] = self.VRF_df_reg['roomTemp'] * self.VRF_df_reg['ambientTemp']
        
        self.VRF_df_reg['condQuad'] = self.VRF_df_reg['condenserTemp'] **2
        self.VRF_df_reg['condCube'] = self.VRF_df_reg['condenserTemp'] ** 3
        
        self.VRF_df_reg['condQuad'] = self.VRF_df_reg['condenserTemp'] **2
        self.VRF_df_reg['condCube'] = self.VRF_df_reg['condenserTemp'] ** 3
        
        self.VRF_df_reg['fanFreqQuad'] = self.VRF_df_reg['fanFreq'] **2
        # for models do not need evaporator temperature
        # model 2
        # polynomial of Q
        if modelNO == 'model2' or modelNO == 'all':
            a_columns = ['constant', 'roomTemp', 'ambientTemp']
            b_columns = ['constant', 'revolvingSpeed', 'revQuad', 'revCube']
            self.model_df = self.dot_multiply(a_columns, b_columns, self.VRF_df_reg)
            self.model_df.drop(['constant_constant'],axis = 1, inplace = True)
            self.x_co = self.model_df.columns.values
            self.model_df.index = self.VRF_df_reg.index
            self.model_df = pd.concat([self.model_df, self.VRF_df_reg], axis = 1, join='outer')
        # model 4
        # polynomial of Q
        if modelNO == 'model4' or modelNO == 'all':
            a_columns = ['constant', 'roomTemp', 'roomQuad', 'ambientTemp', 'ambientQuad', 'roomAmbient']
            b_columns = ['constant', 'revolvingSpeed', 'revQuad', 'revCube']
            self.model_df = self.dot_multiply(a_columns, b_columns, self.VRF_df_reg)
            self.model_df.drop(['constant_constant'],axis = 1, inplace = True)
            self.x_co = self.model_df.columns.values
            self.model_df.index = self.VRF_df_reg.index
            self.model_df = pd.concat([self.model_df, self.VRF_df_reg], axis = 1, join='outer')
        # model 5
        # polynomial of power of compressor
        if modelNO == 'model5' or modelNO == 'all':
            a_columns = ['constant', 'revolvingSpeed']
            b_columns = ['constant', 'ambientTemp']
            self.model_df = self.dot_multiply(a_columns, b_columns, self.VRF_df_reg)
            self.model_df.drop(['constant_constant'],axis = 1, inplace = True)
            self.x_co = self.model_df.columns.values
            self.model_df.index = self.VRF_df_reg.index
            self.model_df = pd.concat([self.model_df, self.VRF_df_reg], axis = 1, join='outer')
                
        # model 1 E+, # TODO No Ga, suppose it is running under the rating condition
        if modelNO == 'model1' or modelNO == 'all':
            for evaporatorCo in evaporaterTemps:
                self.VRF_df_reg['evaporatorTemp'] = self.VRF_df[evaporatorCo]
                self.VRF_df_reg['evapQuad'] = self.VRF_df[evaporatorCo] **2
                self.VRF_df_reg['evapCube'] = self.VRF_df[evaporatorCo] **3
                self.VRF_df_reg['condEvap'] = self.VRF_df['condenserTemp'] * self.VRF_df[evaporatorCo]
                self.model_df = self.VRF_df_reg
                self.x_co = ['condenserTemp', 'evaporatorTemp', 'condQuad'
                         , 'condEvap', 'evapQuad', 'fanFreqQuad']
        #model 3  20系数模型
        if modelNO == 'model3' or modelNO == 'all':
            for evaporatorCo in evaporaterTemps:
                self.VRF_df_reg['evaporatorTemp'] = self.VRF_df[evaporatorCo]
                self.VRF_df_reg['evapQuad'] = self.VRF_df[evaporatorCo] **2
                self.VRF_df_reg['evapCube'] = self.VRF_df[evaporatorCo] **3
                self.VRF_df_reg['condEvap'] = self.VRF_df['condenserTemp'] * self.VRF_df[evaporatorCo]
                self.VRF_df_reg['evapRev'] = self.VRF_df_reg['evaporatorTemp'] * self.VRF_df_reg['revolvingSpeed']
                self.VRF_df_reg['condRev'] = self.VRF_df_reg['condenserTemp'] * self.VRF_df_reg['revolvingSpeed']
                self.VRF_df_reg['evapQuadCond'] = self.VRF_df_reg['evaporatorTemp'] ** 2 *  self.VRF_df_reg['condenserTemp']
                self.VRF_df_reg['evapQuadRev'] = self.VRF_df_reg['evaporatorTemp'] ** 2 *  self.VRF_df_reg['revolvingSpeed']
                self.VRF_df_reg['condQuadRev'] = self.VRF_df_reg['condenserTemp'] ** 2 *  self.VRF_df_reg['revolvingSpeed']
                self.VRF_df_reg['condQuadEvap'] = self.VRF_df_reg['condenserTemp'] ** 2 *  self.VRF_df_reg['evaporatorTemp']
                self.VRF_df_reg['revQuadEvap'] = self.VRF_df_reg['revolvingSpeed'] ** 2 *  self.VRF_df_reg['evaporatorTemp']
                self.VRF_df_reg['revQuadCond'] = self.VRF_df_reg['revolvingSpeed'] ** 2 *  self.VRF_df_reg['condenserTemp']
                self.VRF_df_reg['evapCondRev'] =  self.VRF_df_reg['evaporatorTemp'] * self.VRF_df_reg['condenserTemp'] *  self.VRF_df_reg['revolvingSpeed']
                self.x_co = ['evaporatorTemp', 'condenserTemp', 'revolvingSpeed'
                         , 'evapQuad', 'condQuad', 'revQuad'
                         , 'condEvap', 'evapRev', 'condRev'
                         ,'evapCube', 'condCube', 'revCube'
                         ,'evapQuadCond', 'evapQuadRev', 'condQuadRev', 'condQuadEvap'
                         , 'revQuadEvap', 'revQuadCond', 'evapCondRev'
                         ]
                self.model_df = self.VRF_df_reg
        # model 7
        if modelNO == 'model7' or modelNO == 'all':
            for evaporatorCo in evaporaterTemps:
                self.VRF_df_reg['evaporatorTemp'] = self.VRF_df[evaporatorCo]
                self.VRF_df_reg['evapQuad'] = self.VRF_df[evaporatorCo] **2
                self.VRF_df_reg['evapCube'] = self.VRF_df[evaporatorCo] **3
                self.VRF_df_reg['condEvap'] = self.VRF_df['condenserTemp'] * self.VRF_df[evaporatorCo]
                # polynomial of power of compressor
                a_columns = ['constant', 'evaporatorTemp', 'condenserTemp', 'evapQuad', 'condQuad', 'condEvap']
                b_columns = ['constant', 'revolvingSpeed', 'revQuad']
                self.model_df = self.dot_multiply(a_columns, b_columns, self.VRF_df_reg)
                self.model_df.drop(['constant_constant'],axis = 1, inplace = True)
                self.x_co = self.model_df.columns.values
                self.model_df.index = self.VRF_df_reg.index
                self.model_df = pd.concat([self.model_df, self.VRF_df_reg], axis = 1, join='outer')

    def generate_matrix(self, columns, VRF_df_reg):
        df = pd.DataFrame()
        for c in columns:
            if c == 'constant':
                df['constant'] = [1]
            else:
                df[c] = [VRF_df_reg[c].values]
        return df
    
    
    def dot_multiply(self, a_columns, b_columns, df):
        a_df = self.generate_matrix(a_columns, df)
        b_df = self.generate_matrix(b_columns, df)
        a =  np.array(a_df).reshape(-1,1)
        b = np.array(b_df.values).reshape(1,-1)
        dot_multi = np.dot(a, b)
        dot_multi_df = pd.DataFrame()
        for row in range(dot_multi.shape[0]):
            row_name = a_df.columns[row]
            for co in range(dot_multi.shape[1]):
                co_name = b_df.columns[co]
                dot_multi_df[str(row_name) +'_'+str(co_name)] = dot_multi[row][co]
        return dot_multi_df

            
    # def split_data(self):
    def split_data(self
                    ,cross_valid = False
                   ):
        self.cross_valid = cross_valid
        VRF_df_all = self.model_df.copy().dropna(how = 'any')
        VRF_df_all = self.model_df[self.model_df['powerNeed'] > 0]
        X = VRF_df_all.loc[:, (self.x_co)]
        y = VRF_df_all.loc[:, self.target]
        self.X_train_list = []
        self.y_train_list = []
        self.X_test_list = []
        self.y_test_list = []

        if cross_valid:
            kf = KFold(n_splits=5,shuffle=False)  
            for train_index, test_index in kf.split(X): 
                # print('train_index:%s , test_index: %s ' %(train_index,test_index))
                self.X_train_list.append(X.iloc[train_index,:])
                self.y_train_list.append(y.iloc[train_index])
                self.X_test_list.append(X.iloc[test_index,:])
                self.y_test_list.append(y.iloc[test_index])
        else:
            row_count = X.shape[0]
            self.X_train_list.append(X.iloc[:(int(row_count*0.8))])
            self.y_train_list.append(y.iloc[:(int(row_count*0.8))])
            self.X_test_list.append(X.iloc[(int(row_count*0.8)):, :])
            self.y_test_list.append(y[(int(row_count*0.8)):])

    # For temporary
    def predict_data(self, pred_date = datetime.date(2022,10,23)
                     , decision_vara_name = 'evaporatorTemp' # or onOff
                     , decision_vara = None
                     ):
        VRF_df_all = self.model_df.copy().dropna(how = 'any')
        VRF_df_all = self.model_df[self.model_df['powerNeed'] > 0]
        self.VRF_pred_data = VRF_df_all[VRF_df_all.index.date == pred_date]
        if type(decision_vara) != type(None):
            self.X = self.VRF_pred_data.loc[:, (self.x_co)]
            self.X = self.X.drop([decision_vara_name],axis = 1)
            self.X[decision_vara_name] = decision_vara #TODO: how to deal with missing data
        else:
            self.X = self.VRF_pred_data.loc[:, (self.x_co)]
        self.y = self.VRF_pred_data[self.target]
        return self.X, self.y
        
class PVData():
    def __init__(self, data_pro, predict_day = '2022-10-23'
                 , stage = 'train' # 'train' or 'control'
                 ):
        self.PV_data = data_pro.PV_meter_pro
        self.weather = data_pro.weather_pro
        self.predict_day = predict_day
        self.predict_cos = ['E_diff']
        self.x_co = ['solar_radiation',  'Elevation angle', 'Azimuth angle', 'hour', 'zenith_solar'] # 'e3',
        # self.model_data = self.generate_data()
        self.stage = stage
        if self.stage == 'train':
            self.data_split()
    
    def generate_data(self
                      , data_type = 'train' #'train' or 'prediction'
                      ):
        model_data = self.feature_engineering(data_type)
        model_data = model_data[self.x_co + self.predict_cos]
        model_data = model_data.dropna(how = 'any')
        model_data = model_data.drop( index = model_data[model_data['E_diff'] == 0].index )
        if data_type == 'train':
            model_data = model_data[model_data.index < datetime.datetime.strptime(self.predict_day,"%Y-%m-%d").replace(tzinfo=timezone('Asia/Shanghai'))]
            model_data = model_data[model_data.index >= (datetime.datetime.strptime(self.predict_day,"%Y-%m-%d")- timedelta(days = 60)).replace(tzinfo=timezone('Asia/Shanghai'))]
        elif data_type == 'prediction':
            model_data = model_data[model_data.index.date == datetime.datetime.strptime(self.predict_day,"%Y-%m-%d").replace(tzinfo=timezone('Asia/Shanghai')).date()]

        return model_data

    def feature_engineering(self, data_type):
        self.weather_data = self.weather_preprocessing(data_type)
        data = self.PV_data.join(self.weather_data)
        data['date'] = data.index.date
        data['hour'] = data.index.hour
        data['month'] = data.index.month
        data['day'] = data.index.day
        angles = solar_angle.angles_main(start_time = str(self.PV_data.index.min().date())
                                         , end_time = str(self.PV_data.index.max().date()))
        data = data.copy().join(angles)
        data['zenith_solar'] = data['solar_radiation'] * np.sin(data['Elevation angle'] * np.pi / 180)
        return data

    def weather_preprocessing(self, data_type):
        if data_type == 'train':
            if 'e3' in self.weather.columns:
                weather_data = self.weather.rename(columns = {'e3': 'ambientTemp'})
            if 'e11' in self.weather.columns:
                weather_data = self.weather.rename(columns = {'e11': 'solar_radiation'})
        # TODO: no prediction weather, use historical data instead
        if data_type == 'prediction':
            if 'e3' in self.weather.columns:
                weather_data = self.weather.rename(columns = {'e3': 'ambientTemp'})
            if 'e11' in self.weather.columns:
                weather_data = self.weather.rename(columns = {'e11': 'solar_radiation'})
        #     weather_pred = load_prediction_weather(self.predict_day)
        #     weather_pred = weather_pred.resample('15T').interpolate()
        #     weather_pred = weather_pred.rename(columns = {'dswrf': 'solar_radiation', 'temperature': 'ambientTemp'})
        #     weather_data = weather_pred
        return weather_data

    def data_split(self):
        #TODO： need to check if there is data in predict and train datasets
        pred_data = self.generate_data('prediction')
        train_data = self.generate_data('train')
        self.X_train = train_data[self.x_co]
        self.X_test = pred_data[self.x_co]
        self.y_train = train_data[self.predict_cos]
        self.y_test = pred_data[self.predict_cos]
        return self.X_train, self.y_train, self.X_test, self.y_test

#TODO this is draft
class Battery():
    def __init__(self, data_pro, params: dict=None, efficiency: float=0.99, t0: int=0) -> None:
        # super().__init__(params=params)
        self.battery_meter = data_pro.battery_meter_pro
        self.battery_data = data_pro.battery_dev_pro

        default_params = {
            "Pmaxbat": 20,   # maximum charging power, usually 20, max 50
            "Pminbat": -20,  # maximum discharging power, usually 20, max 50
            "Bmax": 100,      # maximum charge  (battery capacity), unit kWh
            "Bmin": 0,       # lowest charge allowed
        }
        if params == None:
            self.params = default_params
        else:
            self.params = params
        self.efficiency = efficiency
        self.charge_value = t0   # total charging energy, suppose charging efficiency equals 1
        self.discharge_value = self.charge_value * self.efficiency 
        self.SOC = t0 / self.params['Bmax'] * 100

    # TODO more appropriate to generate a array of SOC or charge?
    def update_state(self, p: float) -> None:
        '''
        p: charge/discharge power (positive means charge, negative means discharge)
        '''
        energy = self.charge_value + 1 * max(p, 0) + self.efficiency * min(p, 0)
        assert energy >= self.params["Bmin"]
        assert energy <= self.params["Bmax"]
        self.charge_value = energy
        self.discharge_value = self.charge_value * self.efficiency 
        self.SOC = self.SOC + self.charge_value / self.params['Bmax']  # TODO: need charging efficiency not round trip efficiency

    def should_renew(self) -> np.ndarray:
        thres = 0.85 # lower limit of efficiency
        return self.efficiency < thres
    
    #TODO: use meter data to update efficiency
    def update_enficiency(battery_data):
        battery_process = battery_data.copy()
        # get data of previous month
        battery_process = battery_process.loc[battery_process.index[-1] - timedelta(days = 30) : battery_process.index[-1],:]
        SOC_mode = battery_process['BMS_SOC'].mode()[0]
        mode_index = battery_process[battery_process['BMS_SOC'] == SOC_mode].index
        battery_process = battery_process.loc[mode_index[0]: mode_index[-1],:]
        charge = battery_process['totalCharge'][-1] - battery_process['totalCharge'][0]
        discharge = battery_process['totalDischarge'][-1] - battery_process['totalDischarge'][0]
        efficiency = discharge / charge
        return efficiency
    
    def battery_constraints(p_max, p, SOC):
        p < p_max
        p > -p_max
        SOC > 0
        SOC < 1
        
