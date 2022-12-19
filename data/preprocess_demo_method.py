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
# data['E'] = data['E'].diff()
data



# outlier detection test
#%% od_boxplot, od_sigma
win_size = 4*24*3
data_rmol, outlier_indexes = preprocess.od_boxplot(data, win_size=win_size, remove_outlier=True, plot=True)
# data_rmol, outlier_indexes = preprocess.od_sigma(data, win_size=win_size, remove_outlier=True, plot=True)

subplot_num = len(data_rmol.columns)
for col, i in zip(data_rmol.columns, range(subplot_num)):
    outlier = data[col].iloc[outlier_indexes[i]]
    print(len(outlier))
    plt.subplot(subplot_num, 1, i+1)
    plt.scatter(data_rmol[col].index, data_rmol[col])
    plt.scatter(outlier.index, outlier)
    plt.legend([col, col+'_rmol_boxplot'], loc = 'upper left')
plt.gcf().set_size_inches(12, 6)
plt.show()


#%% od_KD, od_IF
# data_rmol, outlier_indexes = preprocess.od_KD(data, plot=True)
# # data_rmol, outlier_indexes = preprocess.od_IF(data, plot=True)

# subplot_num = len(data_rmol.columns)
# for col, i in zip(data_rmol.columns, range(subplot_num)):
#     outlier = data[col].iloc[outlier_indexes[i]]
#     print(len(outlier))
#     plt.subplot(subplot_num, 1, i+1)
#     plt.scatter(data_rmol[col].index, data_rmol[col])
#     plt.scatter(outlier.index, outlier)
#     plt.legend([col, col+'_rmol_KD'], loc = 'upper left')
# plt.gcf().set_size_inches(12, 6)
# plt.show()


#%% od_IF_multi
# data_rmol, outlier_index = preprocess.od_IF_multi(data, plot=True)

# outlier = data.iloc[outlier_index]
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

# data imputation test
#%% impute_linear
# data_impute = preprocess.impute_linear(data, pd.Timedelta('15 min'), pd.Timedelta('6 hour'), plot=True)

# subplot_num = len(data_impute.columns)
# for col, i in zip(data_impute.columns, range(subplot_num)):
#     plt.subplot(subplot_num, 1, i+1)
#     plt.plot(data_impute[col].index, data_impute[col])
#     plt.plot(data[col].index, data[col])
#     plt.legend([col+'_impute_linear', col], loc = 'upper left')
# plt.gcf().set_size_inches(12, 6)
# plt.show()


#%% impute_KNN
data_impute = preprocess.impute_KNN(data_rmol, plot=True)

subplot_num = len(data_impute.columns)
for col, i in zip(data_impute.columns, range(subplot_num)):
    plt.subplot(subplot_num, 1, i+1)
    plt.plot(data_impute[col].index, data_impute[col])
    plt.plot(data_rmol[col].index, data_rmol[col])
    plt.legend([col+'_impute_KNN', col+'_rmol'], loc = 'upper left')
plt.gcf().set_size_inches(12, 6)
plt.show()


#%% impute_MICE
import numpy as np
from sklearn.experimental import enable_iterative_imputer
from sklearn.impute import IterativeImputer
imp = IterativeImputer(max_iter=10, random_state=0)
imp.fit([[1, 2], [3, 6], [4, 8], [np.nan, 3], [7, np.nan]])
IterativeImputer(random_state=0)

X_test = [[np.nan, 2], [6, np.nan], [np.nan, 6]]
# the model learns that the second feature is double the first
print(np.round(imp.transform(X_test)))

#%%