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
        # 'modata': {
        #     'tag_dict': {'nid': 'vrf/vrf_0000CC311178CCM26232341000271K0V/indoor/0'},
        #     'field_list': ['roomTemp']
        # }
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
            # 启停数据不能mean(), 需要修改
            df_temp = df_temp.resample('15 min').mean()
            df_list.append(df_temp)

data = pd.concat(df_list, axis=1)
column_type = {
    'E': 'Meter',
    'e3': 'T_amb',
    # 'roomTemp': 'T_amb'
}
data



# %% rmol_boxplot
# data_rmol, outlier_indexes = preprocess.rmol_boxplot(data, 288, plot=True)

# subplot_num = len(data_rmol.columns)
# for col, i in zip(data_rmol.columns, range(subplot_num)):
#     outlier = data[col].iloc[outlier_indexes[i]]
#     plt.subplot(subplot_num, 1, i+1)
#     plt.scatter(data_rmol[col].index, data_rmol[col])
#     plt.scatter(outlier.index, outlier)
#     plt.legend([col, col+'_rmol_boxplot'], loc = 'upper left')
# plt.gcf().set_size_inches(12, 6)
# plt.show()


#%% rmol_IF
# data_rmol, outlier_indexes = preprocess.rmol_IF(data)

# subplot_num = len(data_rmol.columns)
# for col, i in zip(data_rmol.columns, range(subplot_num)):
#     outlier = data_rmol[col].iloc[outlier_indexes[i]]
#     plt.subplot(subplot_num, 1, i+1)
#     plt.scatter(data_rmol[col].index, data_rmol[col])
#     plt.scatter(outlier.index, outlier)
#     plt.legend([col, col+'_rmol_IF'], loc = 'upper left')
# plt.gcf().set_size_inches(12, 6)
# plt.show()


#%% rmol_IF_multi
# data_rmol, outlier_index = preprocess.rmol_IF_multi(data)

# outlier = data_rmol.iloc[outlier_index]
# plt.scatter(data_rmol.iloc[:,0], data_rmol.iloc[:,1], color='tab:blue')
# plt.scatter(outlier.iloc[:,0], outlier.iloc[:,1], color='tab:red')
# plt.show()
# subplot_num = len(data_rmol.columns)
# for col, i in zip(data_rmol.columns, range(subplot_num)):
#     plt.subplot(subplot_num, 1, i+1)
#     plt.scatter(data_rmol[col].index, data_rmol[col])
#     plt.scatter(outlier[col].index, outlier[col])
#     plt.legend([col, col+'_rmol_IF'], loc = 'upper left')
# plt.gcf().set_size_inches(12, 6)
# plt.show()




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

process = preprocess.DataPreprocess(data=data, column_type=column_type, **params)

#%%
process.outlier_detect(method='boxplot')
process.impute(method='linear')
process.missing_rate(label='original')
process.missing_rate(label='remove_outlier')
process.missing_rate(label='imputation')

# process.process(rmol_method='boxplot', impute_method='linear')

# %%
