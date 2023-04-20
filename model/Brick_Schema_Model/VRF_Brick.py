# -*- coding: utf-8 -*-
"""
@Project ：Midea-DR-Project-main 
@File    ：VRF_Brick.py
@Time: 01/15/2023 1:53
@Author: Mingchen Li
"""
import json
import brickschema
from rdflib import RDF, RDFS, OWL, Namespace
from bricksrc.namespaces import TAG
from InfluxDB_Point_VRF import VRF_Point_Dic
from rdflib import Literal
from VRFmodel.Post_packaging_InfluxAPI import GetData_JsonList

# Some parameters
VRF_ID = "1K0V"
VRF_Indoor_Nub = 7
g = brickschema.Graph()
BLDG = Namespace('http://midea_HKUST.com/VRF_{}#'.format(VRF_ID))
g.bind("bldg", BLDG)

BRICK = Namespace("https://brickschema.org/schema/Brick#")
g.bind("brick", BRICK)

######################################## Add additional classes #######################################################
# VRF_Outdoor
g.add((BRICK.VRF_Outdoor, RDF.type, OWL.Class))
g.add((BRICK.VRF_Outdoor, RDFS.subClassOf, BRICK.HVAC_Equipment))
# VRF_Indoor
g.add((BRICK.VRF_Indoor, RDF.type, OWL.Class))
g.add((BRICK.VRF_Indoor, RDFS.subClassOf, BRICK.HVAC_Equipment))

######################################## Add tag to additional classes ################################################
Dic_VRF_tag = {
    "VRF_Outdoor": {"tags": [
        TAG.Equipment,
        TAG.VRF_Outdoor,
        TAG.Heat_Exchanger,
        TAG.Fan,
        TAG.Compressor,
        TAG.Check_Valve,
        TAG.Four_way_Valve,
        TAG.Cool,
        TAG.Heat,
        TAG.Hydrofluorocarbon,
        TAG.Supply,
        TAG.Return,
        TAG.Point,
        TAG.Pressure,
        TAG.Setpoint,
        TAG.Electronic_Expansion_Valve,
        TAG.sensor,
    ]},
    "VRF_Indoor": {"tags": [
        TAG.Equipment,
        TAG.VRF_Indoor,
        TAG.Heat_Exchanger,
        TAG.Fan,
        TAG.Cool,
        TAG.Heat,
        TAG.Hydrofluorocarbon,
        TAG.Electromagnetic_Valve,
        TAG.Volume,
        TAG.Box,
        TAG.Supply,
        TAG.Return,
        TAG.Setpoint,
        TAG.Point,
        TAG.sensor,
        TAG.Electronic_Expansion_Valve,
    ]}
}
for key, value in Dic_VRF_tag.items():
    tag_list = value["tags"]
    for tag in tag_list:
        g.add((BRICK[key], BRICK.hasAssociatedTag, tag))

########################################## Building Metamodel Frame ###################################################
'''
declare entities first
'''
# Outdoor Unit
Outdoor_Point_Type = {
    "VRF_Outdoor_FanFrequency_Sensor": BRICK.Frequency_Sensor,
    "VRF_Outdoor_CondensingTemperature_Sensor": BRICK.Air_Temperature_Sensor,
    "VRF_Outdoor_EvaporatingTemperature_Sensor": BRICK.Air_Temperature_Sensor,
    "VRF_Outdoor_Electrical_Meter": BRICK.Electrical_Meter,
    "VRF_Outdoor_OutdoorAirTemperature_Sensor": BRICK.Air_Temperature_Sensor,
    "VRF_Outdoor_HighPressure_Sensor": BRICK.Pressure_Sensor,
    "VRF_Outdoor_LowPressure_Sensor": BRICK.Pressure_Sensor,
    "VRF_Outdoor_CompressorFrequency_Sensor": BRICK.Frequency_Sensor,
}
g.add((BLDG["VRF_Outdoor_{}".format(VRF_ID)], RDF.type, BRICK.VRF_Outdoor))
for key, value in Outdoor_Point_Type.items():
    g.add((BLDG[key], RDF.type, value))

