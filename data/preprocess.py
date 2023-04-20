"""
Script for data pre_processing

Major parts:
- data_preprocess class
- identify the valid data for model training
- outlier detection function
- data imputation function

If needed, can be splitted into multiple files

Created on Tue Dec 13 15:14:50 2022
Last updated on 
@author: Zhenyu WANG (wangzhy237@mail2.sysu.edu.cn)
"""

import matplotlib.pyplot as plt
from matplotlib.pylab import mpl
import numpy as np
import pandas as pd
import copy
import seaborn as sns

from Influxdb_API.Influxdb_API import ClientInfluxdb
# import rc_model_1k0v2


#%% data_preprocessing class
class DataPreprocess(object):

    # common parameters
    sampling_time = pd.Timedelta('15 min')
    sampling_rate = 4   # 4 times per hour, depends on sampling time
    # parameters of outlier detect
    kd_bandwidth = 1
    kd_ratio = 0.005
    abrupt_win_size = 5
    abrupt_thresh = 2.5

    linear_time_delta = {
        'Ti': '4 hours',
        'Ta': '4 hours',
        'Qs': '4 hours',
        'Qin': '4 hours',
        'Qac': '0.5 hours',
    }
    

    def __init__(self, data:pd.DataFrame, column_type:dict, data_range:dict, **kw):
        '''
        data: dataframe,
            Data to be preprocessed
        column_type: dictionary
            The outlier detection and data algoirthms vary for different type of data
            Key is the column name
            Value is the data type, currently we support the following types {'T_amb', 'T_sys', 'Sys', 'Meter', 'Other'}, standing for
                - T_amb: ambient temperature, including the room and outdoor temperature
                - T_sys: system related temperature, including the evaporative temperature, condensing temperature, ...
                - Sys: system operational data, including the operations such as start and stop, the value is discrete like 0-1
                - Meter: electrical and power meter data
                - Other: other data types
        data_range: dictionary
            The reasonable physical range of data for each column.
        linear_time_delta: dictionary
            Data missing that is larger than the linear_time_delta will not be imputed.
        '''
        assert len(column_type) == len(data.columns), f"Specify the column type for each column, valid types are: 'T_amb', 'T_sys', 'Sys', 'Meter', 'Other'."
        
        self.column_type = column_type
        self.data_range = data_range

        self.data = data
        self.data_rmol = None
        self.data_rmol_impute = None
        self.data_impute = None

        for param, value in kw.items():
            setattr(self, param, value)


    def outlier_detect(self, method=None, remove_outlier=True, **kw) -> None:
        '''
        Remove outliers.
        method=None means to use the combined method.
        '''
        self.data_rmol = copy.deepcopy(self.data)
        assert self.data_rmol is not None, "Plese verify the original data is not empty."

        if method is None:
            self.data_rmol, index1 = od_negative(self.data_rmol, self.column_type)
            self.data_rmol, index2 = od_range(self.data_rmol, data_range=self.data_range)
            self.data_rmol, index3 = od_KD(self.data_rmol, bandwidth=self.kd_bandwidth ,ratio=self.kd_ratio, remove_outlier=remove_outlier)
            self.data_rmol, index4 = od_abrupt(self.data_rmol, self.column_type, win_size=self.abrupt_win_size, thresh=self.abrupt_thresh, remove_outlier=remove_outlier)

            self.outlier_indexes = []
            for i in range(self.data.shape[1]):
                self.outlier_indexes.append(np.concatenate((index1[i], index2[i], index3[i], index4[i])))

        elif method == 'boxplot':
            self.data_rmol, self.outlier_indexes = od_boxplot(self.data_rmol)

        elif method == 'n-sigma':
            self.data_rmol, self.outlier_indexes = od_sigma(self.data_rmol)

        elif method == 'kernal_density':
            self.data_rmol, self.outlier_indexes = od_KD(self.data_rmol, bandwidth=self.kd_bandwidth ,ratio=self.kd_ratio, remove_outlier=remove_outlier)


    def impute(self, method='linear', **kw) -> None:

        if self.data is not None: self.data_impute = copy.deepcopy(self.data)
        if self.data_rmol is not None: self.data_rmol_impute = copy.deepcopy(self.data_rmol)
        assert self.data_impute is not None, "Please verify the original data is not empty."

        sampling_time = self.sampling_time
        linear_time_delta = self.linear_time_delta
        assert linear_time_delta is not None, "Please input the maximum interval for linear interpolation of each column."

        if method is None:
            pass
            # self.data_impute = impute_linear(self.data_impute, sampling_time, linear_time_delta)
            # self.data_rmol_impute = impute_linear(self.data_rmol_impute, sampling_time, linear_time_delta)
            # self.data_impute = impute_KNN(self.data_impute, period_num=4*24*7)
            # self.data_rmol_impute = impute_KNN(self.data_rmol_impute, period_num=4*24*7)

        elif method == 'linear':
            self.data_impute = impute_linear(self.data_impute, sampling_time, linear_time_delta)
            self.data_rmol_impute = impute_linear(self.data_rmol_impute, sampling_time, linear_time_delta)

        elif method == 'KNN':
            self.data_impute = impute_KNN(self.data_impute, period_num=4*24*7)
            self.data_rmol_impute = impute_KNN(self.data_rmol_impute, period_num=4*24*7)

        elif method == 'MICE':
            pass
        else: assert False, "Please enter the correct method: 'linear', 'KNN', 'MICE'."


    def process(self, oldt_method=None, impute_method='linear') -> None:
        '''
        oldt_method = ['boxplot', 'n-sigma', 'kernal_density'].
        impute_method = ['linear', 'KNN', 'MICE'].
        '''
        self.outlier_detect(method=oldt_method, remove_outlier=True)
        self.impute(method=impute_method)


    def evaluate(self) -> float:
        pass



