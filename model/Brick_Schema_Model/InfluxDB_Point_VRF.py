# -*- coding: utf-8 -*-
"""
@Project ：BrickSchema 
@File    ：InfluxDB_Point_VRF.py
@Time: 01/16/2023 1:18
@Author: Mingchen Li
"""
import json
VRF_Indoor_Nub = 7
VRF_Point_Dic = {
    "VRF_Outdoor_FanFrequency_Sensor_Value": json.dumps({
        'database_name': 'moserver',
        'measurement_name': 'modata',
        'field_list': ['fan1Frequency'],
        'tag_dict': {'nid': 'vrf/vrf_0000CC311178CCM26232341000271K0V/outdoor/129'},
        'code_name': ['Outdoor unit fan speed']
    }),

    "VRF_Outdoor_CondensingTemperature_Sensor_Value": json.dumps({
        'database_name': 'moserver',
        'measurement_name': 'modata',
        'field_list': ['highPressureSaturationTemp'],
        'tag_dict': {'nid': 'vrf/vrf_0000CC311178CCM26232341000271K0V/outdoor/129'},
        'code_name': ['Outdoor unit Condensing temperature']
    }),

    "VRF_Outdoor_EvaporatingTemperature_Sensor_Value": json.dumps({
        'database_name': 'moserver',
        'measurement_name': 'modata',
        'field_list': ['lowPressureSaturationTemp'],
        'tag_dict': {'nid': 'vrf/vrf_0000CC311178CCM26232341000271K0V/outdoor/129'},
        'code_name': ['Outdoor unit Evaporating temperature']
    }),

    "VRF_Outdoor_Electrical_Meter_Value": json.dumps({
        'database_name': 'moserveribms',
        'measurement_name': 'ibmsV2modata',
        'field_list': ['E'],
        'tag_dict': {'nid': 'ibmsv2/ibmsv2_5929149262402256896/EMeter/mDev_EMeter_Roof_MDV_10'},
        'code_name': ['Outdoor unit power']
    }),

    "VRF_Outdoor_OutdoorAirTemperature_Sensor_Value": json.dumps({
        'database_name': 'moserveribms',
        'measurement_name': 'bridgemodata',
        'field_list': ['e3'],
        'tag_dict': {'nid': 'ibms/ibms_1564376390869024768/microWeatherStation/20201800'},
        'code_name': ['Outdoor dry bulb temperature']
    }),

    "VRF_Outdoor_HighPressure_Sensor_Value": json.dumps({
        'database_name': 'moserver',
        'measurement_name': 'modata',
        'field_list': ['highPressure'],
        'tag_dict': {'nid': 'vrf/vrf_0000CC311178CCM26232341000271K0V/outdoor/129'},
        'code_name': ['Compressor discharge pressure']
    }),

    "VRF_Outdoor_LowPressure_Sensor_Value": json.dumps({
        'database_name': 'moserver',
        'measurement_name': 'modata',
        'field_list': ['lowPressure'],
        'tag_dict': {'nid': 'vrf/vrf_0000CC311178CCM26232341000271K0V/outdoor/129'},
        'code_name': ['Compressor suction pressure']
    }),

    "VRF_Outdoor_CompressorFrequency_Sensor_Value": json.dumps({
        'database_name': 'moserver',
        'measurement_name': 'modata',
        'field_list': ['compressor1Frequency', 'compressor2Frequency'],
        'tag_dict': {'nid': 'vrf/vrf_0000CC311178CCM26232341000271K0V/outdoor/129'},
        'code_name': ['Compressor frequency 1', 'Compressor frequency 2']
    }),
}

for indoor_nub in range(VRF_Indoor_Nub):
    VRF_Point_Dic["VRF_Indoor_IndoorAirTemperature_Sensor_{}_Value".format(indoor_nub)] = json.dumps({
        'database_name': 'moserver',
        'measurement_name': 'modata',
        'field_list': ['roomTemp'],
        'tag_dict': {'nid': 'vrf/vrf_0000CC311178CCM26232341000271K0V/indoor/{}'.format(indoor_nub)},
        'code_name': ['Indoor temperature {}'.format(indoor_nub)]
    })
    VRF_Point_Dic["VRF_Indoor_CoolingState_{}_Value".format(indoor_nub)] = json.dumps({
        'database_name': 'moserver',
        'measurement_name': 'modata',
        'field_list': ['exv1Opening'],
        'tag_dict': {'nid': 'vrf/vrf_0000CC311178CCM26232341000271K0V/indoor/{}'.format(indoor_nub)},
        'code_name': ['Indoor unit cooling state {}'.format(indoor_nub)]
    })