# Indoor Unit
Indoor_Point_Type = {
    "VRF_Indoor_IndoorAirTemperature_Sensor_": BRICK.Air_Temperature_Sensor,
    "VRF_Indoor_CoolingState_": BRICK.On_Off_Status
}
for indoor_nub in range(VRF_Indoor_Nub):
    g.add((BLDG["VRF_Indoor_{}_{}".format(VRF_ID, indoor_nub)], RDF.type, BRICK.VRF_Indoor))
    for key, value in Indoor_Point_Type.items():
        g.add((BLDG[key+str(indoor_nub)], RDF.type, value))

#  HVAC_Zone
g.add((BLDG["{}_HVACZone".format(VRF_ID)], RDF.type, BRICK.HVAC_Zone))

'''
declare edges
'''
for key in Outdoor_Point_Type.keys():
    g.add((BLDG["VRF_Outdoor_{}".format(VRF_ID)], BRICK.hasPoint, BLDG[key]))
    g.add((BLDG[key], BRICK.hasTag, TAG.MPC_VRF))

for indoor_nub in range(VRF_Indoor_Nub):
    g.add((BLDG["VRF_Outdoor_{}".format(VRF_ID)], BRICK.feeds, BLDG["VRF_Indoor_{}_{}".format(VRF_ID, indoor_nub)]))
    
    g.add((BLDG["VRF_Indoor_{}_{}".format(VRF_ID, indoor_nub)], BRICK.feeds, BLDG["{}_HVACZone".format(VRF_ID)]))

    for key in Indoor_Point_Type.keys():
        g.add((BLDG["VRF_Indoor_{}_{}".format(VRF_ID, indoor_nub)],
               BRICK.hasPoint,
               BLDG[key+str(indoor_nub)]))

############################################# add value and their tag #################################################
'''
declare tags
'''
# outdoor
for key in Outdoor_Point_Type.keys():
    g.add((BLDG[key], BRICK.hasTag, TAG.MPC_VRF))

# indoor
for indoor_nub in range(VRF_Indoor_Nub):
    for key in Indoor_Point_Type.keys():
        g.add((BLDG[key+str(indoor_nub)], BRICK.hasTag, TAG.MPC_VRF))

'''
add value
'''

# outdoor
for key in Outdoor_Point_Type.keys():
    g.add((BLDG[key+'_Value'], RDF.type, BRICK.TimeseriesReference))
    g.add((BLDG[key+'_Value'], BRICK.hasTimeseriesId, Literal(VRF_Point_Dic[key+'_Value'])))
    g.add((BLDG[key], BRICK.timeseries, BLDG[key+'_Value']))

# indoor
for indoor_nub in range(VRF_Indoor_Nub):
    for key in Indoor_Point_Type.keys():
        key = key + str(indoor_nub)
        g.add((BLDG[key + '_Value'], RDF.type, BRICK.TimeseriesReference))
        g.add((BLDG[key + '_Value'], BRICK.hasTimeseriesId, Literal(VRF_Point_Dic[key + '_Value'])))
        g.add((BLDG[key], BRICK.timeseries, BLDG[key + '_Value']))

############################################# Saving and Validating ###################################################
with open("{}_VRF_Model.ttl".format(VRF_ID), "w") as f:
    # the Turtle format strikes a balance between being compact and easy to read
    f.write(g.serialize(format="ttl"))


# validating using externally-defined shapes
external = brickschema.Graph()
external.load_file("{}_VRF_Model.ttl".format(VRF_ID))
valid, _, report = g.validate(shape_graphs=[external])
print(f"Graph is valid? {valid}")
if not valid:
  print(report)

#################################################### Query data #######################################################

# Query by timeseries and tag for getting VRF needed data
for point, params in g.query("""
    SELECT ?point ?params WHERE {
        ?point brick:timeseries/brick:hasTimeseriesId ?params .
        ?point brick:hasTag tag:MPC_VRF.
    }
"""):
    print(point, json.loads(params))

# Query by type
for i in g.query(
    """SELECT ?sensor WHERE {
    ?sensor rdf:type brick:Frequency_Sensor
}"""
):
    print(i)

# Query specific data
for point, params in g.query("""
    SELECT ?point ?params WHERE {
        ?point brick:timeseries/brick:hasTimeseriesId ?params .
        ?point brick:timeseries bldg:VRF_Outdoor_CompressorFrequency_Sensor_Value.
    }
"""):
    print(point, json.loads(params))
    temp_df = GetData_JsonList([params])