#%% Obtain the valid data set for training
def valid_data(df:pd.DataFrame, mode:str, interval_min_day:float, interval_max_day:float, \
    sampling_time:pd.Timedelta, sampling_rate:float, ms_thresh=0.0, label='original', verbose='more', plot=False, **kw) -> pd.DataFrame:
    '''
    Obtain valid data by calculating missing rate.

    Parameters
    -----
    df: data to be searched.
    mode: ['closest', 'longset'].
    interval_min_day: minimum number of days needed for training. 
    interval_max_day: maximum number of days needed for training.
    sampling_time: the sampling interval of the data.
    sampling_rate: number of samples per hour.
    ms_thresh: missing rate thresh.
    verbose: ['more', 'less']

    Return
    -----
    if mode=='closest':
        return valid data closest to the current time try to meet ms_thresh and interval_min_day.
    if mode=='longest':
        return valid data longest try to meet ms_thresh and interval_max_day.
    '''
    from pandas.api.indexers import FixedForwardWindowIndexer

    data = df
    data_valid = None

    # if mode == 'closest':
    #     step = int(sampling_rate*24*interval_min_day)
    #     missing_rate, _, _ = cal_missing_rate(data, sampling_time, step, ms_thresh)
    #     ms_multi = missing_rate[missing_rate <= ms_thresh]
    #     ms_multi = ms_multi.dropna()

    #     # filtering data using non-zero rate of cooling capacity
    #     nonzero_rate = pd.DataFrame(data=None, index=data.index, columns=data.columns)
    #     for col in data.columns:
    #         nonzero_rate[col] = (data!=0)[col].rolling(step, min_periods=0).sum() / float(step)
    #     closest_time = None
    #     for i in range(len(ms_multi)-1, -1, -1):
    #         time = ms_multi.index[i]
    #         if nonzero_rate['Qac'][time] > 0.05:
    #             closest_time = time
    #             break
 
    #     if closest_time is not None:
    #         # ms_results['closest_time_multi'] = closest_time.strftime('%Y-%m-%d %H:%M:00')[0]
    #         closest_time_back = closest_time - sampling_time*(step-1)
    #         # data_valid = data[closest_time_back.strftime('%Y-%m-%d %H:%M:00')[0]: closest_time.strftime('%Y-%m-%d %H:%M:00')[0]]
    #         data_valid = data[(data.index >= closest_time_back) & (data.index <= closest_time)]

    #         days_backward = round(step/sampling_rate/24, 2)
    #         print(f'{label}, the closest moment meets the condition (missing rate <= {ms_thresh}, {days_backward} days) for multiple data: ', closest_time, '\n------------------\n\n')
    #             # else:
    #             #     print(f'{key} {label}, the closest optimal moment to the present: ', value, '\n------------------')
    #         if plot:
    #             # data.plot(title=f'Measurement data ({label})', figsize=(12,6))
    #             # plt.legend(loc = 'upper left')
    #             missing_rate.plot(title=f'Missing Rate ({days_backward} days backward) ({label})', figsize=(12,6))
    #             plt.legend(loc = 'upper left')
    #             data_valid.plot(title=f'Data meets condition (missing rate <= {ms_thresh}, {days_backward} days backward) ({label})', figsize=(12,6))
    #             plt.legend(loc = 'upper left')
    #             plt.ylim(-10, 50)
    #             plt.show()
    #     if closest_time is None:
    #         print(f'{label}, there is no moment meets the condition (missing rate <= {ms_thresh}, {interval_min_day} days backward) for multiple data.', '\n------------------\n\n')

    if mode == 'closest':
        step = int(sampling_rate*24*interval_min_day)
        missing_rate, data_mc, ms_results = cal_missing_rate(data, sampling_time, step, ms_thresh)
        if data_mc is not None:
            data_valid = data_mc
            days_backward = round(step/sampling_rate/24, 2)
            for key, value in ms_results.items():
                if key == 'closest_time_multi':
                    print(f'{label}, the closest moment meets the condition (missing rate <= {ms_thresh}, {days_backward} days) for multiple data: ', ms_results['closest_time_multi'], '\n------------------\n\n')
                else:
                    if verbose == 'more':
                        print(f'{key} {label}, the closest optimal moment to the present: ', value, '\n------------------')
            if plot:
                # data.plot(title=f'Measurement data ({label})', figsize=(12,6))
                # plt.legend(loc = 'upper left')
                missing_rate.plot(title=f'Missing Rate ({days_backward} days backward) ({label})', figsize=(12,6))
                plt.legend(loc = 'upper left')
                data_mc.plot(title=f'Data meets condition (missing rate <= {ms_thresh}, {days_backward} days backward) ({label})', figsize=(12,6))
                plt.legend(loc = 'upper left')
                plt.ylim(-10, 100)
                plt.show()
        if data_mc is None:
            print(f'{label}, there is no moment meets the condition (missing rate <= {ms_thresh}, {interval_min_day} days backward) for multiple data.', '\n------------------\n\n')

    if mode == 'longest':
        # step = sampling_rate/h*24h/day*ndays means to calculate the missing rate n days backward at each moment
        step_min = int(sampling_rate*24*interval_min_day)
        step_max = int(sampling_rate*24*interval_max_day)
        # from step_max to step_min, if have multiple data meets the ms_thresh, break and return.
        for step in range(step_max, step_min-1, -1):
            missing_rate, data_mc, ms_results = cal_missing_rate(data, sampling_time, step, ms_thresh)
            if data_mc is not None:
                data_valid = data_mc
                days_backward = round(step/sampling_rate/24, 2)
                for key, value in ms_results.items():
                    if key == 'closest_time_multi':
                        print(f'{label}, the closest moment meets the condition (missing rate <= {ms_thresh}, {days_backward} days) for multiple data: ', ms_results['closest_time_multi'], '\n------------------\n\n')
                    else:
                        if verbose == 'more':
                            print(f'{key} {label}, the closest optimal moment to the present: ', value, '\n------------------')
                if plot:
                    # data.plot(title=f'Measurement data ({label})', figsize=(12,6))
                    # plt.legend(loc = 'upper left')
                    missing_rate.plot(title=f'Missing Rate ({days_backward} days backward) ({label})', figsize=(12,6))
                    plt.legend(loc = 'upper left')
                    data_mc.plot(title=f'Data meets condition (missing rate <= {ms_thresh}, {days_backward} days backward) ({label})', figsize=(12,6))
                    plt.legend(loc = 'upper left')
                    plt.ylim(-10, 100)
                    plt.show()
                break
            if data_mc is None and step==step_min:
                print(f'{label}, there is no moment meets the condition (missing rate <= {ms_thresh}, {interval_min_day} days backward) for multiple data.', '\n------------------\n\n')

    return data_valid


