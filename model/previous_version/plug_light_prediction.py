# -*- coding: utf-8 -*-
"""
Created on Mon Aug  1 00:37:18 2022

@author: Mingyue Guo
"""
#%% import
import chinese_calendar as cc
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import utility
import lightgbm as lgb

#%% functions
def cal_average(train_workdays, train_holidays):
    workday = pd.pivot_table(train_workdays, values = 'E_diff', index = 'Date', columns = "Time")
    # workday.T.plot(alpha = 0.3, legend = False)
    # plt.ylabel('E_diff kWh')
    # plt.title('workday')
    # plt.show()
    
    holiday = pd.pivot_table(train_holidays, values = 'E_diff', index = 'Date', columns = "Time")
    # holiday.T.plot(alpha = 0.3, legend = False)
    # plt.ylabel('E_diff kWh')
    # plt.title('holiday')
    # plt.show()
    
    for co in workday.columns:
        workday[co] = utility.outlier(workday, co)
        holiday[co] = utility.outlier(holiday, co)

    workday_average = workday.mean(axis = 0)
    holiday_average = holiday.mean(axis = 0)

    # workday_average.plot(label = 'workday')
    # holiday_average.plot(label = 'holiday')
    # plt.ylabel('E_diff kWh')
    # plt.title('average MELs')
    # plt.show()
    return workday_average, holiday_average

def target_enc(train, target_col = 'E_diff'):
    df = train.copy()
    df_median = df.groupby(['Hour','IsHoliday'])[target_col].median()
    df_mean = df.groupby(['Hour','IsHoliday'])[target_col].mean()
    df_std = df.groupby(['Hour','IsHoliday'])[target_col].std()
    df_min = df.groupby(['Hour','IsHoliday'])[target_col].min()
    df_max = df.groupby(['Hour','IsHoliday'])[target_col].max()
    df_skew = df.groupby(['Hour','IsHoliday'])[target_col].skew()
    df_per95 = df.groupby(['Hour','IsHoliday'])[target_col].apply(lambda arr: np.nanpercentile(arr, 95))
    df_per5 = df.groupby(['Hour','IsHoliday'])[target_col].apply(lambda arr: np.nanpercentile(arr, 5))
    df1 = pd.DataFrame()
    df1['Hour_median'] = df_median
    df1['Hour_mean'] = df_mean
    df1['Hour_std'] = df_std
    df1['Hour_min'] = df_min
    df1['Hour_max'] = df_max
    df1['Hour_skew'] = df_skew
    df1['Hour_per95'] = df_per95
    df1['Hour_per5'] = df_per5
    df1['Hour'] = list(zip(*df1.index))[0]
    df1['IsHoliday'] = list(zip(*df1.index))[1]
    df1.reset_index(drop=True, inplace = True)
    df_out = pd.merge(df, df1,on = ['Hour','IsHoliday'], how = 'left')
    df_out.reset_index(drop=True, inplace = True)
    return df_out



def MELs_preprocess(submeters):
    MELs_meter = submeters['mDev_EMeter_F2_Backup'].copy()
    MELs_meter['Date'] = MELs_meter.index.date
    MELs_meter['Hour'] = MELs_meter.index.hour
    MELs_meter['Minute'] = MELs_meter.index.minute
    MELs_meter['Time'] = MELs_meter.index.time
    MELs_meter['Month'] = MELs_meter.index.month
    MELs_meter['Weekday'] = MELs_meter.index.weekday
    MELs_meter['Week'] = MELs_meter.index.week
    MELs_meter['IsHoliday'] = 0
    MELs_meter['IsHoliday'] = MELs_meter.index.map(lambda x: 1 if cc.is_holiday(x) else 0)
    MELs_meter.loc[MELs_meter['IsHoliday'] == 0, 'IsHoliday'] = MELs_meter[MELs_meter['IsHoliday'] == 0].index.map(lambda x: 0.5 if cc.is_in_lieu(x) else 0)
    
    
    
    
    workdays = MELs_meter[(MELs_meter['IsHoliday'] ==0)]
    # valid_workdays = workdays[workdays.Date == workdays.Date.max()]
    # train_workdays = workdays[~(workdays.Date == workdays.Date.max())]

    valid_workdays = workdays[workdays.Date == workdays.Date.unique()[-2]]
    train_workdays = workdays[~(workdays.Date == workdays.Date.unique()[-2])]

    holidays = MELs_meter[(MELs_meter['IsHoliday'] == 1)]
    valid_holidays = holidays[holidays.Date == holidays.Date.max()]
    train_holidays = holidays[~(holidays.Date == holidays.Date.max())]
    return valid_workdays, train_workdays, valid_holidays, train_holidays


