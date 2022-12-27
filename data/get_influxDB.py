# -*- coding: utf-8 -*-
"""
Created on Tue Sep  6 15:14:50 2022

@author: Mingyue Guo
"""
'''
InfluxDB of Midea：
InfluxDB connection：
PORT1:
host: vm.buildibp.top,
port: 21621,
username: btri,
password, mBXRGzfeWee3iZzq,
database: moserver,
measurement: modata_indoor, modata_outdoor, modata_sys
database: moserveribms,
measurement: ibmsV2modata, bridgemodata
    sphinx
    
PORT2:
host: vm.buildibp.top,
new port: 21622,
username: btri,
password, mBXRGzfeWee3iZzq,
database: moserver,
measurement: modata_indoor, modata_outdoor, modata_sys
database: moserveribms,
measurement: ibmsV2modata, bridgemodata

'''
#%% import
from influxdb import InfluxDBClient
from influxdb import DataFrameClient
import pandas as pd
import numpy as np
import utility as util
import copy
import influxDB_OldPort as port1

#%%
def get_table_info(host,port,username,password):
    '''
    This function is to get the basic information of the specific database

    Parameters
    ----------
    host : string
        host of infuxDB.
    port : int
        port of influxDB.
    username : string
        username is provided by Midea.
    password : string
        password of get access of influxDB.

    Returns
    -------
    result : result.ResultSet
        basic information of influxDB.

    '''
    client_vrf = InfluxDBClient(host=host, port=port, username=username
                            , password=password
                            , database='moserver'
                            )
    client_meter = InfluxDBClient(host=host, port=port, username=username
                            , password=password
                            , database='moserveribms'
                            )

    database_list = client_vrf.get_list_database()
    print(database_list) #return database names

    measurements_list = client_vrf.get_list_measurements()
    print(measurements_list)
    result = client_vrf.query('show measurements;')
    print(result)
    # check connection of db
    client_vrf.ping()
    client_vrf.query('SELECT *::field')
    
    return result

def get_select_clause(start_time, end_time, cols, ids = None
                      , measure_name = 'modata', table_type = 'indoor'):
    '''
    This function forms the select clause
    Parameters
    ----------
    start_time : string
        Start time of enquire. Format:'%y-%m-%d %H:%M:%S'. If None: no constrint of start time
    end_time : string
        End time of enquire. Format:'%y-%m-%d %H:%M:%S'. If None: no constrint of end time
    cols : list
        The name of the column to query.
    ids : list, optional
        The name of the id to query. The default is None.
    measure_name : string, optional
        Name of measurement in influxDB. The default is 'modata'.
    table_type : string, optional
        Table name to query. The default is 'indoor'.

    Returns
    -------
    select_clause : string
        Select clause.

    '''
    select_fields = ''
    for co in cols:
        if co == cols[-1]:
            select_fields += co 
        else:
            select_fields += co +', '
    select_clause = "select " + select_fields
    # select_clause += " from moserver.autogen."+ measure_name +" where "
    select_clause += " from "+ measure_name +" where "
    # select_clause += " from moserver.autogen.modata" +" where "
    if ids != None:
        if table_type == 'indoor':
            for i in ids:
                if i == ids[-1]:
                    select_clause += " nid =~/" + i + "\/indoor" + "/"
                else:
                    select_clause += " nid =~/" + i + "\/indoor" +"/" + " or"
        if table_type == 'outdoor':
            for i in ids:
                if i == ids[-1]:
                    select_clause += " nid =~/" + i + "\/outdoor" + "/"
                else:
                    select_clause += " nid =~/" + i + "\/outdoor" +"/" + " or"
        if table_type == 'system':
            for i in ids:
                if i == ids[-1]:
                    select_clause += " nid = " + "'vrf/" + i + "'"
                else:
                    select_clause += " nid = " + "'vrf/" + i + "'" + " or"
        if table_type == 'meter':
            for i in ids:
                if i == ids[-1]:
                    select_clause += " devSn = " + "'" + i + "'"
                else:
                    select_clause += " devSn = " + "'" + i + "'" + " or"
        if table_type == 'weather':
            for i in ids:
                if i == ids[-1]:
                    select_clause += " nid = " + "'" + i + "'"
                else:
                    select_clause += " nid = " + "'" + i + "'" + " or"
    if start_time != None:
        select_clause +=  " and time >= '" + start_time + "'"
    if end_time != None:
        select_clause += " and time <= '" + end_time + "'"
    if ids == None and start_time == None and end_time == None:
        select_clause = "select " + select_fields
        # select_clause += " from moserver.autogen."+ measure_name +" where "
        select_clause += " from "+ measure_name
    return select_clause

