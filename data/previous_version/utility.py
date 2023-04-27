# -*- coding: utf-8 -*-
"""
Created on Mon Aug  1 11:23:06 2022

@author: Mingyue Guo
"""

#%% import
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.metrics import explained_variance_score, mean_absolute_error as MAE, mean_squared_error as MSE, r2_score
import math
from pytz import timezone

#%% functions
def outlier(df, co):
    #删除小于0的值
    df_new = df.copy()
    df_new.loc[df_new[co] < 0, co]  = np.nan
    # #利用箱线图找到离群值,会把不是异常值的判定为异常值
    Dcos = df_new[co].quantile(0.95) - df_new[co].quantile(0.05)
    L = df_new[co].quantile(0.05) - 1.5 * Dcos
    U = df_new[co].quantile(0.95) + 1.5 * Dcos

    # #处理小于下边缘的离群值
    # # df_new = df_new[(df_new>L)]
    df_new.loc[(df_new[co] < L), co] = np.nan
    # #处理大于上边缘的离群值
    # # df_new = df_new[(df_new<U)]
    df_new.loc[(df_new[co] > U), co] = np.nan
    return df_new[co]

def outlier_meter(df, co):
    #删除小于0的值
    df_new = df.copy()
    df_new.loc[df_new[co] < 0, co]  = np.nan
    df_new.loc[(df_new[co] > 50), co] = np.nan
    return df_new[co]


def outlier_power(df, co):
    #删除小于初值的值,大于末值
    df_new = df.copy()
    df_new.loc[df_new[co] <= df_new[co][0], co]  = np.nan
    df_new.loc[df_new[co] > df_new[co][-1], co]  = np.nan
    # #利用箱线图找到离群值,会把不是异常值的判定为异常值
    Dcos = df_new[co].quantile(0.75) - df_new[co].quantile(0.25)
    L = df_new[co].quantile(0.25) - 1.5 * Dcos
    U = df_new[co].quantile(0.75) + 1.5 * Dcos

    # #处理小于下边缘的离群值
    # # df_new = df_new[(df_new>L)]
    df_new.loc[(df_new[co] < L), co] = np.nan
    # #处理大于上边缘的离群值
    # # df_new = df_new[(df_new<U)]
    df_new.loc[(df_new[co] > U), co] = np.nan
    return df_new[co]


def cv_rmse(ground_truth, prediction):
    df = pd.DataFrame()
    df['y'] = ground_truth
    df['y_hat'] = prediction
    df = df.dropna(how = 'any', axis = 0)
    return math.sqrt(MSE(df['y'], df['y_hat'])) / np.mean(df['y'])

def change_timezone(date_time):
    tz = timezone('Asia/Shanghai')
    utc = timezone('UTC')
    return date_time.replace(tzinfo=utc).astimezone(tz)