def average_predict(valid_workdays, train_workdays, valid_holidays, train_holidays):
    train_w = train_workdays.copy()
    train_h = train_holidays.copy()
    valid_w = valid_workdays.copy()
    valid_h = valid_holidays.copy()

    workday_average, holiday_average = cal_average(train_w, train_h)
    # visualize
    plt.plot(holiday_average.values, label = 'predict')
    plt.plot(valid_h['E_diff'].values, label = 'measured')
    plt.ylabel('E_diff kWh')
    plt.xlabel('Hour')
    plt.xticks(range(0, workday_average.shape[0], 4),valid_h.resample('1H').mean().index.hour)
    plt.title('Holiday prediction cv_rmse: {}'.format(utility.cv_rmse(valid_h['E_diff'].values,holiday_average.values).round(3)))
    plt.legend()
    plt.show()
    
    plt.plot(workday_average.values, label = 'predict')
    plt.plot(valid_w['E_diff'].values, label = 'measured')
    plt.ylabel('E_diff kWh')
    plt.xlabel('Hour')
    plt.xticks(range(0, workday_average.shape[0], 4),valid_h.resample('1H').mean().index.hour)
    # plt.xticks(range(0, workday_average.shape[0], 4),valid_w.resample('1H').mean().index.hour)
    plt.title('Workday prediction cv_rmse: {}'.format(utility.cv_rmse(valid_w['E_diff'].values
                                                                      ,workday_average.values[:valid_w.shape[0]]
                                                                      ).round(3)))
    plt.legend()
    plt.show()
    valid_w['predict'] = workday_average.values[:valid_w.shape[0]]
    valid_h['predict'] = holiday_average.values[:valid_h.shape[0]]
    return valid_w, valid_h

def MELs_visualize(valid_df, day_type = 'Holiday'):
    # visualize

    plt.plot(valid_df['predict'].values, label = 'predict')
    plt.plot(valid_df['E_diff'].values, label = 'measured')
    plt.ylabel('E_diff kWh')
    plt.xlabel('Time index')
    # plt.xticks(range(0, valid_df.shape[0], 4),valid_df.resample('1H').mean().index.hour)
    plt.title('{} prediction cv_rmse: {}'.format(day_type, 
                                                  utility.cv_rmse(valid_df['E_diff'].values
                                                                  ,valid_df['predict'].values).round(3)))
    plt.legend()
    plt.show()
    return utility.cv_rmse(valid_df['E_diff'].values,valid_df['predict'].values).round(3)



