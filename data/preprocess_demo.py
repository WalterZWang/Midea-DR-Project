#%%
import matplotlib.pyplot as plt
from matplotlib.pylab import mpl
import numpy as np
import pandas as pd
from Influxdb_API.Influxdb_API import ClientInfluxdb
import preprocess


#%% Use the influxdb_API to get data
data_required = {
    'moserveribms': {
        'ibmsV2modata': {
            'tag_dict': {'nid': 'ibmsv2/ibmsv2_5929149262402256896/EMeter/mDev_EMeter_Roof_MDV_10'},
            'field_list': ['E']
        },
        'bridgemodata': {
            'tag_dict': {'nid': 'ibms/ibms_1564376390869024768/microWeatherStation/20201800'},
            'field_list': ['e3']
        }
    },
    'moserver': {
        'modata': {
            'tag_dict': {'nid': 'vrf/vrf_0000CC311178CCM26232341000271K0V/indoor/0'},
            'field_list': ['roomTemp']
        }
    },
}

df_list = []
for key1, value1 in data_required.items():
    for key2, value2 in value1.items():
            db_name_temp = key1
            params_temp = {
                'measurement_name': key2,
                'start_time': pd.to_datetime('2022-07-01 00:00:00'),
                'end_time': pd.to_datetime('2022-10-01 00:00:00'),
                'field_list': value2['field_list'],
                'tag_dict': value2['tag_dict'],
                'fore': False,
                'fore_horizon': None,
                'interval': None
            }
            db_client_temp = ClientInfluxdb(db_name=db_name_temp) 
            df_temp = db_client_temp.read_influxdb(**params_temp)
            # str -> np.float64
            for col in df_temp.columns:
                df_temp[col] = pd.to_numeric(df_temp[col], errors='ignore')
            # resampling data, rsp_time=15min
            # 如果是启停数据重采样不能mean(), 需要修改
            df_temp = df_temp.resample('15 min').mean()
            df_list.append(df_temp)

data = pd.concat(df_list, axis=1)
column_type = {
    'E': 'Meter',
    'e3': 'T_amb',
    'roomTemp': 'T_amb'
}


#%% Recommended to interpolate the meter data before differentiating
data['E'], _ = preprocess.od_boxplot(data['E'].to_frame(), win_size=4*24*3, remove_outlier=True)
data['E'] = preprocess.impute_linear(data['E'].to_frame(), pd.Timedelta('15 min'), pd.Timedelta('12 hour'))
data['E'] = data['E'].diff()
data


#%% Preprocess data
params = {
    # common parameters
    'sampling_time': pd.Timedelta('15 min'),
    'sampling_rate': 4,   # 4 times per hour, depends on sampling_time.

    # parameters of remove outliers
    'win_size': 4*24*7,   # win_size=sampling_rate/h*24h/day*7day, time window size of remove outliers (boxplot, 3-sigma).
    # parameters of data imputation
    'linear_time_delta': pd.Timedelta('4 hours'),   # data missing for more than consecutive linear_time_delta will not be linear imputation.

    # parameters of obtain valid data (by calculating missing rate)
    'ms_thresh': 0.1,   # the condition of missing rate (< ms_thresh) for multiple data.
    'step_min': 4*24*2,   # minimum number of steps needed for training. step=sampling_rate/h*24h/day*2day means to calculate the missing rate 2 days backward at each moment.
    'step_max': 4*24*7,   # maximum number of steps needed for training.
    # 'gap_max': pd.Timedelta('4 hours'),
}

prepro = preprocess.DataPreprocess(data=data, column_type=column_type, **params)
prepro.process(oldt_method='boxplot', impute_method='linear')

# prepro.outlier_detect(method='boxplot')
# prepro.impute(method='linear')


#%% Obtain valid data
data_valid = preprocess.valid_data(prepro.data, label='original', plot=True, **params)
data_valid = preprocess.valid_data(prepro.data_impute, label='imputation', plot=True, **params)


# %%
