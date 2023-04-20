# -*- coding: utf-8 -*-
"""
@Project ：Midea-DR-Project-main 
@File    ：Brick2VRF_Data.py
@Time: 01/07/2023 0:05
@Author: Mingchen Li
"""

import brickschema
from Post_packaging_InfluxAPI import GetData_JsonList
from Data_preprocessing_Brick import GetData_fromCSV, merge_plot, Data2VRFData, Plot_df

# getting data from Brick and DB
g = brickschema.Graph()
g.load_file('1K0V_VRF_Model.ttl')
Json_list = []
for point, params in g.query("""
    SELECT ?point ?params WHERE {
        ?point brick:timeseries/brick:hasTimeseriesId ?params .
        ?point brick:hasTag tag:MPC_VRF.
    }
"""):
    # print(point, json.loads(params))
    Json_list.append(params)

# 该版本输出
df_DB_new = GetData_JsonList(Json_list, endTime='2022-11-30 21:55:00', resample='15T')
df_CSV_new = GetData_fromCSV(["time", "Q_cool"], filename='sys1_Qcool_calc_15Min.csv', resample='15T')
# df_new = merge_plot(df_DB_new, df_CSV_new, plot=False, resample_min=15)
VRF_df_new = merge_plot(df_DB_new, df_CSV_new, plot=False, resample_min=15)
print(VRF_df_new.shape)
print(VRF_df_new['diff(Outdoor unit power)'].mean())
P_df = VRF_df_new[['Cooling capacity', 'diff(Outdoor unit power)']]
Plot_df(P_df, 500, title="E_diff & Q_cool")

# for i in df_new.columns:
#     df_new[i] = df_new[i].interpolate(method='linear')

VRF_df_new.to_csv("Results/temp_1.csv")
# VRF_df_new = Data2VRFData(df_new)
# print(VRF_df_new.shape)
# VRF_df_new.to_csv("VRF_df_new_15.csv")

# test
# old_df = GetData_fromCSV(["time", "Q_cool"], Q_coolname='Q_old')
# new_df = GetData_fromCSV(["time", "Q_cool"], Q_coolname='Q_new', filename='sys1_Qcool_calc_5Min_6_9.csv')
# df_temp = merge_plot(new_df, old_df, shift_nub=8)
