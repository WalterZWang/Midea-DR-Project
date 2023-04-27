# -*- coding: utf-8 -*-
"""
@Project ：RBC 
@File    ：Data2DB.py
@Time: 04/17/2023 10:56 PM
@Author: Mingchen Li
"""
import pandas as pd

from Influxdb_API.Influxdb_API import ClientInfluxdb
from datetime import datetime


def get_key_by_value(dict_obj, value):
    new_dict = {v: k for k, v in dict_obj.items()}
    return new_dict.get(value)


def get_item(inputData):
    """
    获取各个参数索引值
    Parameters
    ----------
    inputData: 平台入参

    Returns
    -------
    各个参数索引值
    """
    global indoor_item, in_EMeter_item, out_EMeter_item
    for indoor_item, dic in enumerate(inputData["deviceData"]):
        if dic.get('devType') == 'indoor':
            break
    for in_EMeter_item, dic in enumerate(inputData["deviceData"]):
        if dic.get('devType') == 'EMeter' and dic.get('nid') == 'ibmsv2/ibmsv2_5929149262402256896/EMeter' \
                                                                '/mDev_EMeter_F2_Backup':
            break

    for out_EMeter_item, dic in enumerate(inputData["deviceData"]):
        if dic.get('devType') == 'EMeter' and dic.get('nid') == 'ibmsv2/ibmsv2_5929149262402256896/EMeter' \
                                                                '/mDev_EMeter_Roof_MDV_10':
            break
    item_dir = {
        'indoor_item': indoor_item,
        'in_EMeter_item':  in_EMeter_item,
        'out_EMeter_item':  out_EMeter_item,
    }
    return item_dir


def data_write_db(inputData, result, logger, item_dir, Weather_dir):
    """
    
    Parameters
    ----------
    inputData: 输入数据值
    result: RBC返回值
    logger: 平台抓取log
    indoor_item: 室内索引值
    in_EMeter_item: 室内扰动
    out_EMeter_item: 外籍电表
    -------

    """
    indoor_item = item_dir['indoor_item']
    in_EMeter_item = item_dir['in_EMeter_item']
    out_EMeter_item = item_dir['out_EMeter_item']

    # 记录当前时刻
    control_time = datetime.now()
    db_name = 'moserver'

    # 电表写入InfluxDB
    for EMeter_item in [in_EMeter_item, out_EMeter_item]:
        EMeterData = inputData["deviceData"][EMeter_item]
        EMeter_df_data = {
            'E': EMeterData['props']['E'],
            'time': EMeterData['props']['time'],
        }
        EMeter_df = pd.DataFrame(EMeter_df_data).set_index('time')
        params = {'measurement_name': 'RBC',
                  'data': EMeter_df,
                  'tag_list_in_data': None,
                  'add_in_tag_dict': {'nid': EMeterData["nid"]},
                  }
        db_client = ClientInfluxdb(db_name=db_name)  # connect the database
        db_client.write_influxdb(**params)
        # logger.info("电表数据写入成功")

    # 室内数据写入InfluxDB
    IndoorData = inputData["deviceData"][indoor_item]
    Indoor_df_data = {
        'roomTemp': IndoorData['props']['roomTemp'],
        'time': IndoorData['props']['time'],
    }
    Indoor_df = pd.DataFrame(Indoor_df_data).set_index('time')
    params1 = {'measurement_name': 'RBC',
               'data': Indoor_df,
               'tag_list_in_data': None,
               'add_in_tag_dict': {'nid': IndoorData["nid"]},
               }
    db_client = ClientInfluxdb(db_name=db_name)  # connect the database
    db_client.write_influxdb(**params1)
    logger.info("室内温度数据写入成功")

    # 控制命令写入InfluxDB
    for key, value in result["actionArray"][0]["control"].items():
        data = {key: [value], 'time': [control_time]}
        # 格式化时间戳为字符串格式
        data['time'] = [t.strftime('%Y-%m-%d %H:%M:%S') for t in data['time']]
        # 创建DataFrame并将时间戳键设置为索引
        data_df = pd.DataFrame(data).set_index('time')
        params = {'measurement_name': 'RBC',
                  'data': data_df,
                  'tag_list_in_data': None,
                  'add_in_tag_dict': {'nid': result["actionArray"][0]["nid"]},
                  }
        db_client.write_influxdb(**params)
    logger.info("控制命令写入InfluxDB成功")

    # 写入气象数据和室外温度
    for key, value in Weather_dir.items():
        data = {key: [value], 'time': [control_time]}
        # 格式化时间戳为字符串格式
        data['time'] = [t.strftime('%Y-%m-%d %H:%M:%S') for t in data['time']]
        # 创建DataFrame并将时间戳键设置为索引
        data_df = pd.DataFrame(data).set_index('time')
        params = {'measurement_name': 'RBC',
                  'data': data_df,
                  'tag_list_in_data': None,
                  'add_in_tag_dict': {'nid': "ibms/ibms_1564376390869024768/microWeatherStation/20201800"},
                  }
        db_client.write_influxdb(**params)
    logger.info("天气预测数据写入成功")

    logger.info('写入数据库成功')
