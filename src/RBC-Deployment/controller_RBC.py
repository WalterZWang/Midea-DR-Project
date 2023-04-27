import numpy as np
import urllib
import uuid
import json


def rbc(param, logger, item_dir):
    # 获取索引值
    indoor_item = item_dir['indoor_item']

    # 省略算法逻辑
    logger.info("算法逻辑运行中")

    # 获取设备nid
    nid = param["deviceData"][indoor_item]['nid']

    # influxdb数据默认倒序，取第一个最新的值
    # 取设备运行模式列表
    # runModeList = param['deviceData'][0]['props']['runMode']
    # 取设备室内温度列表
    roomTempList = param["deviceData"][indoor_item]['props']['roomTemp'][0]
    # 取设备设定温度列表
    tempSettingList = param["deviceData"][indoor_item]['props']['tempSetting'][0]
    # 取设备启停列表
    onOffList = param["deviceData"][indoor_item]['props']['onOff'][0]

    runMode = 2

    #  rbc控制逻辑
    Tset = 25
    if roomTempList < Tset - 0.5:
        tempSetting = 30
        onOff = 0
    elif roomTempList > Tset + 0.5:
        tempSetting = 16
        onOff = 1
    else:
        tempSetting = tempSettingList
        onOff = int(onOffList)

    single_obj = {"nid": nid,
                  "control": {
                      "runMode": runMode,
                      "onOff": onOff,
                      "tempSetting": tempSetting
                  }
                  }

    url = 'http://caiyunapi.market.alicloudapi.com/forecast/24hour/113,23'
    appcode = 'f963fc47fe7540b8a1d923c484d63315'

    # Ambient temp forcast and linearize for 24 time-step
    request = urllib.request.Request(url)
    request.add_header('Authorization', 'APPCODE ' + appcode)
    request.add_header('X-Ca-Nonce', str(uuid.uuid4()))
    response = urllib.request.urlopen(request)
    Ta = np.zeros(1)
    content = json.loads(str(response.read(), 'utf-8'))
    for i in range(0, 6):
        T1 = content["result"]["hourly"]["temperature"][i]["value"]
        T4 = content["result"]["hourly"]["temperature"][i + 1]["value"]
        a = (T4 - T1) / 60
        T2 = T1 + 15 * a
        T3 = T2 + 15 * a
        for T in [T1, T2, T3, T4]:
            Ta = np.append(Ta, T)
    Ta_fore = np.delete(Ta, 0)
    logger.info("室外温度预测")
    logger.info(Ta_fore)

    # Solar radiation forcast and linearize for 24 time-step
    request = urllib.request.Request(url)
    request.add_header('Authorization', 'APPCODE ' + appcode)
    request.add_header('X-Ca-Nonce', str(uuid.uuid4()))
    response = urllib.request.urlopen(request)
    sol_rad = np.zeros(1)
    content = json.loads(str(response.read(), 'utf-8'))
    for i in range(0, 6):
        r1 = content["result"]["hourly"]["dswrf"][i]["value"]
        r4 = content["result"]["hourly"]["dswrf"][i + 1]["value"]
        a = (r4 - r1) / 60
        r2 = r1 + 15 * a
        r3 = r2 + 15 * a
        for r in [r1, r2, r3, r4]:
            sol_rad = np.append(sol_rad, r)
    sol_rad_fore = np.delete(sol_rad, 0)
    logger.info("太阳辐射预测")
    logger.info(sol_rad_fore)

    Weather_dir = {
        "OutdoorTemp": Ta_fore[0],
        "SolarRadiation": sol_rad_fore[0],
    }

    return {"actionArray": [single_obj]}, Weather_dir
