#%%
import matplotlib.pyplot as plt
from matplotlib.pylab import mpl
import numpy as np
import pandas as pd
from Influxdb_API.Influxdb_API import ClientInfluxdb
import preprocess


#%% Use the influxdb_API to get data
data_required = {
    'moserveribms': {'ibmsV2modata': {'tag_dict': {'nid': 'ibmsv2/ibmsv2_5929149262402256896/EMeter/mDev_EMeter_Roof_MDV_10'},
                                    'field_list': ['E']
                    },
                    'bridgemodata': {'tag_dict': {'nid': 'ibms/ibms_1564376390869024768/microWeatherStation/20201800'},
                                    'field_list': ['e3']
                    }
    },
    'moserver': {'modata': {'tag_dict': {'nid': 'vrf/vrf_0000CC311178CCM26232341000271K0V/indoor/0'},
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
            # 启停数据不能mean()
            df_temp = df_temp.resample('15 min').mean()
            df_list.append(df_temp)

data = pd.concat(df_list, axis=1)
column_type = {
    'E': 'Meter',
    'e3': 'T_amb',
    'roomTemp': 'T_amb'
}
data

#%%
params = {
    # common parameters
    'sampling_time': pd.Timedelta('15 min'),
    'sampling_rate': 4,   # 4 times per hour, depends on sampling_time
    # parameters of calculate missing rate
    'step': 4*24*3,    # step=4/h*24h/day*3day means to calculate the missing rate three days forward at each moment
    'ms_thresh': 0.2,   # the condition of missing rate (< ms_thresh) for multiple data
    # parameters of remove outliers
    'win_size': 4*24*3,   # window_size of remove outliers by boxplot
    # parameters of data imputation
    'linear_time_delta': pd.Timedelta('6 hours'),   # data missing for more than consecutive linear_time_delta will not be linear imputation
}

process = preprocess.DataPreprocess(data = data, column_type = column_type, **params)

# process.remove_outlier(method='boxplot')
# process.impute(method='linear')
# process.missing_rate(label='original')
# process.missing_rate(label='remove_outlier')
# process.missing_rate(label='imputation')

# process.process(rmol_method='boxplot', impute_method='linear')

# %%
