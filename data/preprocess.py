"""
Script for data pre_processing

Major parts:
- data_preprocess class
- identify the valid data for model training
- outlier detection function
- data imputation function

If needed, can be splitted into multiple files

Created on Tue Sep 6 15:14:50 2022
Last updated on 
@author: Zhenyu Wang
"""

import pandas as pd

#%% data_preprocessing class
class DataPreprocess(object):

    def __init__(self, data, column_type):
        '''
        data: dataframe,
            Data to be preprocessed
        column_type: dictionary
            The outlier detection and data algoirthms vary for different type of data
            Key is the column name
            Value is the data type, currently we support the following types {'T_amb', 'T_sys', 'Sys', 'Meter', 'Other'}, standing for
                - T_amb: ambient temperature, including the room and outdoor temperature
                - T_sys: system related temperature, including the evaporative temperature, condensing temperature, ...
                - Sys: system operational data, including 
                - Meter: electrical and power meter data
                - Other: other data types
        '''
        assert len(column_type) == len(data.columns), f"Specify the column type for each column, valid types are: 'T_amb', 'T_sys', 'Sys', 'Meter', 'Other'"
        
        self.data = data
        self.column_type = column_type
    
    def outlier_detect(self) -> pd.DataFrame:
        for column in self.data.columns:
            if self.column_type[column] == 'T_amb':
                pass
                
    def impute(self) -> pd.DataFrame:
        for column in self.data.columns:
            if self.column_type[column] == 'T_amb':
                pass

    def evaluate(self) -> float:
        pass

    def process(self) -> (pd.DataFrame, float):
        self.outlier_detect()
        self.impute()
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


#%% outlier detection functions



#%% data imputation functions