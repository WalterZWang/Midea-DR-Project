import time
import os

import numpy as np
from influxdb import InfluxDBClient,DataFrameClient
import pandas as pd
from datetime import datetime

from utils.influxdb_util import utc2local,local2utc,get_field_list,fore_data_preprocessing,resultset_to_df,\
    fore_data_preprocessing_read



influxHost = 'vm.buildibp.top'
influxPort = 21622
influxUser = 'btri'
influxPassword = 'mBXRGzfeWee3iZzq'


class ClientInfluxdb(object):

    def __init__(self, db_name):

        self.db_name = db_name
        self.influxDBClient = InfluxDBClient(influxHost, influxPort, influxUser, influxPassword, self.db_name)
        self.dataframeclient=DataFrameClient(influxHost, influxPort, influxUser, influxPassword, self.db_name)
        # self.client = InfluxDBClient(influxHost, influxPort, influxUser, influxPassword, self.db_name)
        # selfmeasurement = measurement

        # self.ifluxdb_version = self.client_DataFrame.ping()  # influxDB version

    def read_influxdb(self, measurement_name:str, start_time:datetime, end_time:datetime, field_list:list,
                      tag_dict: dict=None,fore=False,fore_horizon: int=None)->pd.DataFrame:
        # fore_interval： minutes as unit
        assert isinstance(measurement_name, str), f"measurement expected a string data type, got {type(measurement_name)}"
        assert isinstance(field_list,list), \
            f"field_list expected list data type, got {type(field_list)}"
        assert tag_dict is None or isinstance(tag_dict,dict), \
            f"tag_list expected None value or list data type, got {type(dict)}"
        assert isinstance(fore, bool), f"fore expected a boolean data type, got {type(fore)} "
        assert fore_horizon is None or isinstance(fore_horizon, int), \
            f"tag_list expected None value or list data type, got {type(fore_horizon)}"

        field_list_raw=field_list

        if fore:
            assert start_time==end_time, f"start_time==end_time expected"
            new_field_list=[]
            for col in field_list:
                new_field_list=np.concatenate((new_field_list,[col+"_"+str(i) for i in range(1,fore_horizon+1)]))
            # print(new_field_list)

            field_list=new_field_list

        utc_start_time=local2utc(start_time).strftime('%Y-%m-%dT%H:%M:%SZ')
        utc_end_time=local2utc(end_time).strftime('%Y-%m-%dT%H:%M:%SZ')
        field_string = ''
        for field in field_list:
            field_string += '"{}", '.format(field)
        field_string=field_string[:-2]
        if tag_dict is None:
            query_str = 'SELECT %s FROM %s WHERE time >= \'%s\' AND time <= \'%s\'' % \
                        (field_string, measurement_name,utc_start_time, utc_end_time)
        else:
            tag_string = ''
            for k, v in tag_dict.items():
                tag_string += ' AND "{}"=\'{}\''.format(k, v)

            query_str ='SELECT %s FROM %s WHERE time >= \'%s\' AND time <= \'%s\'%s' % \
                        (field_string, measurement_name, utc_start_time, utc_end_time,tag_string)

        data = self.dataframeclient.query(query_str)
        if not data:
            if start_time==end_time:
                print('Data on {} does not exist!'.format(start_time))
            else:
                print('Data between {} and {} does not exist!'.format(start_time,end_time))
            return pd.DataFrame()
        result_df=data[measurement_name]
        result_df.index=result_df.index.map(lambda x: utc2local(x))

        if fore:
            max_fore_horizon=int(len(result_df.columns.to_list())/len(field_list_raw))
            assert fore_horizon<=max_fore_horizon,\
                f"fore_horizon expected not greater than {max_fore_horizon}, got {fore_horizon}>{max_fore_horizon}"
            result_df=fore_data_preprocessing_read(result_df,field_list_raw,fore_horizon)

        return  result_df

    def write_influxdb(self, measurement_name:str,data:pd.DataFrame,
                       tag_list: list=None, fore: bool=False)->None:
        data_df=data.copy(deep=True)
        assert isinstance(measurement_name, str),f"measurement expected a string data type, got {type(measurement_name)}"
        assert isinstance(data_df, pd.DataFrame), f"data_df expected a string data type, got {type(data_df)}"
        assert tag_list is None or isinstance(tag_list, list), \
            f"tag_list expected None value or list data type, got {type(tag_list)}"
        assert isinstance(fore,bool),f"fore expected a boolean data type, got {type(fore)} "
        # print(data_df.index)
        if fore:
            data_df=fore_data_preprocessing(data_df,tag_list)

        cols = data_df.columns.to_list()
        field_list = get_field_list(cols,tag_list)
        data_df.index = pd.to_datetime(data_df.index.values).map(lambda x: local2utc(x))
        # data_df = data_df.set_index(time_stamp)
        if tag_list:
            for t in tag_list:
                data_df[t]=data_df[t].astype(str)



        self.dataframeclient.write_points(data_df,measurement_name,tag_columns=tag_list,field_columns=field_list)

        self.dataframeclient.close()

    def get_table_info(self, need_field: bool=False, need_tag: bool=False, save_to_file: bool=False)->None:



        os.makedirs(os.path.join('./table_info/', self.db_name), exist_ok=True)
        # print("influxDB version: ", self.ifluxdb_version)

        database_list = self.influxDBClient.get_list_database()
        print('database_list: \n', database_list)  # return database names

        measurements_list = self.influxDBClient.get_list_measurements()
        print('measurements_list: \n', measurements_list)
        print('\n')

        if need_field:
            for measurement_dict in measurements_list:
                measurement_name = measurement_dict['name']
                query = 'show field keys from ' + measurement_name
                print("Querying data: " + query)

                result = self.influxDBClient.query(query)

                if save_to_file:
                    result_df = resultset_to_df(result)
                    result_df.to_csv(os.path.join('./table_info/', self.db_name, measurement_name + '_fieldKey.csv'))

                print("{} result: {}".format(measurement_name, result))
                print('\n')
        if need_tag:
            for measurement_dict in measurements_list:
                measurement_name = measurement_dict['name']
                query = 'show tag keys from {}'.format(measurement_name)
                print("Querying data: " + query)
                result = self.influxDBClient.query(query)

                if save_to_file:
                    result_df = resultset_to_df(result)
                    result_df.to_csv(os.path.join('./table_info/', self.db_name, measurement_name + '_tagKey.csv'))

                print("{} result: {}".format(measurement_name, result))
                print('\n')

    def get_first_and_last_local_timestamp(self, measurement_name: str,field_name: str) -> (str,str):

        query_str1='SELECT "{}" FROM {} ORDER BY ASC LIMIT 1'.format(field_name,measurement_name)
        query_str2 = 'SELECT "{}" FROM {} ORDER BY DESC LIMIT 1'.format(field_name,measurement_name)
        first_utc_time = self.dataframeclient.query(query_str1)[measurement_name].index[0]
        last_utc_time = self.dataframeclient.query(query_str2)[measurement_name].index[0]

        first_local_time=utc2local(first_utc_time)
        last_local_time=utc2local(last_utc_time)
        return str(first_local_time)[:19], str(last_local_time)[:19]

    def delete_measurement(self,measurement_name:str)->None:
        self.influxDBClient.drop_measurement(measurement_name)