def valid_data2(df:pd.DataFrame, interval_min_day:float, interval_max_day:float, \
    sampling_time:pd.Timedelta, sampling_rate:float, ms_thresh=0.0, label='original', **kw) -> list:
    '''
    Return all data fragments that meets the interval_min_day and ms_thresh requirement.

    Parameters
    -----
    df: data to be searched.
    interval_min_day: minimum number of days needed for training. 
    interval_max_day: maximum number of days needed for training.
    sampling_time: the sampling interval of the data.
    sampling_rate: number of samples per hour.
    ms_thresh: missing rate thresh.

    Return
    -----
    data_valid_list: all data fragments that meets the interval_min_day and ms_thresh requirement.
    '''
    data = df
    data_valid_list = []

    step_min = int(sampling_rate*24*interval_min_day)
    step_max = int(sampling_rate*24*interval_max_day)
    for step in range(step_max, step_min-1, -1):
        missing_rate, _, _ = cal_missing_rate(data, sampling_time, step, ms_thresh)
        # 获取每一行数据的missing_rate都小于ms_thresh的所有数据
        ms_multi = missing_rate[missing_rate <= ms_thresh]
        ms_multi = ms_multi.dropna()
        for time in ms_multi.index:
            time_back = time - sampling_time*(step-1)
            flag = True
            for data_acquired in data_valid_list:
                if (time_back >= data_acquired.index[0]) and (time <= data_acquired.index[-1]):
                    flag = False
                    break
            if flag:
                data_valid = data[(data.index >= time_back) & (data.index <= time)]
                data_valid_list.append(data_valid)

        if len(data_valid_list)==0 and step==step_min:
            print(f'{label}, there is no moment meets the condition (missing rate <= {ms_thresh}, {interval_min_day} days backward) for multiple data.', '\n------------------\n\n')

    return data_valid_list


def cal_missing_rate(df:pd.DataFrame, sampling_time:pd.Timedelta, step:int, ms_thresh:float, **kw) -> (pd.DataFrame, pd.DataFrame, dict):
    '''
    Calculate the missing rate of n steps backward at each moment.

    Parameters
    -----
    df: data to be searched.
    sampling_time: the sampling interval of the data.
    step: n steps backward.
    ms_thresh: missing rate thresh.

    Return
    -----
    missing_rate: missing rate of data.
    data_mc: the closest data meets the condition (missing rate <= ms_thresh) for multivariable.
    ms_results: the closest optimal time for univariable, the closest time meets the condition (missing rate <= ms_thresh) for multivariable.
    '''

    data = df

    missing_rate = pd.DataFrame(data=None, index=data.index, columns=data.columns)
    data_mc = None
    ms_results = {}

    for col in data.columns:
        missing_rate[col] = 1 - (data[col].rolling(step, min_periods=0).count() / float(step))
    for col in data.columns:
        # 获取具有最小missing_rate的所有时刻
        min_index = np.where(missing_rate[col] == missing_rate[col].min())
        # 获得具有最小missing_rate的最近的时刻
        best_time = missing_rate[col].iloc[min_index[0]].tail(1).index
        ms_results[col] = best_time.strftime('%Y-%m-%d %H:%M:00')[0] + ' (minimum missing rate: ' + str(missing_rate[col].min()) + ')'
    # 当包含多组数据时
    if len(data.columns) > 1:
        # 获取每一行数据的missing_rate都小于ms_thresh的所有数据
        ms_multi = missing_rate[missing_rate <= ms_thresh]
        ms_multi = ms_multi.dropna()
        # 所有数据满足距离当前时间最近的n天缺失率低于ms_thresh的时刻
        closest_time = ms_multi.tail(1).index            
        if any(closest_time):
            ms_results['closest_time_multi'] = closest_time.strftime('%Y-%m-%d %H:%M:00')[0]
            # 获取满足条件的多通道数据
            closest_time_back = closest_time - sampling_time*(step-1)
            data_mc = data[closest_time_back.strftime('%Y-%m-%d %H:%M:00')[0]: closest_time.strftime('%Y-%m-%d %H:%M:00')[0]]

    return missing_rate, data_mc, ms_results


def pattern_anomaly(df_list:list, len_train:int, len_valid:int) -> list:
    '''
    Determine whether the pattern of data fragment is anomaly.
    Using non-zero rate of cooling capacity (Qac).

    Parameters
    -----
    df_list: data_frame list (Obtained these data by valid_data2())
    len_train: step length of training data (e.g. room model)
    len_valid: step length of valid data

    Return
    -----
    good_time: time for good data fragments
    '''
    from pandas.api.indexers import FixedForwardWindowIndexer

    good_time = []
    for data in df_list:
        nonzero_rate = pd.DataFrame(data=None, index=data.index, columns=data.columns)
        for col in data.columns:
            nonzero_rate[col] = (data!=0)[col].rolling(FixedForwardWindowIndexer(window_size=len_train), min_periods=1).sum() / float(len_train)
        
        for i in range(0, len(data) - (len_train + len_valid - 1), len_valid):
            if nonzero_rate['Qac'].iloc[i] > 0.05:
                good_time.append(nonzero_rate.iloc[i:i+1].index)

    return good_time


#%% outlier detection functions
def od_ensemble(df):
    pass


def od_negative(df:pd.DataFrame, column_type:dict, **kw) -> pd.DataFrame:
    '''
    Replace negative values with 0 for data of specific column type.

    Parameters
    -----
    df: Dataframe.
    column_type: The type of data for each column.

    Return
    -----
    data: Data with negative values replaced.
    outlier_indexes: outliers' indexes of original data.
    '''

    data = copy.deepcopy(df)

    outlier_indexes = []
    for col in data.columns:
        if column_type[col] in ['Meter', 'Other']: 
            outlier_index = np.where(data[col] < 0)[0]
            outlier_indexes.append(outlier_index)
            data[col].iloc[outlier_index] = 0
            # data[col].loc[data[col] < 0] = 0
        else:
            outlier_indexes.append(np.array([]))

    return data, outlier_indexes