def lgb_predict(valid_workdays, train_workdays, valid_holidays, train_holidays):
    train_w = train_workdays.copy()
    train_h = train_holidays.copy()
    valid_w = valid_workdays.copy()
    valid_h = valid_holidays.copy()

    target = ['E_diff']
    encoder_cols = ['Hour_median'
                     ,'Hour_mean', 'Hour_std', 'Hour_min', 'Hour_max'
                     ,'Hour_skew', 'Hour_per95', 'Hour_per5']
    x_cos = ['Hour', 'Minute', 'Month', 'Weekday', 'Week', 'Hour_median'
             ,'Hour_mean', 'Hour_std', 'Hour_min', 'Hour_max'
             ,'Hour_skew', 'Hour_per95', 'Hour_per5']

    train_h = target_enc(train_holidays, target_col = 'E_diff')
    valid_h = valid_h.merge(train_h.groupby(['Hour'])[encoder_cols].mean(),on = ['Hour'],how = 'left')
    # holiday model
    x_axis = np.arange(0.001,0.011,0.001)
    errors = []
    for i in x_axis:
        params = {
                "objective": "regression",
                "boosting": "gbdt",
                "learning_rate":0.02, #0.02,
                "n_estimators": 100, #400,
                "max_depth":2,
                "num_leaves": 4,
                "min_data_in_leaf":2, #20,
                "max_bin":30,
                "feature_fraction": 0.4,
                "bagging_fraction": 0.2, #0.1,
                "bagging_freq":40,
                "reg_alpha":0.001, #0.5,
                "reg_lambda":0.00001, #0.2,
                "metric": "rmse",
                "verbosity":0
                }
        nround = 1000
        categorical_features = ['Hour'
                                , 'Minute'
                                , 'Month'
                                , 'Weekday'
                                , 'Week']
        d_train = lgb.Dataset(train_h[x_cos], label = train_h[target], categorical_feature = categorical_features, free_raw_data=False)
        d_valid = lgb.Dataset(valid_h[x_cos], label = valid_h[target], categorical_feature = categorical_features, free_raw_data=False)
    
        model = lgb.train(params, train_set = d_train, num_boost_round = nround, valid_sets = [d_valid], early_stopping_rounds = 100)
        valid_h['predict'] = model.predict(valid_h[x_cos])[:valid_h.shape[0]]
        # train_h['predict'] = model.predict(train_h[x_cos])[:train_h.shape[0]]
        # errors.append(MELs_visualize(train_h, day_type = 'Holiday'))
        errors.append(MELs_visualize(valid_h, day_type = 'Holiday'))
    plt.plot(x_axis, errors)
    print('best parameter: {}'.format(x_axis[errors.index(min(errors))]))

    train_w = target_enc(train_workdays, target_col = 'E_diff')
    valid_w = valid_w.merge(train_w.groupby(['Hour'])[encoder_cols].mean(),on = ['Hour'],how = 'left')
    # workday model
    x_axis = np.arange(0.1,1.1,0.1)
    errors = []
    for i in x_axis:
        params = {
                "objective": "regression",
                "boosting": "gbdt",
                "learning_rate":0.4, 
                "n_estimators": 100, #400,
                "max_depth":2,
                "num_leaves": 4,
                "min_data_in_leaf":9, #20,
                "max_bin":26,
                "feature_fraction": 0.3,
                "bagging_fraction": 0.3,
                "bagging_freq":60,
                "reg_alpha":0.0001, #0.7, 
                "reg_lambda": 0.5,
                "metric": "rmse",
                "verbosity":0
                }
        nround = 1000
        categorical_features = ['Hour'
                                , 'Minute'
                                , 'Month'
                                , 'Weekday'
                                , 'Week']
        d_train = lgb.Dataset(train_w[x_cos], label = train_w[target], categorical_feature = categorical_features, free_raw_data=False)
        d_valid = lgb.Dataset(valid_w[x_cos], label = valid_w[target], categorical_feature = categorical_features, free_raw_data=False)
    
        model = lgb.train(params, train_set = d_train, num_boost_round = nround, valid_sets = [d_valid], early_stopping_rounds = 100)
        valid_w['predict'] = model.predict(valid_w[x_cos])[:valid_w.shape[0]]
        errors.append(MELs_visualize(valid_w, day_type = 'Workday'))
    plt.plot(x_axis, errors)
    print('best parameter: {}'.format(x_axis[errors.index(min(errors))]))
    return valid_w, valid_h

