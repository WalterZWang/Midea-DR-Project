# -*- coding: utf-8 -*-
"""
Created on Wed Oct 12 19:48:25 2022

@author: Mingyue Guo
"""
import get_influxDB
import EDA_west as EDA
import matplotlib.pyplot as plt
import PV_pred
data,VRF_rsp, blg_meter_rsp, weather_rsp, PV_meter_rsp, PV_dev_rsp,\
        battery_meter_rsp, battery_dev_rsp, PV_meter, PV_dev = get_influxDB.get_influxDB_main()
        
#EDA
def EDA_func():
    EDA.VRF_msno(VRF_rsp)
    EDA.VRF_device_eda_main(VRF_rsp)
    EDA.weather_msno(weather_rsp)
    EDA.PV_msno(PV_dev_rsp, PV_meter_rsp)
    EDA.battery_msno(battery_dev_rsp, battery_meter_rsp)
    EDA.blg_meter_msno(blg_meter_rsp)
    
def EDA_Temp(VRF_rsp):
    sys= 'VRF_1K0V'
    idu = 'idu_0'
    df = VRF_rsp[sys][idu]
    (df['onOff'] * 200).plot(alpha = 0.5)
    df['exv1Opening'].plot(alpha = 0.5)
    plt.legend()
    
def PV_prediction(PV_meter_rsp):
    target_co = 'Pri_AE'
    predict_cos = ['E_diff']
    x_co = ['solar_radiation',  'Elevation angle', 'Azimuth angle', 'hour', 'zenith_solar'] # 'e3',

    PV_data = PV_pred.pv_meter_proprecess(PV_meter_rsp, weather_rsp)