class FormatOriginData():
    def __init__(self, vrf_ids):
        self.vrf_ids = vrf_ids

    def get_vrf_df(self, df_sys, df_idr, df_odr):
        '''
        This function puts the queried VRF data into a specific dictionary form
    
        Parameters
        ----------
        df_sys : defaultdict (of DataFrameClient)
            System data enquired form influxDB.
        df_idr : defaultdict (of DataFrameClient)
            Indoor data enquired form influxDB.
        df_odr : defaultdict (of DataFrameClient)
            Outdoor data enquired form influxDB.
        Returns
        -------
        df_dic : dict
            Dictionary of all VRF device data.
    
        '''
        odr = df_odr[list(df_odr.keys())[0]]
        odr_copy = odr.copy()
        odr_copy['sys_id'] = odr_copy['nid'].apply(lambda x: x.split('/')[1])
        self.VRF_data = {}
        for vrf_id in self.vrf_ids:
            self.VRF_data['VRF_' +vrf_id[-4:]] = {}
        for name,group in odr_copy.groupby('nid'):
            for co in group.columns:
                if 'id' not in co:
                    group[co] = pd.to_numeric(group[co],errors='coerce')
            group.index = group.index.map(lambda x: util.change_timezone(x))
            self.VRF_data ['VRF_' +name.split('/')[1][-4:]]["odu_"+name.split('/')[3]]=group.copy()
    
        idr = df_idr[list(df_idr.keys())[0]]
        idr_copy = idr.copy()
        for name,group in idr_copy.groupby('nid'):
            for co in group.columns:
                if 'id' not in co:
                    group[co] = pd.to_numeric(group[co],errors='coerce')
            group.index = group.index.map(lambda x: util.change_timezone(x))
            self.VRF_data ['VRF_' +name.split('/')[1][-4:]]["idu_"+name.split('/')[3]]=group.copy()
    
        sys = df_sys[list(df_sys.keys())[0]]
        sys_copy = sys.copy()
        for name,group in sys_copy.groupby('nid'):
            for co in group.columns:
                if 'id' not in co:
                    group[co] = pd.to_numeric(group[co],errors='coerce')
            group.index = group.index.map(lambda x: util.change_timezone(x))
            self.VRF_data ['VRF_' +name.split('/')[1][-4:]]["sys_"+name.split('/')[1][-4:]]=group.copy()
        return self.VRF_data 
    
    def add_meter_df(self
                     , df_blg_meter
                     , df_PV_dev
                     , df_PV_meter
                     , df_battery_dev
                     , df_battery_meter
                     , df_weather
                     # , VRF_data
                     , blg_devSn_id):
        '''
        This function puts meter data and weather data into a specific dictionary form
    
        Parameters
        ----------
        df_blg_meter : defaultdict (of DataFrameClient)
            Meter data of building(all meters in building including VRF meters) enquired form influxDB.
        df_PV_dev : defaultdict (of DataFrameClient)
            Device data of PV enquired form influxDB.
        df_PV_meter : defaultdict (of DataFrameClient)
            Meter data of PV enquired form influxDB.
        df_battery_dev : defaultdict (of DataFrameClient)
            Device data of battery enquired form influxDB.
        df_battery_meter : defaultdict (of DataFrameClient)
            Meter data of battery enquired form influxDB.
        df_weather : defaultdict (of DataFrameClient)
            Weather data enquired form influxDB.
        blg_devSn_id : dict
            The mapping of devSn and name in the specific dictionary format.
    
        Returns
        -------
        VRF_data : dict
            VRF device data and meter data in the certain dictionary format.
        blg_meter_data : dict
            Meter data in the building exclude VRF meter in the specific dictionary format.
        weather_data : dataframe
            Weather data.
        PV_meter : dataframe
            Meter data of PV.
        PV_dev : dataframe
            Device data of PV.
        battery_meter : dataframe
            Meter data of battery.
        battery_dev : dataframe
            Device data of battery.
    
        '''
        blg_meter = df_blg_meter[list(df_blg_meter.keys())[0]].copy()
        self.blg_meter_data = {}
        for name,group in blg_meter.groupby('devSn'):
            for co in group.columns:
                if 'devSn' not in co and 'nid' not in co:
                    group[co] = pd.to_numeric(group[co],errors='coerce')
            if name in blg_devSn_id.keys():
                group.index = group.index.map(lambda x: util.change_timezone(x))
                if blg_devSn_id[name] in self.VRF_data.keys():
                    self.VRF_data[blg_devSn_id[name]]["meter"]=group.copy()
                elif name in blg_devSn_id.keys():
                    self.blg_meter_data[name] = group.copy()
        weather = df_weather[list(df_weather.keys())[0]].copy()
        self.weather_data = weather.dropna(axis=0, subset=['e1', 'e3', 'e5', 'e7', 'e9', 'e11', 'e12'])
        for co in self.weather_data.columns:
            if 'devSn' not in co and 'nid' not in co:
                self.weather_data[co] = pd.to_numeric(self.weather_data[co],errors='coerce')
        self.weather_data.index = self.weather_data.index.map(lambda x: util.change_timezone(x))
        
        self.PV_meter = df_PV_meter[list(df_PV_meter.keys())[0]].copy()
        self.PV_dev = df_PV_dev[list(df_PV_dev.keys())[0]].copy()
        self.PV_meter.index = self.PV_meter.index.map(lambda x: util.change_timezone(x))
        self.PV_dev.index = self.PV_dev.index.map(lambda x: util.change_timezone(x))
    
        for co in self.PV_meter.columns:
            if 'devSn' not in co and 'nid' not in co:
               self. PV_meter[co] = pd.to_numeric(self.PV_meter[co],errors='coerce')
        for co in self.PV_dev.columns:
            if 'devSn' not in co and 'nid' not in co:
                self.PV_dev[co] = pd.to_numeric(self.PV_dev[co],errors='coerce')
        # PV_dev_data = {}
        # for name,group in PV_dev.groupby('devSn'):
        #     for co in group.columns:
        #         if 'devSn' not in co and 'nid' not in co:
        #             group[co] = pd.to_numeric(group[co],errors='coerce')
        #     PV_dev_data[name] = group.copy()
        #battery
        self.battery_meter = df_battery_meter[list(df_battery_meter.keys())[0]].copy()
        self.battery_dev = df_battery_dev[list(df_battery_dev.keys())[0]].copy()
        for co in self.battery_meter.columns:
            if 'devSn' not in co and 'nid' not in co:
                self.battery_meter[co] = pd.to_numeric(self.battery_meter[co],errors='coerce')
        for co in self.battery_dev.columns:
            if 'devSn' not in co and 'nid' not in co:
                self.battery_dev[co] = pd.to_numeric(self.battery_dev[co],errors='coerce')
        self.battery_meter.index = self.battery_meter.index.map(lambda x: util.change_timezone(x))
        self.battery_dev.index = self.battery_dev.index.map(lambda x: util.change_timezone(x))
    
        return self.VRF_data, self.blg_meter_data, self.weather_data\
            , self.PV_meter, self.PV_dev,self. battery_meter, self.battery_dev
    
    def resample_min_interval(self):
        '''
        This function resamples data according to their minimum interval
    
        Parameters
        ----------
    
        Returns
        -------
        VRF_rsp : dict
            Resampled VRF device data and meter data in the certain dictionary format.
        blg_meter_rsp : dict
            Resampled meter data in the building exclude VRF meter in the specific dictionary format..
        weather_rsp : dataframe
            Resampled weather data.
        PV_meter_rsp : dataframe
            Resampled PV meter data.
        PV_dev_rsp : dataframe
            Resampled PV device data.
        battery_meter_rsp : dataframe
            Resampled battery meter data.
        battery_dev_rsp : dataframe
            Resampled battery device data.
        PV_meter : dataframe
            Resampled PV meter data.
        PV_dev : dataframe
            Resampled PV device data.
        '''
        self.VRF_rsp = copy.deepcopy(self.VRF_data)
        VRF_res = '15T'
        for sys,sys_dic in self.VRF_rsp.items():
            for key, item in sys_dic.items():
                # if 'meter' in key:
                #     VRF_res = '15T'
                self.VRF_rsp[sys][key] = item.copy().resample(VRF_res).mean()
                # for co in item.columns:
                #     if 'str' in str(type(item[co][0])):
                #         VRF_rsp[sys][key][co] = item[co][0]
    
        self.blg_meter_rsp = copy.deepcopy(self.blg_meter_data)
        meter_res = '15T'
        for key, item in self.blg_meter_rsp.items():
            self.blg_meter_rsp[key] = item.copy().resample(meter_res).mean()
            # for co in item.columns:
            #     if 'str' in str(type(item[co][0])):
            #         VRF_rsp[sys][key][co] = item[co][0]
    
        self.weather_rsp = copy.deepcopy(self.weather_data)
        weather_res = '15T'
        self.weather_rsp = self.weather_rsp.resample(weather_res).mean()
        self.PV_meter_rsp = copy.deepcopy(self.PV_meter)
        self.PV_meter_rsp = self.PV_meter_rsp.resample(meter_res).mean()
        self.PV_dev_rsp = copy.deepcopy(self.PV_dev)
        self.PV_dev_rsp = self.PV_dev_rsp.resample(meter_res).mean()
        self.battery_meter_rsp = copy.deepcopy(self.battery_meter)
        self.battery_meter_rsp = self.battery_meter_rsp.resample(meter_res).mean()
        self.battery_dev_rsp = copy.deepcopy(self.battery_dev)
        self.battery_dev_rsp = self.battery_dev_rsp.resample(meter_res).mean()
        return self.VRF_rsp, self.blg_meter_rsp, self.weather_rsp, self.PV_meter_rsp\
            , self.PV_dev_rsp, self.battery_meter_rsp, self.battery_dev_rsp\
                , self.PV_meter, self.PV_dev

    def combine_port(self,VRF_data_port1, VRF_data_port2):
        '''
        This function combine data from port 1 and port 2

        Parameters
        ----------
        VRF_data_port1 : dict
            VRF data from port 1.
        VRF_data_port2 : dict
            VRF data from port 2.

        Returns
        -------
        VRF_data : dict
            Combined VRF data.

        '''
        self.VRF_data = copy.deepcopy(VRF_data_port2)
        if VRF_data_port1 == None:
            print('ERROR: can not access port 1')
        else:
            for sys, sys_dic in VRF_data_port2.items():
                for key,item in VRF_data_port2[sys].items():
                    if key in VRF_data_port1[sys].keys():
                        self.VRF_data[sys][key] = pd.concat([VRF_data_port1[sys][key], VRF_data_port2[sys][key]])
        return self.VRF_data