def od_range(df:pd.DataFrame, data_range:dict, **kw) -> pd.DataFrame:
    '''
    Replace out-of-range values with Nan.

    Parameters
    -----
    df: Dataframe.
    data_range: The reasonable physical range of data for each column.

    Return
    -----
    Data with out-of-range values removed.
    outlier_indexes: outliers' indexes of original data.
    '''

    data = copy.deepcopy(df)

    outlier_indexes = []
    for col in data.columns:
        lower_bound = data_range[col][0]
        upper_bound = data_range[col][1]
        outlier_index = np.where((data[col] > upper_bound) | (data[col] < lower_bound))[0]
        outlier_indexes.append(outlier_index)
        data[col].iloc[outlier_index] = np.nan

    return data, outlier_indexes


def od_abrupt(df:pd.DataFrame, column_type:dict, win_size=5, thresh=2.5, remove_outlier=True, **kw) -> pd.DataFrame:
    '''
    Remove local abrupt changes by mean.

    Parameters
    -----
    df: Dataframe.
    column_type: the type of data for each column.
    win_size: window size.
    thresh: abrupt thresh.
    remove_outlier: whether to remove outliers from the data.

    Return
    -----
    data: data removed outliers (remove_outlier=True) / original data (remove_outlier=False).
    outlier_indexes: outliers' indexes of original data.
    '''

    data = copy.deepcopy(df)

    data_mean = data.rolling(win_size, center=True).mean()
    data_mean_diff = (data - data_mean).fillna(0)

    outlier_indexes = []
    for col in data.columns:
        if column_type[col] in ['T_amb']: 
            # np.where return a tuple
            outlier_index = np.where(abs(data_mean_diff[col])>thresh)[0]
            outlier_indexes.append(outlier_index)
            if remove_outlier:
                data[col].iloc[outlier_index] = np.nan
        else:
            outlier_indexes.append(np.array([]))

    return data, outlier_indexes


def od_boxplot(df:pd.DataFrame, thresh=2, win_size=None, remove_outlier=True, **kw) -> (pd.DataFrame, list):
    '''
    Remove outliers by boxplot (univariable).

    Parameters
    -----
    df: Dataframe.
    win_size: window size, 'win_size == None' means no window.
    thresh: determining the margins of the boxplot.
    remove_outlier: whether to remove outliers from the data.

    Return
    -----
    data: data removed outliers (remove_outlier=True) / original data (remove_outlier=False).
    outlier_indexes: outliers' indexes of original data.
    '''

    data = copy.deepcopy(df)
    
    # 'win_size == None' means 'win_size == time period for all data'
    if not win_size:
        Q1 = data.quantile(0.25)
        Q3 = data.quantile(0.75)
    else:
        Q1 = data.rolling(win_size, center=True, min_periods=1).quantile(0.25)
        Q3 = data.rolling(win_size, center=True, min_periods=1).quantile(0.75)
    IQR = Q3 - Q1
    min = Q1 - thresh*IQR
    max = Q3 + thresh*IQR

    outlier_indexes = []
    for col in data.columns:
        outlier_index = np.where((data[col]<min[col]) | (data[col]>max[col]))[0]
        outlier_indexes.append(outlier_index)
        if remove_outlier:
            data[col].iloc[outlier_index] = np.nan

    return data, outlier_indexes


def od_sigma(df:pd.DataFrame, thresh=3, win_size=None, remove_outlier=True, **kw) -> (pd.DataFrame, list):
    '''
    Remove outliers by n-sigma (univariable), data should follow normal distribution.

    Parameters
    -----
    df: Dataframe.
    win_size: window size, 'win_size == None' means no window.
    thresh: determining the 'n' of 'n-sigma'.
    remove_outlier: whether to remove outliers from the data.

    Return
    -----
    data: data removed outliers (remove_outlier=True) / original data (remove_outlier=False).
    outlier_indexes: outliers' indexes of original data.
    '''

    data = copy.deepcopy(df)

    # 'win_size == None' means 'win_size == time period for all data'
    if not win_size:
        std = data.std()
        mean = data.mean()
    else:
        std = data.rolling(win_size, center=True, min_periods=1).std()
        mean = data.rolling(win_size, center=True, min_periods=1).mean()

    outlier_indexes = []
    for col in data.columns:
        outlier_index = np.where(abs(data[col] - mean[col]) > thresh*std[col])[0]
        outlier_indexes.append(outlier_index)
        if remove_outlier:
            data[col].iloc[outlier_index] = np.nan

    return data, outlier_indexes


def od_KD(df:pd.DataFrame, bandwidth=1, ratio=0.0005, remove_outlier=True, **kw) -> (pd.DataFrame, list):
    '''
    Remove outliers by Kernal Density Estimation (univariable).

    Parameters
    -----
    df: Dataframe.
    bandwidth: band width of the kenal function.
    ratio: the ratio of outliers.
    remove_outlier: whether to remove outliers from the data.

    Return
    -----
    data: data removed outliers (remove_outlier=True) / original data (remove_outlier=False).
    outlier_indexes: outliers' indexes of original data.
    '''

    from sklearn.neighbors import KernelDensity
    data = copy.deepcopy(df)

    outlier_indexes = []
    for col in data.columns:
        col_dropna = data[col].replace([np.inf, -np.inf], np.nan).to_frame().dropna()
        kern_dens = KernelDensity(kernel='gaussian', bandwidth=bandwidth)
        kern_dens.fit(col_dropna)
        scores = kern_dens.score_samples(col_dropna)
        threshold = np.quantile(scores, ratio)
        outlier_dateindex = col_dropna.iloc[np.where(scores<=threshold)].index

        outlier_index = data[col].index.get_indexer(outlier_dateindex)
        outlier_indexes.append(outlier_index)
        if remove_outlier:
            data[col].iloc[outlier_index] = np.nan

    return data, outlier_indexes


