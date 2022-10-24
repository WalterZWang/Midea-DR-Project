# -*- coding: utf-8 -*-
"""
Created on Tue Sep  6 15:14:50 2022

@author: Mingyue Guo
"""
'''
美的项目Influxbd的API：
InfluxDB连接方式：
host: vm.buildibp.top,
port： 21621,
username：btri,
password，mBXRGzfeWee3iZzq,
database：moserver,
measurement: modata_indoor, modata_outdoor, modata_sys
'''
#%% import
from influxdb import InfluxDBClient
from influxdb import DataFrameClient
import pandas as pd
import numpy as np
import utility as util

#%%

def get_select_clause(start_time, end_time, cols, ids, measure_name = 'indoor'):
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
    select_clause += " from moserver.autogen.modata_"+ measure_name +" where "
    for i in ids:
        if i == ids[-1]:
            select_clause += " nid =~/" + i +"/"
        else:
            select_clause += " nid =~/" + i +"/" + " or"
    if start_time != None:
        select_clause +=  " and time >= '" + start_time + "'"
    if end_time != None:
        select_clause += " and time <= '" + end_time + "'"
    # select_clause +=  " and time >= '" + start_time + "' and time <= '" + end_time + "'"
    if ids == None and start_time == None and end_time == None:
        select_clause = "select " + select_fields
        # select_clause += " from moserver.autogen."+ measure_name +" where "
        select_clause += " from "+ measure_name

    # select_clause +=  " and time >= '" + start_time + "' and time <= '" + end_time + "'"
    return select_clause

def get_df(df_sys, df_idr, df_odr):
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
    df_dic = {}
    for name,group in odr_copy.groupby('sys_id'):
        df_dic['VRF_' +name[-4:]] = {}
    for name,group in odr_copy.groupby('nid'):
        for co in group.columns:
            if 'id' not in co:
                group[co] = pd.to_numeric(group[co],errors='coerce')
        group.index = group.index.map(lambda x: util.change_timezone(x))
        df_dic['VRF_' +name.split('/')[1][-4:]]["odu_"+name.split('/')[3]]=group.copy()

    idr = df_idr[list(df_idr.keys())[0]]
    idr_copy = idr.copy()
    for name,group in idr_copy.groupby('nid'):
        for co in group.columns:
            if 'id' not in co:
                group[co] = pd.to_numeric(group[co],errors='coerce')
        group.index = group.index.map(lambda x: util.change_timezone(x))
        df_dic['VRF_' +name.split('/')[1][-4:]]["idu_"+name.split('/')[3]]=group.copy()
    return df_dic


#%% 
# if __name__ == "__main__":
def port1_main(start_time,end_time, vrf_ids, sys_cos, idr_cos, odr_cos):
    '''
    This function gets data from the previous influxDB database.

    Parameters
    ----------
    start_time : string
        Start time of enquire. Format:'%y-%m-%d %H:%M:%S'. If None: no constrint of start time
    end_time : string
        End time of enquire. Format:'%y-%m-%d %H:%M:%S'. If None: no constrint of end time
    vrf_ids : list
        IDs of VRFs you want to enquiry.
    sys_cos : list
        Columns in system sheet you want to enquiry.
    idr_cos : list
        Columns in indoor sheet you want to enquiry.
    odr_cos : list
        Columns in outdoor sheet you want to enquiry.

    Returns
    -------
    VRF_data : dict
        Data of VRFs.

    '''
    client = InfluxDBClient(host='vm.buildibp.top', port=21621, username='btri', password='mBXRGzfeWee3iZzq', database='moserver')
    df_client = DataFrameClient(host='vm.buildibp.top', port=21621, username='btri', password='mBXRGzfeWee3iZzq', database='moserver')
    start_time = start_time
    end_time = end_time
    ids = vrf_ids
    # indoor
    idr_select_clause = get_select_clause(start_time, end_time, idr_cos, ids, measure_name = 'indoor')
    df_idr = df_client.query(idr_select_clause)
    # outdoor
    odr_select_clause = get_select_clause(start_time, end_time, odr_cos, ids, measure_name = 'outdoor')
    df_odr = df_client.query(odr_select_clause)
    # system
    sys_select_clause = get_select_clause(start_time, end_time, sys_cos, ids, measure_name = 'sys')
    df_sys = df_client.query(sys_select_clause)
    
    VRF_data = get_df(df_sys, df_idr, df_odr)
    return VRF_data
