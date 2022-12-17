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
@author: Zhenyu Wang
"""

import matplotlib.pyplot as plt
from matplotlib.pylab import mpl
import numpy as np
import pandas as pd
import copy

#%% data_preprocessing class
class DataPreprocess(object):

    # common parameters
    sampling_time = pd.Timedelta('15 min')
    sampling_rate = 4   # 4 times per hour, depends on sampling time
    # parameters of calculate missing rate
    step = 4*24*3   # step = sampling_rate/h*24h/day*3day means to calculate the missing rate three days backward at each moment
    ms_thresh = 0.2   # the condition of missing rate (< ms_thresh) for multiple data
    # parameters of outlier detect
    win_size = None   # time window size of remove outliers, 'None' means 'win_size == time period for all data'
    # parameters of data imputation
    linear_time_delta = pd.Timedelta('6 hours')   # data missing for more than consecutive linear_time_delta will not be linear imputation
    
    def __init__(self, data:pd.DataFrame, column_type:dict, **kw):
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
        '''
        assert len(column_type) == len(data.columns), f"Specify the column type for each column, valid types are: 'T_amb', 'T_sys', 'Sys', 'Meter', 'Other'."
        
        self.column_type = column_type
        self.data = data
        self.data_rmol = None
        self.data_impute = None

        if 'sampling_time' in kw: self.sampling_time = kw['sampling_time']
        if 'sampling_rate' in kw: self.sampling_rate = kw['sampling_rate'] 
        if 'step' in kw: self.step = kw['step']
        if 'ms_thresh' in kw: self.ms_thresh = kw['ms_thresh']
        if 'win_size' in kw: self.win_size = kw['win_size'] 
        if 'linear_time_delta' in kw: self.linear_time_delta = kw['linear_time_delta']

    def missing_rate(self, label='original', plot=True, **kw) -> (pd.DataFrame, dict):
        '''
        label = ['original', 'remove_outlier', 'imputation']
        '''
        if label == 'original':
            data = self.data
        elif label == 'remove_outlier':
            data = self.data_rmol
            assert data is not None, "The data should be removed outliers first by self.outlier_detect()."
        elif label == 'imputation':
            data = self.data_impute
            assert data is not None, "The data should be removed outliers and imputed first by self.outlier_detect() and self.impute()"
        else: assert False, "Please enter the correct label: 'original', 'remove_outlier', 'imputation'."
        
        if 'step' in kw: step = kw['step']
        else: step = self.step
        if 'ms_thresh' in kw: ms_thresh = kw['ms_thresh']
        else: ms_thresh = self.ms_thresh

        missing_rate = pd.DataFrame(data=None, index=data.index, columns=data.columns)
        for col in data.columns:
            missing_rate[col] = 1 - (data[col].rolling(step, min_periods=0).count() / float(step))
        describe = missing_rate.describe()
        
        ms_results = {}
        for col in data.columns:
            print(f'{col} {label}, minimal missing rate: ', describe.loc['min', col])
            print(f'{col} {label}, average missing rate: ', describe.loc['mean', col])
            # 获取具有最小missing_rate时刻的所有索引
            idxmin = np.where(missing_rate[col] == missing_rate[col].min())
            # 获得最近的具有最小missing_rate的时刻
            best = missing_rate[col].iloc[idxmin[0]].tail(1)
            best_time = best.index.strftime('%Y-%m-%d %H:%M:00')
            print(f'{col} {label}, the closest optimal moment to the present: ', best_time[0], '\n------------------')
            ms_results[col] = best_time[0]

        # 当dataframe有多组数据时
        if len(data.columns) > 1:
            # 获取每一行数据的missing_rate都小于ms_thresh的所有索引
            idx_thresh = missing_rate[missing_rate <= ms_thresh]
            idx_thresh = idx_thresh.dropna()
            # 所有数据满足距离当前时间段最近的3天缺失率低于ms_thresh的时刻
            closest_time = idx_thresh.tail(1).index.strftime('%Y-%m-%d %H:%M:00')
            if not any(closest_time):
                print(f'{label}, there is no moment meets the condition (missing rate < {ms_thresh}) for multiple data.', '\n------------------\n\n')
            else:
                print(f'{label}, the closest moment meets the condition (missing rate < {ms_thresh}) for multiple data: ', closest_time[0], '\n------------------\n\n')
                ms_results['closest_time_multi'] = closest_time[0]

        if plot:
            data.plot(title=f'Measurement data ({label})', figsize=(12,6))
            plt.legend(loc = 'upper left')
            missing_rate.plot(title=f'Missing Rate ({step} steps backward) ({label})', figsize=(12,6))
            plt.legend(loc = 'upper left')
            plt.show()

        return missing_rate, ms_results

    def outlier_detect(self, method='boxplot', remove_outlier=True, **kw) -> None:
        '''
        method = ['boxplot', '3-sigma', 'kernal_density', 'isolation_forest']
        '''
        self.data_rmol = copy.deepcopy(self.data)
        assert self.data_rmol is not None, "Plese verify the original data is not empty."
        self.data_rmol = od_negative(self.data_rmol, self.column_type)

        if method == 'boxplot':
            win_size = self.win_size
            self.data_rmol, _ = od_boxplot(self.data_rmol, win_size, remove_outlier)

        elif method == '3-sigma':
            win_size = self.win_size
            self.data_rmol, _ = od_sigma(self.data_rmol, win_size, remove_outlier)

        elif method == 'kernal_density':
            self.data_rmol, _ = od_KD(self.data_rmol, remove_outlier)

        elif method == 'isolation_forest':
            self.data_rmol, _ = od_IF(self.data_rmol, remove_outlier)

        else: assert False, "Please enter the correct method: 'boxplot', '3-sigma', 'kernal_density', 'isolation_forest'."

    def impute(self, method='linear', **kw) -> None:
        '''
        method = ['linear', 'KNN', 'MICE']
        '''
        if self.data_rmol: self.data_impute = copy.deepcopy(self.data_rmol)
        else: self.data_impute = copy.deepcopy(self.data)
        assert self.data_impute is not None, "Plese verify the original data is not empty."

        if method == 'linear':
            sampling_time = self.sampling_time
            linear_time_delta = self.linear_time_delta
            for col in self.data_impute.columns:
                if self.column_type[col] == 'Sys': continue   # Discrete value like 0-1 would not be imputed
                self.data_impute[col] = \
                    impute_linear(df=self.data_impute[col].to_frame(), sampling_time=sampling_time, linear_time_delta=linear_time_delta)

        elif method == 'KNN':
            pass
        elif method == 'MICE':
            pass
        else: assert False, "Please enter the correct method: 'linear', 'KNN', 'MICE'."

    def process(self, oldt_method='boxplot', impute_method='linear') -> (pd.DataFrame, pd.DataFrame, dict):
        self.outlier_detect(method=oldt_method, remove_outlier=True)
        self.impute(method=impute_method)
        ms, ms_results = self.missing_rate(label='imputation')
        return self.data_impute, ms, ms_results

    def evaluate(self) -> float:
        pass


#%% identify the valid data set for training
def valid_data(data, interval_min_day=2, interval_max_day=10) -> pd.DataFrame:
    '''
    data: dataframe,
        Data to be searched
    interval_min_day: float,
        Minimum number of days needed for training
    interval_max_day: float,
        Maximum number of days needed for training        
    '''
    pass


#%% outlier detection functions
def od_negative(df:pd.DataFrame, column_type:dict, **kw) -> pd.DataFrame:
    '''
    remove negative.
    '''
    data = copy.deepcopy(df)
    for col in data.columns:
        if column_type[col] == 'Meter': 
            data[col].loc[data[col] < 0]  = np.nan

    return data

def od_boxplot(df:pd.DataFrame, win_size:int, thresh=3, remove_outlier=True, plot=False, **kw) -> (pd.DataFrame, list):
    '''
    remove outliers by boxplot (univariable).
    return:
        pd.DataFrame: data removed outliers (remove_outlier=True) / original data (remove_outlier=False).
        list: outliers' indexes of original data.
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
        outlier_index = np.where((data[col]<min[col]) | (data[col]>max[col]))
        outlier_indexes.append(outlier_index)
        if remove_outlier:
            data[col].iloc[outlier_index] = np.nan

    if plot and remove_outlier:
        df.plot(subplots=True, title=f'Measurement data (original)')
        data.plot(subplots=True, title=f'Measurement data (rmol_boxplot)')
        plt.show()

    return data, outlier_indexes

def od_sigma(df:pd.DataFrame, win_size: int, thresh=3, remove_outlier=True, plot=False, **kw) -> (pd.DataFrame, list):
    '''
    remove outliers by n-sigma (univariable), data should follow normal distribution.
    return:
        pd.DataFrame: data removed outliers (remove_outlier=True) / original data (remove_outlier=False).
        list: outliers' indexes of original data.
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
        outlier_index = np.where(abs(data[col] - mean[col]) > thresh*std[col])
        outlier_indexes.append(outlier_index)
        if remove_outlier:
            data[col].iloc[outlier_index] = np.nan
    
    if plot and remove_outlier:
        df.plot(subplots=True, title=f'Measurement data (original)')
        data.plot(subplots=True, title=f'Measurement data (rmol_sigma)')
        plt.show()

    return data, outlier_indexes

def od_KD(df:pd.DataFrame, remove_outlier=True, plot=False, **kw) -> (pd.DataFrame, list):
    '''
    remove outliers by Kernal Density (univariable).
    return:
        pd.DataFrame: data removed outliers (remove_outlier=True) / original data (remove_outlier=False).
        list: outliers' indexes of original data.
    '''
    from sklearn.neighbors import KernelDensity
    data = copy.deepcopy(df)

    outlier_indexes = []
    for col in data.columns:
        col_dropna = data[col].to_frame().dropna()
        kern_dens = KernelDensity()
        kern_dens.fit(col_dropna)
        scores = kern_dens.score_samples(col_dropna)
        threshold = np.quantile(scores, .02)
        outlier_dateindex = col_dropna.iloc[np.where(scores<=threshold)].index

        outlier_index = data[col].index.get_indexer(outlier_dateindex)
        outlier_indexes.append(outlier_index)
        if remove_outlier:
            data[col].iloc[outlier_index] = np.nan

    if plot and remove_outlier:
        df.plot(subplots=True, title=f'Measurement data (original)')
        data.plot(subplots=True, title=f'Measurement data (rmol_KD)')
        plt.show()

    return data, outlier_indexes

def od_IF(df:pd.DataFrame, remove_outlier=True, plot=False, **kw) -> (pd.DataFrame, list):
    '''
    remove outliers by Isolation Forest (univariable).
    return:
        pd.DataFrame: data removed outliers (remove_outlier=True) / original data (remove_outlier=False).
        list: outliers' indexes of original data.
    '''
    from sklearn.ensemble import IsolationForest
    data = copy.deepcopy(df)

    outlier_indexes = []
    for col in data.columns:
        col_dropna = data[col].to_frame().dropna()
        IF = IsolationForest(n_estimators=100, contamination=0.02)
        predictions = IF.fit_predict(col_dropna)
        outlier_dateindex = col_dropna.iloc[np.where(predictions==-1)].index

        outlier_index = data[col].index.get_indexer(outlier_dateindex)
        outlier_indexes.append(outlier_index)
        if remove_outlier:
            data[col].iloc[outlier_index] = np.nan

    if plot and remove_outlier:
        df.plot(subplots=True, title=f'Measurement data (original)')
        data.plot(subplots=True, title=f'Measurement data (rmol_IF)')
        plt.show()

    return data, outlier_indexes

def od_IF_multi(df:pd.DataFrame, remove_outlier=True, plot=False, **kw) -> (pd.DataFrame, list):
    '''
    remove outliers by Isolation Forest (multivariable).
    return:
        pd.DataFrame: data removed outliers (remove_outlier=True) / original data (remove_outlier=False).
        list: outliers' index of original data.
    '''
    from sklearn.ensemble import IsolationForest

    data = copy.deepcopy(df)
    data_dropna = data.dropna()

    IF = IsolationForest(n_estimators=100, contamination=.02)
    predictions = IF.fit_predict(data_dropna)
    outlier_dateindex = data_dropna.iloc[np.where(predictions==-1)].index
    outlier_index = data.index.get_indexer(outlier_dateindex)
    if remove_outlier:
        data.iloc[outlier_index] = np.nan

    if plot and remove_outlier:
        df.plot(subplots=True, title=f'Measurement data (original)')
        data.plot(subplots=True, title=f'Measurement data (rmol_IF_multi)')
        plt.show()

    return data, outlier_index 


#%% data imputation functions
def impute_linear(df:pd.DataFrame, sampling_time:pd.Timedelta, linear_time_delta:pd.Timedelta, plot=False, **kw) -> pd.DataFrame:
    '''
    impute data by linear interpolation (univariable).
    return:
        pd.DataFrame: data imputed.
    '''
    data = copy.deepcopy(df)

    for col in data.columns:
        series = data[col]
        # 获取空值索引
        series_nan = series[series.isna()]
        series_nan_index = series_nan.index
        if series_nan_index.empty: continue
        # 获取小于imputation_time_delta的空值索引
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
        # 对满足imputation_time_delta的空值进行线性插值
        for imputation in series_imputation_list:
            data[col].loc[imputation[0]-sampling_time: imputation[1]+sampling_time] = \
                series.loc[imputation[0]-sampling_time: imputation[1]+sampling_time].interpolate(method='polynomial', order=1)

    if plot:
        df.plot(subplots=True, title=f'Measurement data (original)')
        data.plot(subplots=True, title=f'Measurement data (imputation_linear)')
        plt.show()

    return data

def impute_KNN(df:pd.DataFrame, plot=False, **kw) -> pd.DataFrame:
    '''
    impute data by K-Nearest Neighbor (multivariable).
    return:
        pd.DataFrame: data imputed.
    '''
    from sklearn.impute import KNNImputer

    data = copy.deepcopy(df)

    imputer = KNNImputer(n_neighbors=5, weights="uniform")
    data = pd.DataFrame(data=imputer.fit_transform(data), index=df.index, columns=df.columns, dtype='float')

    if plot:
        df.plot(subplots=True, title=f'Measurement data (original)')
        data.plot(subplots=True, title=f'Measurement data (imputation_KNN)')
        plt.show()

    return data

def impute_MICE(df:pd.DataFrame, plot=False, **kw) -> pd.DataFrame:
    '''
    impute data by MICE (multivariable).
    return:
        pd.DataFrame: data imputed.
    '''
    data = copy.deepcopy(df)

    if plot:
        df.plot(subplots=True, title=f'Measurement data (original)')
        data.plot(subplots=True, title=f'Measurement data (imputation_MICE)')
        plt.show()

    return data

# for col in self.data_impute.columns:
        #     if self.column_type[col] == 'T_amb':
        #     elif self.column_type[col] == 'T_sys':
        #     elif self.column_type[col] == 'Sys':
        #     elif self.column_type[col] == 'Meter':
        #     elif self.column_type[col] == 'Other':
        #     else:
        #         assert False, "Specify the column type for each column, valid types are: 'T_amb', 'T_sys', 'Sys', 'Meter', 'Other'."