def od_IF(df:pd.DataFrame, n_estimators=100, ratio=0.0005, remove_outlier=True, mode='multi', **kw) -> (pd.DataFrame, list):
    '''
    Remove outliers by Isolation Forest (univariable / multivariable).

    Parameters
    -----
    df: Dataframe.
    ratio: the ratio of outliers.
    remove_outlier: whether to remove outliers from the data.
    mode: ['uni', 'multi'].

    Return
    -----
    data: data removed outliers (remove_outlier=True) / original data (remove_outlier=False).
    outlier_index: outliers' indexes of original data.
    '''
    
    from sklearn.ensemble import IsolationForest

    data = copy.deepcopy(df)
    data_dropna = data.dropna()

    if mode == 'uni':
        outlier_indexes = []
        for col in data.columns:
            col_dropna = data[col].to_frame().dropna()
            IF = IsolationForest(n_estimators=n_estimators, contamination=ratio)
            predictions = IF.fit_predict(col_dropna.values)
            outlier_dateindex = col_dropna.iloc[np.where(predictions==-1)].index

            outlier_index = data[col].index.get_indexer(outlier_dateindex)
            outlier_indexes.append(outlier_index)
            if remove_outlier:
                data[col].iloc[outlier_index] = np.nan

        return data, outlier_indexes

    IF = IsolationForest(n_estimators=n_estimators, contamination=ratio)
    predictions = IF.fit_predict(data_dropna.values)
    outlier_dateindex = data_dropna.iloc[np.where(predictions==-1)].index
    outlier_index = data.index.get_indexer(outlier_dateindex)
    if remove_outlier:
        data.iloc[outlier_index] = np.nan

    outlier_indexes = []
    for i in range(data.shape[1]):
        outlier_indexes.append(outlier_index)

    return data, outlier_indexes 


def od_LOF(df:pd.DataFrame, n_neighbors=20, ratio=0.0005, remove_outlier=True, **kw) -> (pd.DataFrame, list):
    '''
    Remove outliers by LOF (multivariable).

    Parameters
    -----
    df: Dataframe.
    ratio: the ratio of outliers.
    remove_outlier: whether to remove outliers from the data.

    Return
    -----
    data: data removed outliers (remove_outlier=True) / original data (remove_outlier=False).
    outlier_index: outliers' indexes of original data.
    '''
    from sklearn.neighbors import LocalOutlierFactor

    data = copy.deepcopy(df)
    data_dropna = data.dropna()

    LOF = LocalOutlierFactor(n_neighbors=n_neighbors, contamination=ratio)
    predictions = LOF.fit_predict(data_dropna)
    outlier_dateindex = data_dropna.iloc[np.where(predictions==-1)].index
    outlier_index = data.index.get_indexer(outlier_dateindex)
    if remove_outlier:
        data.iloc[outlier_index] = np.nan
    
    outlier_indexes = []
    for i in range(data.shape[1]):
        outlier_indexes.append(outlier_index)

    return data, outlier_indexes


def od_SVM(df:pd.DataFrame, ratio=0.0005, remove_outlier=True, mode='multi', **kw) -> (pd.DataFrame, list):
    '''
    Remove outliers by One-Class SVM (univariable / multivariable).

    Parameters
    -----
    df: Dataframe.
    remove_outlier: whether to remove outliers from the data.
    mode: ['uni', 'multi'].

    Return
    -----
    data: data removed outliers (remove_outlier=True) / original data (remove_outlier=False).
    outlier_index: outliers' indexes of original data.
    '''
    from sklearn.svm import OneClassSVM

    data = copy.deepcopy(df)
    data_dropna = data.dropna()

    if mode == 'uni':
        outlier_indexes = []
        for col in data.columns:
            col_dropna = data[col].to_frame().dropna()
            SVM = OneClassSVM(gamma='auto', nu=ratio)
            predictions = SVM.fit_predict(col_dropna)
            outlier_dateindex = col_dropna.iloc[np.where(predictions==-1)].index

            outlier_index = data[col].index.get_indexer(outlier_dateindex)
            outlier_indexes.append(outlier_index)
            if remove_outlier:
                data[col].iloc[outlier_index] = np.nan

        return data, outlier_indexes

    SVM = OneClassSVM(gamma='auto', nu=ratio, tol=1e-6)
    predictions = SVM.fit_predict(data_dropna)
    outlier_dateindex = data_dropna.iloc[np.where(predictions==-1)].index
    outlier_index = data.index.get_indexer(outlier_dateindex)
    if remove_outlier:
        data.iloc[outlier_index] = np.nan

    outlier_indexes = []
    for i in range(data.shape[1]):
        outlier_indexes.append(outlier_index)

    return data, outlier_indexes


def od_SVM_SGD(df:pd.DataFrame, ratio=0.0005, remove_outlier=True, mode='multi', **kw) -> (pd.DataFrame, list):
    '''
    Remove outliers by linear One-Class SVM using Stochastic Gradient Descent (univariable / multivariable).

    Parameters
    -----
    df: Dataframe.
    remove_outlier: whether to remove outliers from the data.
    mode: ['uni', 'multi'].

    Return
    -----
    data: data removed outliers (remove_outlier=True) / original data (remove_outlier=False).
    outlier_index: outliers' indexes of original data.
    '''
    from sklearn.linear_model import SGDOneClassSVM

    data = copy.deepcopy(df)
    data_dropna = data.dropna()
    
    if mode == 'uni':
        outlier_indexes = []
        for col in data.columns:
            col_dropna = data[col].to_frame().dropna()
            SVMSGD = SGDOneClassSVM(nu=ratio)
            predictions = SVMSGD.fit_predict(col_dropna)
            outlier_dateindex = col_dropna.iloc[np.where(predictions==-1)].index

            outlier_index = data[col].index.get_indexer(outlier_dateindex)
            outlier_indexes.append(outlier_index)
            if remove_outlier:
                data[col].iloc[outlier_index] = np.nan

        return data, outlier_indexes

    SVMSGD = SGDOneClassSVM(nu=ratio)
    predictions = SVMSGD.fit_predict(data_dropna)
    outlier_dateindex = data_dropna.iloc[np.where(predictions==-1)].index
    outlier_index = data.index.get_indexer(outlier_dateindex)
    if remove_outlier:
        data.iloc[outlier_index] = np.nan

    outlier_indexes = []
    for i in range(data.shape[1]):
        outlier_indexes.append(outlier_index)

    return data, outlier_indexes



