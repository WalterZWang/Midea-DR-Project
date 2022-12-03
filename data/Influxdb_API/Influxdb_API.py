import time
import os

from influxdb import InfluxDBClient,DataFrameClient
import pandas as pd
from datetime import datetime

from utils.influxdb_util import utc2local,local2utc,get_field_list,fore_data_preprocessing,resultset_to_df,\
    fore_data_preprocessing_read

# import configparser

# config = configparser.ConfigParser()
#
#
# config.read('/home/wanfu/Documents/Midea-DR-Project/data/config.ini')
#
# influxHost = config['INFLUXDB']['Host']
# influxPort = int(config['INFLUXDB']['Port'])
# influxUser = config['INFLUXDB']['Username']
# influxPassword = config['INFLUXDB']['Password']
# influxDatabase_vrf = config['INFLUXDB']['Database_vrf']
# influxDatabase_meter = config['INFLUXDB']['Database_meter']
# measurement_Fore=config['INFLUXDB']['Measurement_Fore']
#
# weatherAppcode=config['WEATHER']['Appcode']
# weatherUrl=config['WEATHER']['Url']

influxHost = 'vm.buildibp.top'
influxPort = 21622
influxUser = 'btri'
influxPassword = 'mBXRGzfeWee3iZzq'
influxDatabase_vrf = 'moserver'
influxDatabase_meter = 'moserveribms'
measurement_Fore = 'forecast6'





class ClientInfluxdb(object):

    def __init__(self, db_name):

        self.db_name = db_name
        self.influxDBClient = InfluxDBClient(influxHost, influxPort, influxUser, influxPassword, self.db_name)
        self.dataframeclient = DataFrameClient(influxHost, influxPort, influxUser, influxPassword, self.db_name)
        # self.influxDBClient = InfluxDBClient('localhost', 8086, 'root', 'root', db_name)
        # self.dataframeclient=DataFrameClient('localhost', 8086, 'root', 'root', db_name)
        # self.client = InfluxDBClient(influxHost, influxPort, influxUser, influxPassword, self.db_name)
        # selfmeasurement = measurement

        # self.ifluxdb_version = self.client_DataFrame.ping()  # influxDB version

    def read_influxdb(self, measurement_name:str, start_time:datetime, end_time:datetime, field_list:list,
                      tag_dict: dict=None,fore=False,fore_horizon: int=None,interval: str=None)->pd.DataFrame:
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
                new_field_list.extend([col+"_"+str(i) for i in range(1,fore_horizon+1)])
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

        result_df=data[measurement_name]
        result_df.index=result_df.index.map(lambda x: utc2local(x))

        if fore:
            result_df=fore_data_preprocessing_read(result_df,field_list_raw,fore_horizon,interval)

        return  result_df

    def write_influxdb(self, measurement_name:str,data:pd.DataFrame,
                       tag_list_in_data: list=None, add_in_tag_dict: dict=None,
                       fore: bool=False,interval: str=None)->None:
        data_df=data.copy(deep=True)
        assert isinstance(measurement_name, str),f"measurement expected a string data type, got {type(measurement_name)}"
        assert isinstance(data_df, pd.DataFrame), f"data_df expected a string data type, got {type(data_df)}"
        assert tag_list_in_data is None or isinstance(tag_list_in_data, list), \
            f"tag_list expected None value or list data type, got {type(tag_list_in_data)}"
        assert isinstance(fore,bool),f"fore expected a boolean data type, got {type(fore)} "
        # print(data_df.index)
        if tag_list_in_data is None:
            tag_list_in_data=[]
        # print(tag_list_in_data)
        if fore:
            assert interval is not None,f"interval expected not None value"
            data_df=fore_data_preprocessing(data_df,tag_list_in_data,interval)
            tag_list_in_data.append('interval')
        cols = data_df.columns.to_list()
        field_list = get_field_list(cols,tag_list_in_data)
        data_df.index = pd.to_datetime(data_df.index.values).map(lambda x: local2utc(x))
        # data_df = data_df.set_index(time_stamp)


        if tag_list_in_data:
            for t in tag_list_in_data:
                data_df[t]=data_df[t].astype(str)
        # print(tag_list_in_data)
        if add_in_tag_dict:
            for k,v in add_in_tag_dict.items():
                data_df[k]=v
                tag_list_in_data.append(k)

        self.dataframeclient.write_points(data_df,measurement_name,tag_columns=tag_list_in_data,field_columns=field_list)

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









