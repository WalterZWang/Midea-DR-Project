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
def change_timezone(date_time):
    '''
    This function convert UTC to +08:00

    Parameters
    ----------
    date_time : UTC datetime

    Returns
    -------
    converted datetime

    '''
    
    tz = timezone('Asia/Shanghai')
    utc = timezone('UTC')
    return date_time.replace(tzinfo=utc).astimezone(tz)