#%% data imputation functions
def impute_linear(df:pd.DataFrame, sampling_time:pd.Timedelta, linear_time_delta:dict, plot=False, **kw) -> pd.DataFrame:
    '''
    Impute data by linear interpolation (univariable).

    Parameters
    -----
    df: data to be imputed.
    sampling_time: the sampling interval of the data.
    linear_time_delta: data missing that is larger than the linear_time_delta will not be imputed.

    Return
    -----
    data: data imputed.
    '''

    def temp(series, sampling_time, linear_time_delta):
        # 获取空值索引
        series_nan = series[series.isna()]
        series_nan_index = series_nan.index
        if series_nan_index.empty: return None
        # 获取小于等于imputation_time_delta的空值索引
        series_imputation_list = []
        start = series_nan_index[0]
        temp = series_nan_index[0]
        end = series_nan_index[0]
        for i in range(len(series_nan_index)-1):
            end = series_nan_index[i+1]
            if (end-temp) == sampling_time:
                temp = end
            else:
                if ((temp - start) <= linear_time_delta) and (start!=series.head(1).index and end!=series.tail(1).index):
                    series_imputation_list.append([start, temp])
                start = end
                temp = end
        if ((temp - start) <= linear_time_delta) and (start!=series.head(1).index and end!=series.tail(1).index):
            series_imputation_list.append([start, temp])
        
        return series_imputation_list
            
    data = copy.deepcopy(df)

    for col in data.columns:
        delta = pd.Timedelta(linear_time_delta[col])
        series = data[col]
        series_imputation_list = temp(series, sampling_time=sampling_time, linear_time_delta=delta)
        if series_imputation_list is None: continue
        for imputation in series_imputation_list:
            data[col].loc[imputation[0]-sampling_time: imputation[1]+sampling_time] = \
                series.loc[imputation[0]-sampling_time: imputation[1]+sampling_time].interpolate(method='polynomial', order=1)
            
        # series = data[col]
        # # 获取空值索引
        # series_nan = series[series.isna()]
        # series_nan_index = series_nan.index
        # if series_nan_index.empty: continue
        # # 获取小于imputation_time_delta的空值索引
        # series_imputation_list = []
        # start = series_nan_index[0]
        # temp = series_nan_index[0]
        # end = series_nan_index[0]
        # for i in range(len(series_nan_index)-1):
        #     end = series_nan_index[i+1]
        #     if (end-temp) == sampling_time:
        #         temp = end
        #     else:
        #         if ((temp - start) <= linear_time_delta) and (start!=series.head(1).index and end!=series.tail(1).index):
        #             series_imputation_list.append([start, temp])
        #         start = end
        #         temp = end
        # if ((temp - start) <= linear_time_delta) and (start!=series.head(1).index and end!=series.tail(1).index):
        #     series_imputation_list.append([start, temp])
        # # 对满足imputation_time_delta的空值进行线性插值
        # for imputation in series_imputation_list:
        #     data[col].loc[imputation[0]-sampling_time: imputation[1]+sampling_time] = \
        #         series.loc[imputation[0]-sampling_time: imputation[1]+sampling_time].interpolate(method='polynomial', order=1)

    if plot:
        df.plot(subplots=True, title='data (original)')
        data.plot(subplots=True, title='data (imputation_linear)')
        plt.show()

    return data