if __name__ == '__main__':
    # influxDatabase_vrf = config['INFLUXDB']['Database_vrf']
    # influxDatabase_meter = config['INFLUXDB']['Database_meter']
    # db_forecast=ClientIfluxdb(db_name=influxDatabase_meter)
    # db_forecast=ClientIfluxdb(db_name=influxDatabase_meter)
    # influxDatabase_vrf = 'moserver'
    # influxDatabase_meter = 'moserveribms'

    # weather = Weather()

    # df = pd.read_excel('2022-11-26_22.xlsx')
    # city_name = ['hk' for i in range(48)]
    # latitude=['23' if i%2==0 else '24' for i in range(48)]
    # # print(latitude)
    # df = df[['datetime', 'temperature','humidity']]
    # df['city'] = city_name
    # df['latitude']=latitude
    # df.set_index('datetime',inplace=True)
    # #
    # # db_forecast2 = ClientIfluxdb(db_name='example')
    # # measurement_name = 'forecast2'
    # # db_forecast2.delete_measurement(measurement_name)
    # #
    # # db_forecast2.write_influxdb(measurement_name, df, tag_list=['city', 'latitude'], fore=True)
    #
    # # if weather.update():
    #     # weather.pack_data()
    # # def write_influxdb(self, measurementmeasurement, data_df, tag_list=None, fore=False):
    # # db_forecast.write_influxdb(measurement_name,df,tag_list=['city','latitude'],fore=True)
    # # first_timestamp,last_timestamp=db_forecast.get_first_and_last_local_timestamp('forecast6','humidity')
    # # print(first_timestamp,last_timestamp)
    # # data=db_forecast.read_influxdb(measurement_name,pd.to_datetime('2022-11-26 22:00:00'),pd.to_datetime('2022-11-26 22:00:00'),
    # #                           ['humidity','temperature'],{'city':'hk','latitude':'23'},fore=True,fore_horizon=12)
    #
    #
    # # db_forecast.get_table_info(need_field=False, need_tag=True, save_to_file=False)
    # db_client = ClientInfluxdb(db_name='test')
    # measurement_name = 'forecast7'
    # db_client.delete_measurement(measurement_name)
    #
    # # db_forecast2.write_influxdb(measurement_name, df, tag_list=['city', 'latitude'], fore=True)
    # # first_timestamp,last_timestamp=db_forecast.get_first_and_last_local_timestamp('forecast6','humidity')
    # # print(first_timestamp,last_timestamp)
    # # result_df=db_forecast.read_influxdb(measurement_name,pd.to_datetime('2022-11-26 22:00:00'),pd.to_datetime('2022-11-26 22:00:00'),['humidity'],{'city':'hk','latitude':'23'},fore=True,fore_horizon=10)
    # # %%write_influxdb(self, measurement_name:str,data:pd.DataFrame,
    # #                        tag_list_in_data: list=None, add_in_tag_dict: dict=None,
    # #                        fore: bool=False,interval: str='60m')->None:
    # db_client.write_influxdb(measurement_name, data=df,
    #                          tag_list_in_data=['city', 'latitude'],
    #                          add_in_tag_dict={'nid': 'vrf/vrf_0000CC311178CCM26232341000271K0V/indoor/0'},
    #                          fore=True,interval='60m')
    # # re_df=db_forecast2.read_influxdb(measurement_name, pd.to_datetime('2022-11-26 14:00:00'),
    # #                            pd.to_datetime('2022-11-26 14:00:00'), ['humidity'], {'city': 'hk', 'latitude': '23'},
    # #                            fore=True, fore_horizon=10)
    # # print(re_df)
    import pandas as pd
    import numpy as np
    # from Influxdb_API import ClientInfluxdb
    # from Influxdb_API_local import ClientInfluxdb

    # %%
    ### import the demo data
    data_df = pd.read_csv('./indoor_state_forecast.csv', index_col=0)
    # data_df
    # %%
    db_name = 'test'

    params = {'measurement_name': 'open_loop_control3',
              'data': data_df,
              'tag_list_in_data': None,
              'add_in_tag_dict': {'nid': 'vrf/vrf_0000CC311178CCM26232341000271K0V/indoor/0'},
              'fore': True,
              'interval': '60m'
              }
    # %%

    # %%
    db_client = ClientInfluxdb(db_name=db_name)  # connect the database
    # %%
    db_client.write_influxdb(**params)