#%% main
def get_influxDB_main():
# if __name__ == "__main__":
    # database settings
    host = 'vm.buildibp.top'
    port = 21622
    # port = port
    username='btri'
    password='mBXRGzfeWee3iZzq'
    database_vrf ='moserver'
    database_meter ='moserveribms'
    # VRF select
    start_time = '2022-08-01 00:00:00' # format: '2022-05-01 00:00:00'
    end_time = '2022-09-15 00:00:00' #format: '2022-10-02 00:00:00'
    # start time and end time for port 1: August only
    start_time2 = None
    end_time2 = None

    vrf_ids = ['vrf_0000CC311178CCM26232341000271K0V'
            ,'vrf_0000CC311178CCM2623234100089GUN5'
            ,'vrf_0000CC311178CCM262323410008787JG'
            ,'vrf_0000CC311178CCM2625194100032JSJR'
            ,'vrf_0000CC311178CCM26221641000108104'
            ,'vrf_0000CC311178CCM2625204100009J8UW'
           ]
    sys_cos = ['nid'
               , 'systemQc', 'systemQh'
               , 'outdoor0Meter', 'outdoor0Power'
               , 'outdoor1Meter', 'outdoor1Power'
               ,'outdoor2Meter', 'outdoor2Power'
               ]
    idr_cos = ['nid'
                , 'systemQc', 'systemQh'
               , 'onOff', 'roomTemp', 'tempSetting', 'errorCode'
               , 'indoorTempT2A', 'indoorTempT2B', 'indoorTempT2'
               , 'exv1Opening'
               ]
    odr_cos = ['nid'
                , 'systemQc', 'systemQh'
               , 'compressor1Frequency', 'compressor2Frequency'
               , 'compressor1Electricity', 'compressor2Electricity'
               , 't3bTemp', 't3Temp','t4Temp', 't5Temp'
               , 'inletT6ATemp', 'outletT6BTemp', 't8Temp', 't9Temp'
               , 'tgTemp', 'tLTemp', 'highPressureSaturationTemp'
               , 'lowPressureSaturationTemp', 'fan1Frequency', 'powerNeed'
               ]
    # VRF meter select
    blg_meter_cos = ['devSn', 'nid', 'E', 'Evar', 'U', 'I', 'P', 'PF']
    
    PV_meter_cos = ['devSn', 'nid'
                   ,'Pri_AE','Pri_RE'
                   ,'Sec_AE', 'Sec_RE']
        
    PV_dev_cos = ['devSn', 'nid'
                       , 'EacTotal'
                      ]
    
    battery_meter_cos = ['devSn', 'nid' 
                       ,'Pri_AE','Pri_RE' 
                       ,'Sec_AE', 'Sec_RE'
                       ]
    
    battery_dev_cos = ['devSn', 'nid' 
                       ,'totalCharge','totalDischarge', 'dailyCharge'
                         # ,'dailyDischarge'
                         ,'BMS_SOC'
                         # , 'BMS_ChargeCap'
                         # ,'BMS_DischargeCap', 'activePowerSp','reactiveModeSp'
                         # ,'reactivePowerSp','PFSp'
                         ]
    
    blg_devSn_id = {  'mDev_EMeter_Roof_MDV_6': "VRF_GUN5"
                  ,'mDev_EMeter_Roof_MDV_3': "VRF_JSJR"
                  ,'mDev_EMeter_Roof_MDV_8': "VRF_J8UW"
                  ,'mDev_EMeter_Roof_MDV_10': "VRF_1K0V"
                  ,'mDev_EMeter_Roof_MDV_7': "VRF_87JG"
                  ,'mDev_EMeter_Roof_MDV_9': "VRF_8104"
                  ,'mDev_EMeter_F2_Backup': 'MEL_light'
                  }
    blg_devSn = list(blg_devSn_id.keys())

    PV_dev_devSn = ['mDev_inverter.growatt_b1'
                    ,'mDev_inverter.growatt_b2'
                    ,'mDev_inverter.growatt_b3'
                    ,'mDev_inverter.growatt_c1'
                    ]
    
    PV_meter_devSn = ['mDev_EMeter2_PV']
    
    battery_dev_devSn = ['mDev_EnergyStore.BCS100K_zlan9100-3']
    battery_meter_devSn = [ 'mDev_EMeter2_ES']
    
    # weather select
    weather_cos = ['devSn', 'e1', 'e3', 'e5', 'e7', 'e9', 'e11', 'e12', 'nid']
    devSn_weather = None
    nid_weather = ['ibms/ibms_1564376390869024768/microWeatherStation/20201800']
    # client setting
    df_client_vrf = DataFrameClient(host=host
                                , port=port
                                , username=username
                                , password=password
                                , database=database_vrf
                                )
    df_client_meter = DataFrameClient(host=host
                                , port=port
                                , username=username
                                , password=password
                                , database=database_meter
                                )