def impute_KNN(df:pd.DataFrame, period_num=4*24*7*2, plot=False, **kw) -> pd.DataFrame:
    '''
    Impute data by K-Nearest Neighbor (multivariable).

    Parameters
    -----
    df: data to be imputed.
    period_num: reshape data by period_num.

    Return
    -----
    data: data imputed.
    '''
    from sklearn.impute import KNNImputer
    data = copy.deepcopy(df)

    matrix_shape = (np.size(data.values)//period_num, period_num)
    data_matrix = np.resize(data.values, matrix_shape)

    imp = KNNImputer(n_neighbors=5, weights="uniform")
    data_impute_matrix = imp.fit_transform(data_matrix)
    data_impute = pd.DataFrame(data=data_impute_matrix.reshape(-1, data.shape[1]), index=data.index, columns=data.columns, dtype='float')

    if plot:
        data.plot(subplots=True, title='data (original)')
        data_impute.plot(subplots=True, title='data (imputation_KNN)')
        plt.show()

    return data_impute


def impute_SVD(df:pd.DataFrame, period_num=4*24*7*2, plot=False, **kw) -> pd.DataFrame:
    '''
    Impute data by Singular Value Decomposition (multivariable).

    Parameters
    -----
    df: data to be imputed.
    period_num: reshape data by period_num.

    Return
    -----
    data: data imputed.
    '''
    from fancyimpute import SoftImpute
    data = copy.deepcopy(df)

    matrix_shape = (np.size(data.values)//period_num, period_num)
    data_matrix = np.resize(data.values, matrix_shape)

    softImpute = SoftImpute()
    data_impute_matrix = softImpute.fit_transform(data_matrix)
    data_impute = pd.DataFrame(data=data_impute_matrix.reshape(-1, data.shape[1]), index=data.index, columns=data.columns, dtype='float')

    if plot:
        data.plot(subplots=True, title='data (original)')
        data_impute.plot(subplots=True, title='data (imputation_SVD)')
        plt.show()
    
    return data_impute


def impute_MF(df:pd.DataFrame, period_num=4*24*7*2, plot=False, **kw) -> pd.DataFrame:
    '''
    Impute data by Matrix Factorization (multivariable).

    Parameters
    -----
    df: data to be imputed.
    period_num: reshape data by period_num.

    Return
    -----
    data: data imputed.
    '''
    from fancyimpute import MatrixFactorization
    data = copy.deepcopy(df)

    matrix_shape = (np.size(data.values)//period_num, period_num)
    data_matrix = np.resize(data.values, matrix_shape)

    MatrixFactorization = MatrixFactorization()
    data_impute_matrix = MatrixFactorization.fit_transform(data_matrix)
    data_impute = pd.DataFrame(data=data_impute_matrix.reshape(-1, data.shape[1]), index=data.index, columns=data.columns, dtype='float')

    if plot:
        data.plot(subplots=True, title='data (original)')
        data_impute.plot(subplots=True, title='data (imputation_MF)')
        plt.show()
    
    return data_impute


def impute_MICE(df:pd.DataFrame, period_num=4*24*7*2, plot=False, **kw) -> pd.DataFrame:
    '''
    Impute data by MICE (multivariable).

    Parameters
    -----
    df: data to be imputed.
    period_num: reshape data by period_num.

    Return
    -----
    data: data imputed.
    '''
    from fancyimpute import IterativeImputer
    data = copy.deepcopy(df)

    matrix_shape = (np.size(data.values)//period_num, period_num)
    data_matrix = np.resize(data.values, matrix_shape)

    IterativeImputer = IterativeImputer()
    data_impute_matrix = IterativeImputer.fit_transform(data_matrix)
    data_impute = pd.DataFrame(data=data_impute_matrix.reshape(-1, data.shape[1]), index=data.index, columns=data.columns, dtype='float')

    if plot:
        data.plot(subplots=True, title='data (original)')
        data_impute.plot(subplots=True, title='data (imputation_MF)')
        plt.show()

    return data_impute


def impute_prophet(df: pd.DataFrame, plot=False):
    '''
    prophet: Interpolation by prediction.
    '''

    import prophet

    data = copy.deepcopy(df)

    for col in data.columns:
        # if col in ['Qac', 'Qin']:
        #     continue
        single_data = data[col].to_frame()
        single_data = single_data.rename(columns = {col : 'y'})
        single_data['ds'] = single_data.index
        single_data['ds'] = single_data['ds'].dt.tz_localize(None) # drop timezone

        model = prophet.Prophet(interval_width=0.8, daily_seasonality=True, weekly_seasonality=True)
        model.fit(single_data)
        forecast = model.predict(single_data)
        model.plot(forecast)
        plt.show()

        # merge data and prediction on the shared timestamp column
        merged = pd.merge(single_data, forecast[['ds','yhat', 'yhat_lower','yhat_upper']], on="ds") 
        # if there's a NaN in the og data, insert that prophet forecast baybeee
        merged['imputed'] = merged.apply(lambda row: row['yhat'] if np.isnan(row['y']) else row['y'], axis=1)
        data.loc[:, col] = merged['imputed'].to_list()
    
    if plot:
        df.plot(subplots=True, title='data (original)')
        data.plot(subplots=True, title='data (imputation_prophet)')
        plt.show()
    
    return data



#%% other functions
def od_plot(df:pd.DataFrame, df_rmol:pd.DataFrame, outlier_indexes:list, label='', **kw):
    '''
    Plot outliers.
    '''
    data = df
    data_rmol = df_rmol

    subplot_num = len(data_rmol.columns)
    for col, i in zip(data_rmol.columns, range(subplot_num)):
        outlier = data[col].iloc[outlier_indexes[i]]
        print(f'{col}:', len(outlier), 'outliers')
        plt.subplot(subplot_num, 1, i+1)
        plt.plot(data_rmol[col].index, data_rmol[col])
        plt.scatter(outlier.index, outlier, color='red')
        plt.legend([col, col+'_outliers'+f'_{label}'], loc='upper left')
    plt.gcf().set_size_inches(12, 8)
    plt.show()

    return


def impute_plot(df:pd.DataFrame, df_impute:pd.DataFrame, label='', **kw):
    '''
    Plot imputation.
    '''
    data = df
    data_impute = df_impute

    subplot_num = len(df_impute.columns)
    for col, i in zip(data_impute.columns, range(subplot_num)):
        plt.subplot(subplot_num, 1, i+1)
        plt.plot(data_impute[col].index, data_impute[col])
        plt.plot(data[col].index, data[col])
        plt.legend([col+'_impute', col+f'_{label}'], loc = 'upper left')
    plt.gcf().set_size_inches(12, 6)
    plt.show()

    return


def get_data(data_point:dict, start_time, end_time, rsp_time='15 min'):
    
    start_time = pd.to_datetime(start_time)
    end_time = pd.to_datetime(end_time)

    df_list = []
    for key1, value1 in data_point.items():
            # print(key1)
            db_name = value1['db_name']
            params = {
                'measurement_name': value1['measurement_name'],
                'start_time': start_time,
                'end_time': end_time,
                'field_list': value1['field_list'],
                'tag_dict': value1['tag_dict'],
                'fore': False,
                'fore_horizon': None,
                'interval': None
            }
            db_client = ClientInfluxdb(db_name=db_name) 
            df = db_client.read_influxdb(**params)
            # str -> np.float64
            for col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='ignore')
                df.rename(columns={col: key1}, inplace=True)
            # resampling data, rsp_time=15min
            df = df.resample(rsp_time).mean()
            df_list.append(df)


    time_range = pd.date_range(start=start_time, end=end_time, freq=rsp_time)
    data = pd.DataFrame(data=pd.concat(df_list, axis=1), index=time_range)

    return data


def data_point(vrf_id='vrf_0000CC311178CCM262323410008787JG', power_vrf_id='mDev_EMeter_Roof_MDV_7', num_indoor=[0,1,2]):

    # vrf_id = 'vrf_0000CC311178CCM26232341000271K0V'
    # power_vrf_id = 'mDev_EMeter_Roof_MDV_10'
    # num_indoor = [0,1,2,3,4,5,6]

    # vrf_id = 'vrf_0000CC311178CCM262323410008787JG'
    # power_vrf_id = 'mDev_EMeter_Roof_MDV_7'
    # num_indoor = [0,1,2]

    rsp_time = '15 min'
    start_time = '2022-04-01 00:00:00'
    end_time = '2022-12-31 23:45:00'

    data_point = {

        'Ta': {
            'db_name': 'moserveribms',
            'measurement_name': 'bridgemodata',
            'start_time': start_time,
            'end_time': end_time,
            'field_list': ['e3'],
            'tag_dict': {'nid': 'ibms/ibms_1564376390869024768/microWeatherStation/20201800'},
        },

        'Qs': {
            'db_name': 'moserveribms',
            'measurement_name': 'bridgemodata',
            'start_time': start_time,
            'end_time': end_time,
            'field_list': ['e11'],
            'tag_dict': {'nid': 'ibms/ibms_1564376390869024768/microWeatherStation/20201800'},
        },

        'Qin': {
            'db_name': 'moserveribms',
            'measurement_name': 'ibmsV2modata',
            'start_time': start_time,
            'end_time': end_time,
            'field_list': ['E'],
            'tag_dict': {'nid': 'ibmsv2/ibmsv2_5929149262402256896/EMeter/mDev_EMeter_F2_Backup'},
        },

        'Pvrf': {
            'db_name': 'moserveribms',
            'measurement_name': 'ibmsV2modata',
            'start_time': start_time,
            'end_time': end_time,
            'field_list': ['E'],
            'tag_dict': {'nid': f'ibmsv2/ibmsv2_5929149262402256896/EMeter/{power_vrf_id}'},
        },

        'Pvrf_sys': {
            'db_name': 'moserver',
            'measurement_name': 'modata',
            'start_time': start_time,
            'end_time': end_time,
            'field_list': ['systemCalculateMeter'],
            'tag_dict': {'nid': f'vrf/{vrf_id}'},
        },

        # 'C1f': {
        #     'db_name': 'moserver',
        #     'measurement_name': 'modata',
        #     'start_time': start_time,
        #     'end_time': end_time,
        #     'field_list': ['compressor1Frequency'],
        #     'tag_dict': {'nid': f'vrf/{vrf_id}/outdoor/129'},
        # },

        'Qac': {
            'db_name': 'moserver',
            'measurement_name': 'VRF_cooling_capacity',
            'start_time': start_time,
            'end_time': end_time,
            'field_list': ['Q_cool'],
            'tag_dict': {'nid': f'vrf/{vrf_id}'},
        },

        'Qac_sys': {
            'db_name': 'moserver',
            'measurement_name': 'modata',
            'start_time': start_time,
            'end_time': end_time,
            'field_list': ['systemQc'],
            'tag_dict': {'nid': f'vrf/{vrf_id}'},
        },

    }

    for indoor_num in num_indoor:
        
        data_point[f'Ti{indoor_num}'] = {
            'db_name': 'moserver',
            'measurement_name': 'modata',
            'start_time': start_time,
            'end_time': end_time,
            'field_list': ['roomTemp'],
            'tag_dict': {'nid': f'vrf/{vrf_id}/indoor/{indoor_num}'},
        }

        data_point[f'Qac{indoor_num}'] = {
            'db_name': 'moserver',
            'measurement_name': 'VRF_cooling_capacity',
            'start_time': start_time,
            'end_time': end_time,
            'field_list': ['Q_cool'],
            'tag_dict': {'nid': f'vrf/{vrf_id}/indoor/{indoor_num}'},
        }

        data_point[f'Sc{indoor_num}'] = {
            'db_name': 'moserver',
            'measurement_name': 'modata',
            'start_time': start_time,
            'end_time': end_time,
            'field_list': ['exv1Opening'],
            'tag_dict': {'nid': f'vrf/{vrf_id}/indoor/{indoor_num}'},
        }

        # 没有这个数据
        # data_point[f'Qac_sys{indoor_num}'] = {
        #     'db_name': 'moserver',
        #     'measurement_name': 'modata',
        #     'start_time': start_time,
        #     'end_time': end_time,
        #     'field_list': ['systemQc'],
        #     'tag_dict': {'nid': f'vrf/{vrf_id}/indoor/{indoor_num}'},
        # }

    # with open(r'C:\Users\Wang\Desktop\dqa\87JG\data_point_all.json', 'w') as f:
    #     json.dump(data_point, f)

    return data_point




# def rc_rmse(data, good_time):

#     rmse_valid = []

#     input_X = data[['Ta', 'Qac', 'Qin', 'Qs']]
#     input_y = data['Ti']
#     len_data = len(data)
#     len_train = 4 * 24 * 3
#     len_valid = 4 * 12

#     for i in range(0, len_data - (len_train + len_valid - 1)):
#         if input_X.iloc[i:i+1].index not in good_time: continue

#         X_train = input_X.iloc[i: i + len_train]
#         y_train = input_y.iloc[i: i + len_train]
#         X_test = input_X.iloc[i + len_train: i + len_train + len_valid]
#         y_test = input_y.iloc[i + len_train: i + len_train + len_valid]

#         R_zC_z, C_z, alpha_sol, alpha_int = rc_model_1k0v2.model_optimization(X_train, y_train)
#         # Tz_training_fore, Tz_training_actual, error_index = rc_model_1k0v2.training_evaluation(R_zC_z, C_z, alpha_sol, alpha_int, X_train, y_train)
#         # rc_model_1k0v2.plot(X_train[0:-1], Tz_training_actual[0: -1], Tz_training_fore[0: -2], suptitle=f'1k0v Zone Training {len_train/24/4} day')
#         Tz_testing_fore, Tz_testing_actual, error_index = rc_model_1k0v2.testing_evaluation(R_zC_z, C_z, alpha_sol, alpha_int, X_test, y_test)
#         # rc_model_1k0v2.plot(X_test[0:-1], Tz_testing_actual[0: -1],  Tz_testing_fore[0: -2], suptitle=f'1k0v Zone Testing {len_valid/24/4} day')
#         rmse_valid.append(error_index['rmse'][0])

#     # print('len_train_data:', len(rmse_valid))

#     if len(rmse_valid) > 1:
#         Q1 = np.quantile(rmse_valid, q=0.25)
#         Q3 = np.quantile(rmse_valid, q=0.75)
#         IQR = Q3 - Q1
#         max = Q3 + 1.5*IQR
#         temp = [x for x in rmse_valid if x < max]
#         # print('avg_rmse:', round(np.mean(temp), 3))
#         return round(np.mean(temp), 3)
    
#     else: 
#         # print('avg_rmse:', round(np.mean(rmse_valid), 3))
#         # print(len(rmse_valid))
#         return round(np.mean(rmse_valid), 3)