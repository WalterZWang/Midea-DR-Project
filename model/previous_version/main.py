# -*- coding: utf-8 -*-
"""
Created on Wed Oct 12 19:48:25 2022

@author: Mingyue Guo
"""
import get_influxDB
# import EDA_west as EDA
import matplotlib.pyplot as plt
import data_processing as dp
import models
#%%
# data process
data,VRF_rsp, blg_meter_rsp, weather_rsp, PV_meter_rsp, PV_dev_rsp,\
        battery_meter_rsp, battery_dev_rsp, PV_meter, PV_dev = get_influxDB.get_influxDB_main()
data_pro = dp.DataProcess(data)

# room data and model
RC_all = dp.RCData(data_pro
                   , analysis_vrf = 'VRF_1K0V'#,'VRF_JSJR'
                   # , neighbor_vrfs = [ 'VRF_1K0V', 'VRF_87JG', 'VRF_J8UW']
                   , neighbor_vrfs = ['VRF_JSJR']
                   )
room_model = models.RoomModel(RC_all)
errors, para_identification, paras_mean = room_model.RC_model_train()
# need to train first to get the parameters
room_pred = room_model.RC_model_predict(RC_all.valid_list[-1])

# VRF data and model
VRF_model_data = dp.VRFData(data_pro, analysis_vrf = 'VRF_1K0V')
VRF_model = models.VRFModel(VRF_model_data)
VRF_pred, VRF_pred_err = VRF_model.VRF_model_train()
# need to train first to get the model
VRF_pred = VRF_model.VRF_model_pred(VRF_model_data.X_test_list[0]
                                                  , VRF_model_data.y_test_list[0])

# PV data
PV_data = dp.PVData(data_pro, predict_day = '2022-09-06'
                 , stage = 'train')
PV_model = models.PVModel(PV_data)

#EDA
# def EDA_func():
#     EDA.VRF_msno(VRF_rsp)
#     EDA.VRF_device_eda_main(VRF_rsp)
#     EDA.weather_msno(weather_rsp)
#     EDA.PV_msno(PV_dev_rsp, PV_meter_rsp)
#     EDA.battery_msno(battery_dev_rsp, battery_meter_rsp)
#     EDA.blg_meter_msno(blg_meter_rsp)
    
# def EDA_Temp(VRF_rsp):
#     sys= 'VRF_1K0V'
#     idu = 'idu_0'
#     df = VRF_rsp[sys][idu]
#     (df['onOff'] * 200).plot(alpha = 0.5)
#     df['exv1Opening'].plot(alpha = 0.5)
#     plt.legend()
    
# def PV_prediction(PV_meter_rsp):
#     target_co = 'Pri_AE'
#     predict_cos = ['E_diff']
#     x_co = ['solar_radiation',  'Elevation angle', 'Azimuth angle', 'hour', 'zenith_solar'] # 'e3',

#     PV_data = PV_pred.pv_meter_proprecess(PV_meter_rsp, weather_rsp)