#%% VRF database
    # indoor
    idr_select_clause = get_select_clause(start_time = start_time
                                          , end_time = end_time
                                          , cols = idr_cos, ids = vrf_ids
                                          , measure_name = 'modata'
                                          , table_type = 'indoor')
    df_idr = df_client_vrf.query(idr_select_clause)
    # outdoor
    odr_select_clause = get_select_clause(start_time = start_time
                                          , end_time = end_time
                                          , cols = odr_cos, ids = vrf_ids
                                          , measure_name = 'modata', table_type = 'outdoor')
    df_odr = df_client_vrf.query(odr_select_clause)
    # system
    sys_select_clause = get_select_clause(start_time = start_time
                                          , end_time = end_time
                                          , cols = sys_cos, ids = vrf_ids
                                          , measure_name = 'modata', table_type = 'system')
    df_sys = df_client_vrf.query(sys_select_clause)
    
#%% meter database
    # VRF and MEL_lighting meter
    blg_meter_select_clause = get_select_clause(start_time = start_time
                                                , end_time = end_time
                                                , cols = blg_meter_cos
                                                , ids = blg_devSn
                                                , measure_name = 'ibmsV2modata'
                                                , table_type = 'meter')
    df_blg_meter = df_client_meter.query(blg_meter_select_clause)
    # pv device(inverter)
    PV_dev_select_clause = get_select_clause(start_time = start_time
                                                , end_time = end_time
                                                , cols = PV_dev_cos
                                                , ids = PV_dev_devSn
                                                , measure_name = 'ibmsV2modata'
                                                , table_type = 'meter')
    df_PV_dev = df_client_meter.query(PV_dev_select_clause)
    # pv meter
    PV_meter_select_clause = get_select_clause(start_time = start_time
                                                , end_time = end_time
                                                , cols = PV_meter_cos
                                                , ids = PV_meter_devSn
                                                , measure_name = 'ibmsV2modata'
                                                , table_type = 'meter')
    
    df_PV_meter = df_client_meter.query(PV_meter_select_clause)
    # battery device(inverter)
    battery_dev_select_clause = get_select_clause(start_time = start_time
                                                , end_time = end_time
                                                , cols = battery_dev_cos
                                                , ids = battery_dev_devSn
                                                , measure_name = 'ibmsV2modata'
                                                , table_type = 'meter')
    df_battery_dev = df_client_meter.query(battery_dev_select_clause)
    # battery meter
    battery_meter_select_clause = get_select_clause(start_time = start_time
                                                , end_time = end_time
                                                , cols = battery_meter_cos
                                                , ids = battery_meter_devSn
                                                , measure_name = 'ibmsV2modata'
                                                , table_type = 'meter')
    df_battery_meter = df_client_meter.query(battery_meter_select_clause)
    # weather
    weather_select_clause = get_select_clause(start_time = start_time
                                              , end_time = end_time
                                              , cols = weather_cos
                                              , ids = nid_weather
                                              , measure_name = 'bridgemodata'
                                              , table_type = 'weather')
    df_weather = df_client_meter.query(weather_select_clause)

    #%% format data
    data = FormatOriginData(vrf_ids)
    VRF_data_port2 = data.get_vrf_df(df_sys, df_idr, df_odr)
    VRF_data_port1 = port1.port1_main(start_time2, end_time2, vrf_ids, sys_cos, idr_cos, odr_cos)
    VRF_data = data.combine_port(VRF_data_port1, VRF_data_port2)

    VRF_data, blg_meter_data, weather_data,\
        PV_meter, PV_dev, battery_meter, battery_dev = data.add_meter_df(df_blg_meter
                                                                    , df_PV_dev
                                                                    , df_PV_meter
                                                                    , df_battery_dev
                                                                    , df_battery_meter
                                                                    , df_weather
                                                                    # , VRF_data
                                                                    , blg_devSn_id)
    
    VRF_rsp, blg_meter_rsp, weather_rsp, PV_meter_rsp, PV_dev_rsp,\
        battery_meter_rsp, battery_dev_rsp, PV_meter, PV_dev = data.resample_min_interval()
    
    return data,VRF_rsp, blg_meter_rsp, weather_rsp, PV_meter_rsp, PV_dev_rsp,\
            battery_meter_rsp, battery_dev_rsp, PV_meter, PV_dev
